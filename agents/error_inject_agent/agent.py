import json
import os
import re
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.utils import change_directory


class ErrorInjectAgent(GenericAgent):
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
            'query': user_prompt
        }


        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)})



        self.chat_history = self.chat_history + messages
        return completion_with_backoff(messages, model_type)

    def get_code(self, response):

        all_python_code_blocks_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```', re.MULTILINE)


        all_code_blocks = all_python_code_blocks_pattern.findall(response)
        all_code_blocks_combined = '\n'.join(all_code_blocks)
        return all_code_blocks_combined
    def get_code2(self, response,file_name):

        all_python_code_blocks_pattern = re.compile(r'```\s*([\s\S]+?)\s*```', re.MULTILINE)


        all_code_blocks = all_python_code_blocks_pattern.findall(response)
        all_code_blocks_combined = '\n'.join(all_code_blocks)
        if all_code_blocks_combined == '':

            response_lines = response.split('\n')
            code_lines = []
            code_start = False
            for line in response_lines:
                if line.find('import') == 0 or code_start:
                    code_lines.append(line)
                    code_start = True
                if code_start and line.find(file_name)!=-1 and line.find('(') !=-1 and line.find(')')!=-1 and line.find('(') < line.find(file_name)< line.find(')'): #要有文件名，同时要有函数调用

                    return '\n'.join(code_lines)
        return all_code_blocks_combined

    def clean_json_string(self, json_str):
        # Locate the injected_code value
        start_index = json_str.find('"injected_code": "') + len('"injected_code": "')
        end_index = json_str.find('",', start_index)

        # Extract the code part and replace newlines and quotes
        code_part = json_str[start_index:end_index]
        cleaned_code_part = code_part.replace('\n', '\\n').replace('"', '\"')

        # Replace the original code part in the json_str with the cleaned code part
        cleaned_json_str = json_str[:start_index] + cleaned_code_part + json_str[end_index:]

        return cleaned_json_str

    def run(self, queries, model_type, code):
        log = []
        injected_results = []
        
        if queries:
            for index, query in enumerate([queries], 1):
                log.append(f"\n--- Processing Query {index} ---")
                log.append(f"Question ID: {query['id']}")
                log.append(f"Question: {query['question']}")
                log.append(f"Constraints: {query['constraints']}")
                log.append(f"Data File: {query['file_name']}")
                log.append(f"Expected Format: {query['format']}")
                log.append(f"Ground Truth: {query['answers']}")

                prompt = f"""Question ID: {query['id']}
Question: {query['question']}
                
Constraints: {query['constraints']}

Data File Name: {query['file_name']}
                
Format: {query['format']}

Correct answer: {query['answers']}. Make sure your analysis results are identical with the annotated ground truth.
                """

                log.append("\nGenerating code...")
                result = self.generate(prompt, model_type=model_type, code=code)

                # Use a more general approach to match the JSON portion in the string
                try:
                    # Locate the first curly brace to the last one for extracting the JSON object
                    start_index = result.find('{')
                    end_index = result.rfind('}')

                    if start_index == -1 or end_index == -1:
                        raise ValueError("No valid JSON found in the input string.")

                    # Extract the JSON substring
                    json_str = result[start_index:end_index + 1]
                    cleaned_json_str = self.clean_json_string(json_str)

                    # Convert the extracted JSON string to a Python dictionary
                    result_dict = json.loads(cleaned_json_str)

                except json.JSONDecodeError as e:
                    raise ValueError(f"Error decoding JSON: {e}")

                # Extract and store the expected result
                injected_code = result_dict.get('injected_code', '')
                error_analysis = result_dict.get('error_analysis', {})
                error_type = error_analysis.get('error_type', '')
                error_explanation = error_analysis.get('explanation', '')
                expected_outcome = error_analysis.get('expected_outcome', '')

                # Use the extracted variables as needed
                log.append(f"Injected Code:\n{injected_code}")
                log.append(f"Error Type: {error_type}")
                log.append(f"Error Explanation: {error_explanation}")
                log.append(f"Expected Outcome: {expected_outcome}")

                # generated_code = self.get_code(injected_code)
                
                # Wrap the extracted information
                injected_results.append({
                    'code': injected_code,
                    'error_type': error_type,
                    'error_explanation': error_explanation,
                    'expected_outcome': expected_outcome
                })
                
                log.append(f"Generated code for Query {index}:")
                log.append(injected_code)
                log.append("\n" + "-"*50)
        else:
            log.append("Processing single query...")
            log.append(f"Query: {self.query}")
            
            result = self.generate(self.query, model_type=model_type, code=code)
            generated_code = self.get_code(result)
            
            # Extract and store the expected result for single query
            error_analysis = result.get('error_analysis', {})
            error_type = error_analysis.get('error_type', '')
            error_explanation = error_analysis.get('explanation', '')
            expected_outcome = error_analysis.get('expected_outcome', '')
            
            # Wrap the extracted information for single query
            injected_results.append({
                'code': generated_code,
                'error_type': error_type,
                'error_explanation': error_explanation,
                'expected_outcome': expected_outcome
            })

        # Join the log list into a single string
        log_string = "\n".join(log)
        return log_string, injected_results
