import io
import json
import os
import re
import shutil
import pandas as pd
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.error_inject_agent.prompt import ERROR_TYPE_PROMPT
from agents.utils import change_directory


def get_code2(response, file_name):
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


def get_code(response):

    all_python_code_blocks_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```', re.MULTILINE)
    all_code_blocks = all_python_code_blocks_pattern.findall(response)
    all_code_blocks_combined = '\n'.join(all_code_blocks)
    return all_code_blocks_combined


def clean_json_string(json_str):
    # Locate the injected_code value
    start_index = json_str.find('"injected_code": "') + len('"injected_code": "')
    end_index = json_str.find('",', start_index)

    # Extract the code part and replace newlines and quotes
    code_part = json_str[start_index:end_index]
    cleaned_code_part = code_part.replace('\n', '\\n').replace('"', '\"')

    # Replace the original code part in the json_str with the cleaned code part
    cleaned_json_str = json_str[:start_index] + cleaned_code_part + json_str[end_index:]

    return cleaned_json_str


def extract_csv_info_as_string(file_path):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Use StringIO to capture df.info() output
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    # Create a string with the CSV information
    csv_info_str = f"""
CSV File Information:
----------------------
Shape: {df.shape[0]} rows, {df.shape[1]} columns

Columns: {', '.join(df.columns)}

Data Types and Non-null Values:
{info_str}

Sample Data (First 5 Rows):
{df.head().to_string(index=False)}
"""

    # Statistical Summary(Numeric Columns):
    # {df.describe().to_string()}

    return csv_info_str


class ErrorSuggestAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.query = kwargs.get('query', '')
        self.data_information = kwargs.get('data_information', None)

    def generate(self, user_prompt, model_type, code, csv_info, concepts):

        workspace_structure = print_filesys_struture(self.workspace)
        
        information = {
            'workspace_structure': workspace_structure,
            'code': code,
            'query': user_prompt,
            'csv_info': csv_info,
            'concepts': concepts
        }


        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)})



        self.chat_history = self.chat_history + messages
        return completion_with_backoff(messages, model_type)

    def run(self, queries, model_type, code):
        log = []
        suggest_results = []
        file_name = queries['file_name']
        error_code_directory = os.path.join(self.workspace, 'error_code_dir')
        os.makedirs(error_code_directory, exist_ok=True)

        src = os.path.join(self.workspace, file_name)
        dst = os.path.join(error_code_directory, file_name)
        shutil.copy(src, dst)

        # Load the CSV file
        csv_info = extract_csv_info_as_string(src)

        query = queries
        print(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Concepts: {query['concepts']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        log.append(f"Ground Truth: {query['answers']}")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}
                    
    Constraints: {query['constraints']}
    
    Data File Name: {query['file_name']}
                    
    Format: {query['format']}
    
    Correct answer: {query['answers']}
    
    **Concepts: {query['concepts']}**
                    """

        concepts = query['concepts']
        log.append("\n\n...Generating error types...\n\n")
        result = self.generate(prompt, model_type=model_type, code=code, csv_info=csv_info, concepts=concepts)

        # Use the extracted variables as needed
        log.append(f"\nSuggest Result:\n{result}\n")

        # Wrap the extracted information
        suggest_results.append({
            'suggest_result': result
        })

        # log.append(f"Generated code for Query {index}:")
        # log.append(injected_code)
        # log.append("\n" + "-"*50)

        # Join the log list into a single string

        log_string = "\n".join(log)
        return log_string, suggest_results
