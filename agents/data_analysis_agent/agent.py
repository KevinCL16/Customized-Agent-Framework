import os
import re
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.utils import change_directory


class DataAnalysisAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.query = kwargs.get('query', '')
        self.data_information = kwargs.get('data_information', None)

    def generate(self, user_prompt, model_type, file_name):

        workspace_structure = print_filesys_struture(self.workspace)
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
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

    def run(self, queries, model_type, file_name):
        log = []
        code = []
        
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
                result = self.generate(prompt, model_type=model_type, file_name=file_name)
                generated_code = self.get_code(result)
                code.append(generated_code)
                
                log.append(f"Generated code for Query {index}:")
                log.append(generated_code)
                log.append("\n" + "-"*50)
        else:
            log.append("Processing single query...")
            log.append(f"Query: {self.query}")
            
            result = self.generate(self.query, model_type=model_type, file_name=file_name)
            generated_code = self.get_code(result)
            code = generated_code
            
            log.append("\nGenerated code:")
            log.append(generated_code)

        # Join the log list into a single string
        log_string = "\n".join(log)
        return log_string, ''.join(code)

    def debug_run(self, queries, model_type, file_name, error_message, buggy_code):
        log = []
        
        log.append("=== Debug Run Initiated ===")
        log.append(f"Model Type: {model_type}")
        log.append(f"File Name: {file_name}")
        
        log.append("\n--- Previous Error Information ---")
        log.append("Error Message:")
        log.append(error_message)
        
        # log.append("\nBuggy Code:")
        # log.append(buggy_code)
        
        if queries:
            debug_prompt = f"""The previous code generated for the data analysis task resulted in errors. 
            Here's the error information:
            
            {error_message}
            
            Here's the previous code that needs to be fixed:
            
            {buggy_code}
            
            
            Please review the error information and generate corrected code that:
            1. Fixes all identified errors
            2. Maintains the original functionality
            3. Follows the output format requirements
            4. Ensures results match the ground truth
            """
        else:
            debug_prompt = f"""The previous code generated for the data analysis task resulted in errors. 
            Here's the error information:
            
            {error_message}
            
            Here's the previous code that needs to be fixed:
            
            {buggy_code}
            
            Please review the error information and generate corrected code.
            """

        '''Question
        ID: {queries['id']}
        Question: {queries['question']}
        Constraints: {queries['constraints']}
        Data
        File: {queries['file_name']}
        Expected
        Format: {queries['format']}
        Ground
        Truth: {queries['answers']}'''

        log.append("\n--- Generating Corrected Code ---")
        result = self.generate(debug_prompt, model_type=model_type, file_name=file_name)
        corrected_code = self.get_code(result)
        
        log.append("Corrected code generated:")
        log.append(corrected_code)
        
        log.append("\n=== Debug Run Completed ===")

        return '\n'.join(log), corrected_code
