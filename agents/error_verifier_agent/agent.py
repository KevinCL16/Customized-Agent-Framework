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
        # error_code_list = []
        # error_code_content = [code]

        # Specify the jsonl file path
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

            # Write the entire dictionary as a single line to a jsonl file
            with open(os.path.join(error_code_directory, 'logical_error_verification.jsonl'), 'w') as jsonl_file:
                jsonl_file.write(json.dumps(result_dict, indent=4) + '\n')

            # Use the extracted variables as needed
            log.append(f"\nVerifier Result:\n{result}\n")


            # Wrap the extracted information
            verifier_results.append({
                'verifier_result': result
            })

            # log.append(f"Generated code for Query {index}:")
            # log.append(injected_code)
            # log.append("\n" + "-"*50)

        # Join the log list into a single string
        log_string = "\n".join(log)
        return log_string, verifier_results