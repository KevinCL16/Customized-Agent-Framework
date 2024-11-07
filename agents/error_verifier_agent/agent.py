import json
import os
import re
import shutil
from tqdm import tqdm
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.utils import change_directory


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

    def generate(self, user_prompt, model_type, code):
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
        return completion_with_backoff(messages, model_type)

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

    def run_with_other_agent(self, queries, model_type, from_prev_agent):
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
        eval_result = completion_with_backoff(messages, model_type)

        eval_result_dict = {
            'id': query['id'],
            'eval_result': eval_result
        }

        result_dict['eval_result'] = eval_result

        # 记录验证结果
        log.append(f"\nVerifier Result:\n{json.dumps(result_dict, indent=2)}\n")

        # 将结果写入文件
        with open(os.path.join(eval_folder, 'eval_result_v2_prompt.jsonl'), 'a') as jsonl_file:
            jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, result_dict

