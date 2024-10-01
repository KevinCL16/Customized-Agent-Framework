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
        if queries:
            log = []
            code = []
            for query in queries:
                input_text = query['question']
                constraints = query['constraints']
                format = query['format']

                prompt = f"""Question ID: {query['id']}
Question: {input_text}
                
Constraints: {constraints}
                
Format: {format}
                """

                result = self.generate(prompt, model_type=model_type, file_name=file_name)
                code.append(self.get_code(result))
                log.append(f"Generated code:\n{code}\n")
        else:
            result = self.generate(self.query, model_type=model_type, file_name=file_name)
            code = self.get_code(result)
            log = f"Generated code:\n{code}\n"

        # Instead of running the code here, we'll return it
        return log, code

    def run_initial(self, model_type, file_name):
        print('========Plot AGENT Expert RUN========')
        self.chat_history = []
        log, code = self.run(self.query, model_type, 'initial', file_name)
        return log, code

    def run_vis(self, model_type, file_name):
        print('========Plot AGENT Novice RUN========')
        self.chat_history = []
        log, code = self.run(self.query, model_type, 'vis_refined', file_name)
        return log, code

    def run_one_time(self, model_type, file_name,query_type='novice',no_sysprompt=False):
        
        print('========Plot AGENT Novice RUN========')
        message = []
        workspace_structure = print_filesys_struture(self.workspace)
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
            'query': self.query
        }
        if no_sysprompt:
            message.append({"role": "system", "content": ''''''})
        message.append({"role": "user", "content": fill_in_placeholders(INITIAL_USER_PROMPT, information)})
        result = completion_with_backoff(message, model_type)
        if model_type != 'gpt-4':
            code = self.get_code(result)
            if code == '':
                code = self.get_code2(result,file_name)
                if code == '':
                    code = result
        else:
            code = self.get_code(result)


        file_name = f'code_action_{model_type}_{query_type}_0.py'
        with open(os.path.join(self.workspace, file_name), 'w') as f:
            f.write(code)
        log = run_code(self.workspace, file_name)
        return log, code
    def run_one_time_zero_shot_COT(self, model_type, file_name,query_type='novice',no_sysprompt=False):
        
        print('========Plot AGENT Novice RUN========')
        message = []
        workspace_structure = print_filesys_struture(self.workspace)
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
            'query': self.query
        }
        message.append({"role": "system", "content": ''''''})
        message.append({"role": "user", "content": fill_in_placeholders(ZERO_SHOT_COT_PROMPT, information)})
        result = completion_with_backoff(message, model_type)
        if model_type != 'gpt-4':
            code = self.get_code(result)
            if code == '':
                code = self.get_code2(result,file_name)
                if code == '':
                    code = result
        else:
            code = self.get_code(result)

        file_name = f'code_action_{model_type}_{query_type}_0.py'
        with open(os.path.join(self.workspace, file_name), 'w') as f:
            f.write(code)
        log = run_code(self.workspace, file_name)
        return log, code
