import json
import os
import re
import shutil
import traceback
from collections import Counter

from tenacity import RetryError
from tqdm import tqdm
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.utils import change_directory


def extract_traceback(error_str):
    """
    从错误信息字符串中提取 'Traceback (most recent call last):' 及其之后的报错信息。
    """
    pattern = r"Traceback \(most recent call last\):.*"
    match = re.search(pattern, error_str, re.DOTALL)
    if match:
        return match.group(0).split('\n')[-2]
    else:
        return None


def clean_json_string(json_str):
    # Locate the injected_code value
    start_index = json_str.find('"error_code": "') + len('"error_code": "')
    end_index = json_str.find('",', start_index)

    # Extract the code part and replace newlines and quotes
    code_part = json_str[start_index:end_index]
    cleaned_code_part = code_part.replace('\n', '\\n').replace('"', '\"')

    # Replace the original code part in the json_str with the cleaned code part
    cleaned_json_str = json_str[:start_index] + cleaned_code_part + json_str[end_index:]

    return cleaned_json_str


def get_code(response):
    all_python_code_blocks_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```', re.MULTILINE)
    all_code_blocks = all_python_code_blocks_pattern.findall(response)
    all_code_blocks_combined = '\n'.join(all_code_blocks)
    return all_code_blocks_combined


def _format_verification_result(result, code):
    """格式化验证结果为标准格式"""
    try:
        # 尝试从结果中提取 JSON 部分
        start_index = result.find('{')
        end_index = result.rfind('}')
        if start_index == -1 or end_index == -1:
            raise ValueError("No valid JSON found in the result")

        json_str = result[start_index:end_index + 1]
        result_dict = json.loads(json_str)

        # 构建标准格式的结果
        formatted_result = {
            "result": {
                "has_errors": result_dict.get("is_error", "false").lower() == "true",
                "errors": []
            }
        }

        # 处理每个错误说明
        for error in result_dict.get("error_explanation", []):
            error_detail = {
                "error_type": error.get("error_type", "Unknown"),
                "error_message": error.get("explanation", ''),
                "expected_outcome": error.get("expected_outcome", ''),
                "suggestions": error.get("suggestions", '')
            }
            formatted_result['result']['errors'].append(error_detail)

        # 如果没有错误信息但标记为有错误，添加默认信息
        if formatted_result['result']['has_errors'] and not formatted_result['result']['errors']:
            formatted_result['result']['errors'].append({
                "error_type": "Unknown",
                "error_message": "Unspecified error detected",
                "expected_outcome": '',
                "suggestions": "Please review and correct the code"
            })

        return formatted_result

    except Exception as e:
        # 如果解析失败，返回错误格式的结果
        return {
            'result': {
                'has_errors': True,
                'error_type': 'ParseError',
                'error_message': f'Failed to parse verification result: {str(e)}',
                'suggestions': 'Please check the code and verification output format',
                'original_result': result
            }
        }


class ErrorVerifierAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.query = kwargs.get('query', '')
        self.data_information = kwargs.get('data_information', None)

    def _get_self_consistent_answer(self, list_of_parsed_json):
        """
        Performs a majority vote to find the most consistent answer.
        Votes are cast based on the (cause_line, effect_line) tuple.
        """
        if not list_of_parsed_json:
            return None

        votes = []
        for output in list_of_parsed_json:
            # 确保每个输出都是有效的字典
            if isinstance(output, dict) and 'cause_line' in output and 'effect_line' in output:
                # 标准化处理，避免因空格等问题导致投票分散
                cause = str(output['cause_line']).strip()
                effect = str(output['effect_line']).strip()
                votes.append((cause, effect))

        if not votes:
            return None

        vote_counts = Counter(votes)
        most_common_answer_tuple, _ = vote_counts.most_common(1)[0]

        # 找到与最常见答案匹配的第一个完整JSON对象
        for output in list_of_parsed_json:
            if isinstance(output, dict) and 'cause_line' in output and 'effect_line' in output:
                if (str(output['cause_line']).strip() == most_common_answer_tuple[0] and
                        str(output['effect_line']).strip() == most_common_answer_tuple[1]):
                    return output  # 返回完整的JSON对象

        return None  # 理论上不应该到这里，但作为保障

    def generate(self, user_prompt, model_type, code, backend='OpenRouter', temperature=0.0):
        workspace_structure = print_filesys_struture(self.workspace)

        information = {
            'workspace_structure': workspace_structure,
            'code': code,
            'query': user_prompt,
        }

        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)})

        self.chat_history = self.chat_history + messages
        return completion_with_backoff(messages, model_type, backend, temperature)

    def generate_for_self_refine(self, user_prompt, model_type, code, initial_analysis=None, backend='OpenRouter'):
        workspace_structure = print_filesys_struture(self.workspace)

        # ------------------ 1. 准备通用的信息 ------------------
        # 这些信息在两个阶段都是共享的
        base_information = {
            # 'workspace_structure': workspace_structure,
            'code': code,
            'query': user_prompt,
        }

        # ------------------ 2. 准备 System Prompt ------------------
        # 两个阶段使用同一个 System Prompt
        system_prompt = fill_in_placeholders(self.prompts['system'], base_information)

        messages = []
        messages.append({"role": "system", "content": system_prompt})

        # ------------------ 3. 根据阶段选择并准备 User Prompt ------------------
        if initial_analysis:
            # --- 第二阶段：Refinement Mode ---
            # 除了基本信息，还需要第一阶段的诊断结果
            refinement_information = {
                **base_information,  # 合并字典，继承所有基本信息
                'initial_cot_output': initial_analysis['cot_output'],
                'initial_json_output': json.dumps(initial_analysis['json_output'], indent=4)
            }

            user_prompt_content = fill_in_placeholders(self.prompts['user_stage_2'], refinement_information)

        else:
            # --- 第一阶段：Initial Analysis Mode ---
            # 只需要基本信息
            user_prompt_content = fill_in_placeholders(self.prompts['user_stage_1'], base_information)

        messages.append({"role": "user", "content": user_prompt_content})

        # ------------------ 4. 调用API并返回结果 ------------------
        # 这里的 chat_history 逻辑可以根据你的需求调整
        # 如果每个阶段是独立的，就不需要累加
        # self.chat_history = self.chat_history + messages

        return completion_with_backoff(messages, model_type, backend)

    def run(self, queries, model_type, code):
        log = []
        verifier_results = []
        query = queries

        concepts = query['concepts']
        error_code_directory = os.path.join(self.workspace, 'error_code_dir/')
        jsonl_file_path = os.path.join(error_code_directory, 'logical_error_data.jsonl')
        error_code_content = []

        # Read from the jsonl file
        with open(jsonl_file_path, 'r') as jsonl_file:
            file_content = jsonl_file.read()

        # Split the content by assuming each JSON object ends with '}\n'
        json_objects = file_content.strip().split('\n}\n')

        for obj_str in json_objects:
            # Ensure each object has proper JSON format by adding the closing brace back
            # obj_str = obj_str + '}'
            result_dict = json.loads(obj_str)

            # Loop through each concept in the JSON object and extract error codes
            for concept, entries in result_dict.items():
                for entry in entries:
                    error_code_each = entry.get('error_code', '')
                    error_code_content.append(error_code_each)

        '''for concept in concepts:
            for i in range(3):
                error_code_list.append(os.path.join(error_code_directory, f"logical_error_{concept}_{i}_injected.py"))

        for idx, error_code_dir in enumerate(error_code_list):
            with open(error_code_dir, 'r') as file:
                error_code_each = file.read()
                error_code_content.append(error_code_each)'''

        for error_code_each in tqdm(error_code_content):
            information = {
                'code': error_code_each,
            }

            messages = []
            messages.append({"role": "system", "content": ''})
            messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['error'], information)})

            error_erase_result = completion_with_backoff(messages, model_type)
            error_erase_code = get_code(error_erase_result)

            # 记录日志
            log.append(f"\n------------------------------------- Processing Query -------------------------------------")
            log.append(f"Question ID: {query['id']}")
            log.append(f"Question: {query['question']}")
            log.append(f"Constraints: {query['constraints']}")
            log.append(f"Data File: {query['file_name']}")
            log.append(f"Expected Format: {query['format']}")
            log.append(f"Ground Truth: {query['answers']}")
            log.append(f"\n\nError Erased Code:\n\n {error_erase_code}\n")

            prompt = f"""Question ID: {query['id']}
    Question: {query['question']}

    Constraints: {query['constraints']}

    Data File Name: {query['file_name']}

    Format: {query['format']}

    Correct answer: {query['answers']}
                    """

            log.append("\n...............Verifying code...............")
            result = self.generate(prompt, model_type=model_type, code=error_erase_code)

            # 解析验证结果并格式化
            verification_result = _format_verification_result(result, error_erase_code)
            verifier_results.append(verification_result)

            # 记录验证结果
            log.append(f"\nVerifier Result:\n{json.dumps(verification_result, indent=2)}\n")

        # 将结果写入文件
        with open(os.path.join(error_code_directory, 'logical_error_verification.jsonl'), 'w') as jsonl_file:
            for result in verifier_results:
                jsonl_file.write(json.dumps(result) + '\n')

        log_string = "\n".join(log)
        return log_string, verifier_results

    def run_with_other_agent(self, queries, model_type, from_prev_agent, individual_workspace):
        log = []
        # verifier_results = []
        query = queries

        concepts = query['concepts']
        error_code_directory = os.path.join(self.workspace, 'error_code_dir/')
        jsonl_file_path = os.path.join(error_code_directory, 'logical_error_data.jsonl')
        error_code_content = []

        if isinstance(from_prev_agent, dict):
            error_erase_code = from_prev_agent['result']
        elif isinstance(from_prev_agent, tuple):
            error_erase_code = from_prev_agent[1]
        else:
            raise TypeError("Unsupported information type between agents")

        '''information = {
            'code': error_code_each,
        }

        messages = []
        messages.append({"role": "system", "content": ''})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['error'], information)})

        error_erase_result = completion_with_backoff(messages, model_type)
        error_erase_code = get_code(error_erase_result)'''

        # 记录日志
        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        log.append(f"Ground Truth: {query['answers']}")
        log.append(f"\n\nError Erased Code:\n\n {error_erase_code}\n")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}

    Constraints: {query['constraints']}

    Data File Name: {query['file_name']}

    Format: {query['format']}

    Correct answer: {query['answers']}
                    """

        log.append("\n...............Verifying code...............")
        result = self.generate(prompt, model_type=model_type, code=error_erase_code)

        # 解析验证结果并格式化
        verification_result = _format_verification_result(result, error_erase_code)
        # verifier_results.append(verification_result)

        # 记录验证结果
        log.append(f"\nVerifier Result:\n{json.dumps(verification_result, indent=2)}\n")

        # 将结果写入文件
        # with open(os.path.join(error_code_directory, 'logical_error_verification.jsonl'), 'w') as jsonl_file:
        #     for result in verifier_results:
        #         jsonl_file.write(json.dumps(result) + '\n')

        log_string = "\n".join(log)
        return log_string, verification_result

    def eval(self, queries, model_type, eval_folder):
        log = []
        query = queries

        error_hidden_code = query['error_hidden_code']
        ground_truth_dict = {
            "error_type": query['error_type'],
            "explanation": query['explanation'],
            "expected_outcome": query['expected_outcome']
        }

        # 记录日志
        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        log.append(f"Ground Truth: {query['answers']}")
        log.append(f"\n\nError Hidden Code:\n\n {error_hidden_code}\n")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}

    Constraints: {query['constraints']}

    Data File Name: {query['file_name']}

    Format: {query['format']}

    Correct answer: {query['answers']}
                    """

        log.append("\n...............Verifying code...............")
        print(f"\n...............Verifying query {query['id']}...............")
        result = self.generate(prompt, model_type=model_type, code=error_hidden_code)

        # Locate the first curly brace to the last one for extracting the JSON object
        start_index = result.find('{')
        end_index = result.rfind('}')

        if start_index == -1 or end_index == -1:
            raise ValueError("No valid JSON found in the input string.")

        # Extract the JSON substring and clean it if necessary
        json_str = result[start_index:end_index + 1]
        cleaned_json_str = clean_json_string(json_str)

        # Convert the extracted JSON string to a Python dictionary
        result_dict = json.loads(cleaned_json_str)

        information = {
            'ground_truth': ground_truth_dict,
            'eval_dict': result_dict
        }

        messages = []
        messages.append({"role": "system", "content": ''})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['eval'], information)})

        print(f"\n...............Evaluating query {query['id']}...............")
        eval_result = completion_with_backoff(messages, 'gpt-4o')

        eval_result_dict = {
            'id': query['id'],
            'eval_result': eval_result
        }

        result_dict['eval_result'] = eval_result

        # 记录验证结果
        log.append(f"\nVerifier Result:\n{json.dumps(result_dict, indent=2)}\n")

        # 将结果写入文件
        with open(os.path.join(eval_folder, f'{model_type.replace("Qwen/","")}_method_eval_result.jsonl'), 'a') as jsonl_file:
            jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, result_dict

    def rubber_duck_eval(self, queries, model_type, eval_folder, individual_workspace):
        log = []
        query = queries

        error_versions = query['error_versions']
        if not error_versions:
            raise ValueError("No error versions found in the query.")

        # 记录日志
        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        # log.append(f"Constraints: {query['constraints']}")
        # log.append(f"Data File: {query['file_name']}")
        # log.append(f"Expected Format: {query['format']}")
         #log.append(f"Ground Truth: {query['answers']}")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}
                    """

        MAX_RETRIES = 5
        eval_results = []
        print(f"\n**********Verifying ID: {query['id']}**********")
        try:
            for idx, error_version in enumerate(error_versions):
                retries = 0  # 重试计数器
                success = False  # 标记是否成功处理

                while retries < MAX_RETRIES and not success:
                    try:
                        log.append(
                            f"\n--- Processing Error Version {idx + 1}/{len(error_versions)} (Attempt {retries + 1}) ---")

                        modified_code = error_version['modified_code']
                        error_message = extract_traceback(error_version['execution_output'])
                        if error_message is not None:
                            ground_truth = {
                                "cause_error_line": error_version["cause_error_line"],
                                "effect_error_line": error_version["effect_error_line"],
                                "execution_output": error_message
                            }
                            # Log error version details
                            log.append(f"\nModified Code:\n{modified_code}")
                            log.append(f"Ground Truth: {json.dumps(ground_truth, indent=2)}")

                            log.append("\n...............Verifying code with LLM...............")
                            print(
                                f"\n...............Verifying error version {idx + 1}/{len(error_versions)} (Attempt {retries + 1})...............")

                            result = self.generate(prompt, model_type=model_type, code=modified_code, backend='OpenRouter')

                            # Locate the first curly brace to the last one for extracting the JSON object
                            start_index = result.rfind('{')
                            end_index = result.rfind('}')

                            if start_index == -1 or end_index == -1:
                                raise ValueError("No valid JSON found in the LLM response.")

                            # Extract and parse JSON
                            json_str = result[start_index:end_index + 1]
                            # cleaned_json_str = clean_json_string(json_str)
                            llm_output = json.loads(json_str)

                            information = {
                                'ground_truth': ground_truth,
                                'eval_dict': llm_output
                            }

                            messages = []
                            messages.append({"role": "system", "content": ''})
                            messages.append(
                                {"role": "user", "content": fill_in_placeholders(self.prompts['eval'], information)})

                            print(
                                f"\n...............Evaluating error version {idx + 1}/{len(error_versions)} (Attempt {retries + 1})...............")
                            eval_completion = completion_with_backoff(messages, 'gpt-4o', backend='OpenRouter')

                            start_index = eval_completion.rfind('{')
                            end_index = eval_completion.rfind('}')
                            json_str = eval_completion[start_index:end_index + 1]
                            eval_result = json.loads(json_str)
                            eval_results.append(eval_result)

                            # Log comparison result
                            log.append(f"LLM Output: {json.dumps(result, indent=2)}")
                            print(f"LLM Output: {json.dumps(result, indent=2)}")
                            log.append(f"JSON Output: {json.dumps(llm_output, indent=2)}")
                            log.append(f"Eval Result: {eval_result}")

                            # 如果成功处理，设置 success 为 True
                            success = True

                        else:
                            break  # 如果没有错误信息，跳过该 error_version

                    except (ValueError, json.JSONDecodeError, KeyError, TypeError, RetryError) as e:
                        retries += 1
                        log.append(f"Error encountered in Attempt {retries}: {str(e)}")
                        print(f"Error in Attempt {retries}: {str(e)}")
                        # traceback.print_exc()

                # 如果重试次数用尽仍未成功
                if not success:
                    log.append(f"Failed to process Error Version {idx + 1} after {MAX_RETRIES} attempts.")
                    print(f"Failed to process Error Version {idx + 1} after {MAX_RETRIES} attempts.")


        except (ValueError, json.JSONDecodeError, KeyError) as e:
            print(f"Exception occurred: {str(e)}")

        finally:
            # Save all results to a file
            with open(os.path.join(eval_folder, f'eval_{model_type.replace("qwen/", "").replace(":", "_")}_rubber_duck_1_shot_CoT_on_bench_v3.jsonl'), 'a') as jsonl_file:
                eval_result_dict = {
                    'id': query['id'],
                    'eval_result': eval_results
                }
                jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, eval_results

    def multi_rubber_duck_eval(self, queries, model_type, eval_folder, individual_workspace):
        log = []
        query = queries

        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")

        prompt = f"""Question ID: {query['id']}
            Question: {query['question']}
                            """

        MAX_RETRIES = 5
        eval_results = []  # Will store list of lists of single-error eval results
        print(f"\n**********Verifying ID: {query['id']}**********")
        try:
            retries = 0
            success = False
            error_message = []
            while retries < MAX_RETRIES and not success:
                try:
                    log.append(
                        f"\n--- Processing Error {query['id']} (Attempt {retries + 1}) ---")

                    modified_code = query['modified_code']
                    for exec_o in query['execution_outputs']:
                        error_message.append(extract_traceback(exec_o))
                    if error_message is not None:
                        ground_truth_info = []
                        for cause_e_l, effect_e_l, error_m in zip(query["cause_error_lines"], query["effect_error_lines"], error_message):
                            ground_truth_info.append({  # Store ground truth lists
                                "cause_error_line": cause_e_l,
                                "effect_error_line": effect_e_l,
                                "error_message": error_m
                            })

                        log.append(f"\nModified Code:\n{modified_code}")
                        log.append(f"Ground Truth Lists: {json.dumps(ground_truth_info, indent=2)}")

                        log.append("\n...............Verifying code with LLM...............")
                        print(
                            f"\n...............Verifying error {query['id']} (Attempt {retries + 1})...............")

                        result = self.generate(prompt, model_type=model_type, code=modified_code, backend='THU')

                        # start_index = result.rfind('[')  # Expecting JSON list now for multi-bug detection
                        # end_index = result.rfind(']')

                        match = re.search(r"\[\s*\{.*?\}\s*\]", result, re.DOTALL)

                        if match:
                            json_list_str = match.group(0)
                        else:
                            json_list_str = None

                        # if start_index == -1 or end_index == -1:
                            # raise ValueError("No valid JSON List found in the LLM response (Error Detection).")

                        llm_output_errors = json.loads(json_list_str)

                        # json_list_str = result[start_index:end_index + 1]
                        # cleaned_json_list_str = clean_json_string(json_list_str)
                        # llm_output_errors = json.loads(json_list_str)  # Now LLM output is expected to be a list of errors

                        log.append(f"LLM Output (Error Detection): {json.dumps(llm_output_errors, indent=2)}")

                        single_error_eval_results = []  # List to store eval results for each detected error
                        for llm_error_index, llm_error in enumerate(
                                llm_output_errors):  # Loop through each detected error
                            information_single_error = {
                                'ground_truth': ground_truth_info,
                                'llm_output_error': llm_error  # Pass the single LLM detected error
                            }

                            messages = []
                            messages.append({"role": "system", "content": ''})
                            messages.append(
                                {"role": "user", "content": fill_in_placeholders(self.prompts['eval'],
                                                                                 information_single_error)})  # Use single-error eval prompt

                            print(
                                f"\n...............Evaluating detected error {llm_error_index + 1}/{len(llm_output_errors)} of error version {query['id']} (Attempt {retries + 1})...............")
                            eval_result_str = completion_with_backoff(messages,
                                                                      'gpt-4o', backend='THU')  # Get single-error eval result

                            start_index = eval_result_str.rfind('{')
                            end_index = eval_result_str.rfind('}')
                            json_str = eval_result_str[start_index:end_index + 1]
                            single_error_eval_result = json.loads(json_str)  # Parse single-error eval JSON
                            single_error_eval_results.append(single_error_eval_result)  # Append single-error result

                            log.append(
                                f"  Error {llm_error_index + 1} Eval Result: {json.dumps(single_error_eval_result, indent=2)}")

                        eval_results.append(
                            single_error_eval_results)  # Append list of single-error results for this error_version
                        success = True

                    else:
                        break

                except (ValueError, json.JSONDecodeError, KeyError) as e:
                    retries += 1
                    log.append(f"Error encountered in Attempt {retries}: {str(e)}")
                    print(f"Error in Attempt {retries}: {str(e)}")

            if not success:
                log.append(f"Failed to process Error Version {query['id']} after {MAX_RETRIES} attempts.")
                print(f"Failed to process Error Version {query['id']} after {MAX_RETRIES} attempts.")


        except (ValueError, json.JSONDecodeError, KeyError) as e:
            print(f"Exception occurred: {str(e)}")

        finally:
            with open(
                    os.path.join(eval_folder, f'eval_{model_type.replace("Qwen/", "").replace(":", "_")}_multi_rubber_duck_CoT_on_multi_bench_v2.jsonl'),
                    'a') as jsonl_file:
                eval_result_dict = {
                    'id': query['id'],
                    'eval_result': eval_results  # Now contains list of lists of single-error evaluations
                }
                jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, eval_results

    def rubber_duck_eval_self_refine(self, queries, model_type, eval_folder, individual_workspace):
        """
        Modified version of rubber_duck_eval to implement a two-stage self-refine process.
        """
        log = []
        query = queries

        error_versions = query.get('error_versions')
        if not error_versions:
            raise ValueError("No error versions found in the query.")

        # 记录日志
        log.append(
            f"\n------------------------------------- Processing Query (Self-Refine) -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")

        base_prompt = f"""Question ID: {query['id']}
    Question: {query['question']}"""

        MAX_RETRIES = 5
        eval_results = []
        print(f"\n**********Verifying ID: {query['id']} (Self-Refine)**********")
        try:
            for idx, error_version in enumerate(error_versions):
                retries = 0
                success = False

                while retries < MAX_RETRIES and not success:
                    try:
                        log.append(
                            f"\n--- Processing Error Version {idx + 1}/{len(error_versions)} (Attempt {retries + 1}) ---")

                        modified_code = error_version['modified_code']
                        error_message = extract_traceback(error_version.get('execution_output', ''))

                        if error_message is None:
                            log.append("Skipping error version due to missing execution output.")
                            break

                        ground_truth = {
                            "cause_error_line": error_version["cause_error_line"],
                            "effect_error_line": error_version["effect_error_line"],
                            "execution_output": error_message
                        }

                        log.append(f"\nModified Code:\n{modified_code}")
                        log.append(f"Ground Truth: {json.dumps(ground_truth, indent=2)}")

                        # ------------------ STAGE 1: Initial Diagnosis ------------------
                        log.append("\n............... STAGE 1: Performing Initial Diagnosis ...............")
                        print(
                            f"\n............... STAGE 1: Verifying error version {idx + 1}/{len(error_versions)} ...............")

                        # 调用LLM进行初步诊断
                        initial_result_raw = self.generate_for_self_refine(base_prompt, model_type=model_type, code=modified_code,
                                                           backend='OpenRouter')

                        # 提取初步诊断的CoT和JSON
                        # 注意：这里需要一个更健壮的解析器，但为了简单起见，我们先用字符串分割
                        if "**JSON Output:**" not in initial_result_raw:
                            raise ValueError("Initial diagnosis response is malformed: missing 'JSON Output'.")

                        parts = initial_result_raw.split("**JSON Output:**")
                        initial_cot_output = parts[0].replace("**CoT Output:**", "").strip()
                        json_part_raw = parts[1]

                        start_index = json_part_raw.find('{')
                        end_index = json_part_raw.rfind('}')
                        if start_index == -1 or end_index == -1:
                            raise ValueError("No valid JSON found in the initial LLM response.")

                        initial_json_str = json_part_raw[start_index:end_index + 1]
                        initial_llm_output = json.loads(initial_json_str)

                        log.append(f"\n[STAGE 1] Initial CoT Output:\n{initial_cot_output}")
                        log.append(f"[STAGE 1] Initial JSON Output: {json.dumps(initial_llm_output, indent=2)}")

                        # ------------------ STAGE 2: Refinement ------------------
                        log.append("\n............... STAGE 2: Performing Refinement ...............")
                        print(
                            f"\n............... STAGE 2: Refining diagnosis for error version {idx + 1}/{len(error_versions)} ...............")

                        # 构建第二阶段的输入
                        initial_analysis = {
                            "cot_output": initial_cot_output,
                            "json_output": initial_llm_output
                        }

                        print(f"\nInitial analysis: \n{initial_analysis}")

                        # 再次调用LLM进行修正
                        final_result_raw = self.generate_for_self_refine(
                            base_prompt,
                            model_type=model_type,
                            code=modified_code,
                            initial_analysis=initial_analysis,  # 传入第一阶段的结果
                            backend='OpenRouter'
                        )

                        # 提取最终的诊断结果
                        if "**Final JSON Output:**" not in final_result_raw:
                            raise ValueError("Refined response is malformed: missing 'Final JSON Output'.")

                        print(f"\nFinal Analysis: \n{final_result_raw}")

                        final_parts = final_result_raw.split("**Final JSON Output:**")
                        refined_cot_output = final_parts[0].replace("**Refined CoT Output:**", "").strip()
                        final_json_part_raw = final_parts[1]

                        start_index = final_json_part_raw.find('{')
                        end_index = final_json_part_raw.rfind('}')
                        if start_index == -1 or end_index == -1:
                            raise ValueError("No valid JSON found in the final LLM response.")

                        final_json_str = final_json_part_raw[start_index:end_index + 1]
                        final_llm_output = json.loads(final_json_str)

                        # ------------------ EVALUATION ------------------
                        # 使用最终结果进行评估
                        information = {
                            'ground_truth': ground_truth,
                            'eval_dict': final_llm_output  # 使用最终的输出进行评估
                        }

                        messages = [
                            {"role": "system", "content": ''},  # 你的评估System Prompt
                            {"role": "user", "content": fill_in_placeholders(self.prompts['eval'], information)}
                        ]

                        print(f"\n............... Evaluating final refined output ...............")
                        eval_completion = completion_with_backoff(messages, 'gpt-4o', backend='OpenRouter')

                        start_index = eval_completion.rfind('{')
                        end_index = eval_completion.rfind('}')
                        json_str = eval_completion[start_index:end_index + 1]
                        eval_result = json.loads(json_str)
                        eval_results.append(eval_result)

                        # 记录最终日志
                        log.append(f"\n[STAGE 2] Refined CoT Output:\n{refined_cot_output}")
                        log.append(f"[STAGE 2] Final LLM Output (for eval): {json.dumps(final_llm_output, indent=2)}")
                        print(f"Final LLM Output: {json.dumps(final_llm_output, indent=2)}")
                        log.append(f"Eval Result: {eval_result}")

                        success = True

                    except (ValueError, json.JSONDecodeError, KeyError, TypeError, RetryError) as e:
                        retries += 1
                        log.append(f"Error encountered in Attempt {retries}: {str(e)}")
                        print(f"Error in Attempt {retries}: {str(e)}")

                if not success:
                    log.append(f"Failed to process Error Version {idx + 1} after {MAX_RETRIES} attempts.")
                    print(f"Failed to process Error Version {idx + 1} after {MAX_RETRIES} attempts.")

        except (ValueError, json.JSONDecodeError, KeyError) as e:
            print(f"Exception occurred during processing of query {query['id']}: {str(e)}")

        finally:
            # 文件名中加入 "self_refine" 标识
            output_filename = os.path.join(eval_folder,
                                           f'eval_{model_type.replace("qwen/", "").replace(":", "_")}_rubber_duck_self_refine_on_bench_v3.jsonl')
            with open(output_filename, 'a') as jsonl_file:
                eval_result_dict = {
                    'id': query['id'],
                    'eval_result': eval_results
                }
                jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, eval_results

    def rubber_duck_eval_self_consistency(self, queries, model_type, eval_folder, individual_workspace, n_samples=5,
                                          temperature=0.7):
        """
        Modified version of rubber_duck_eval for Self-Consistency.
        It generates multiple responses and uses a majority vote to determine the final answer.
        """
        log = []
        query = queries

        error_versions = query.get('error_versions')
        if not error_versions:
            raise ValueError("No error versions found in the query.")

        log.append(
            f"\n------------------------------------- Processing Query (Self-Consistency) -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}"""

        MAX_RETRIES = 5  # 这是针对每个样本的重试次数
        eval_results = []
        print(f"\n**********Verifying ID: {query['id']} (Self-Consistency, n={n_samples})**********")

        try:
            for idx, error_version in tqdm(enumerate(error_versions)):
                log.append(f"\n--- Processing Error Version {idx + 1}/{len(error_versions)} ---")

                modified_code = error_version['modified_code']
                error_message = extract_traceback(error_version.get('execution_output', ''))

                if error_message is None:
                    log.append("Skipping error version due to missing execution output.")
                    break

                ground_truth = {
                    "cause_error_line": error_version["cause_error_line"],
                    "effect_error_line": error_version["effect_error_line"],
                    "execution_output": error_message
                }

                log.append(f"\nModified Code:\n{modified_code}")
                log.append(f"Ground Truth: {json.dumps(ground_truth, indent=2)}")

                # ------------------ SAMPLING STAGE ------------------
                all_sample_outputs = []
                log.append(f"\n............... Generating {n_samples} samples ...............")
                print(f"\n............... Generating {n_samples} samples for error version {idx + 1}/{len(error_versions)} ...............")

                for i in range(n_samples):
                    retries = 0
                    sample_success = False
                    while retries < MAX_RETRIES and not sample_success:
                        try:
                            # 假设 self.generate 支持 temperature 参数
                            # 如果不支持，需要在 self.generate 内部传递给 completion_with_backoff
                            result = self.generate(prompt, model_type=model_type, code=modified_code,
                                                   backend='OpenRouter', temperature=temperature)

                            start_index = result.rfind('{')
                            end_index = result.rfind('}')
                            if start_index == -1 or end_index == -1:
                                raise ValueError("No valid JSON found in the LLM sample response.")

                            json_str = result[start_index:end_index + 1]
                            llm_output = json.loads(json_str)

                            all_sample_outputs.append(llm_output)
                            log.append(
                                f"--- Sample {i + 1}/{n_samples} successful. JSON: {json.dumps(llm_output, indent=2)}")
                            sample_success = True

                        except (ValueError, json.JSONDecodeError, KeyError, TypeError, RetryError) as e:
                            retries += 1
                            log.append(f"Error encountered in Sample {i + 1} Attempt {retries}: {str(e)}")
                            print(f"Error in Sample {i + 1} Attempt {retries}: {str(e)}")

                    if not sample_success:
                        log.append(
                            f"Failed to generate Sample {i + 1} after {MAX_RETRIES} attempts. Skipping this sample.")

                # ------------------ VOTING STAGE ------------------
                if not all_sample_outputs:
                    log.append("No successful samples were generated. Skipping evaluation for this error version.")
                    print("No successful samples were generated. Skipping evaluation.")
                    continue

                log.append(f"\n............... Performing Majority Vote ...............")
                final_llm_output = self._get_self_consistent_answer(all_sample_outputs)

                if final_llm_output is None:
                    log.append("Voting resulted in no clear winner or failed. Using the first sample as fallback.")
                    print("Voting failed. Using first sample as fallback.")
                    final_llm_output = all_sample_outputs[0]  # 回退策略

                log.append(f"Final Voted Output (for eval): {json.dumps(final_llm_output, indent=2)}")
                print(f"Final Voted Output: {json.dumps(final_llm_output, indent=2)}")

                # ------------------ EVALUATION ------------------
                information = {
                    'ground_truth': ground_truth,
                    'eval_dict': final_llm_output
                }

                messages = [
                    {"role": "system", "content": ''},  # 你的评估System Prompt
                    {"role": "user", "content": fill_in_placeholders(self.prompts['eval'], information)}
                ]

                print(f"\n............... Evaluating final voted output ...............")
                eval_completion = completion_with_backoff(messages, 'gpt-4o', backend='OpenRouter')

                start_index = eval_completion.rfind('{')
                end_index = eval_completion.rfind('}')
                json_str = eval_completion[start_index:end_index + 1]
                eval_result = json.loads(json_str)
                eval_results.append(eval_result)
                log.append(f"Eval Result: {eval_result}")

        except Exception as e:
            print(f"An unexpected error occurred during processing of query {query['id']}: {str(e)}")

        finally:
            output_filename = os.path.join(eval_folder,
                                           f'eval_{model_type.replace("qwen/", "_").replace(":", "_")}_self_consistency_n-{n_samples}_on_bench_v3.jsonl')
            with open(output_filename, 'a') as jsonl_file:
                eval_result_dict = {
                    'id': query['id'],
                    'eval_result': eval_results
                }
                jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, eval_results
