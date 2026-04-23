import ast
import os
import re
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.utils import change_directory
from agents.plot_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, VIS_SYSTEM_PROMPT, VIS_USER_PROMPT, ERROR_PROMPT, ZERO_SHOT_COT_PROMPT


class PlotAgent(GenericAgent):


    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.query = kwargs.get('query', '')
        self.data_information = kwargs.get('data_information', None)

    def _workspace_path(self):
        if isinstance(self.workspace, dict):
            return self.workspace["workspace"]
        return self.workspace

    def _sanitize_model_type(self, model_type):
        return model_type.replace("/", "_").replace(":", "_")

    def _target_image_exists(self, workspace_path, image_file):
        return os.path.exists(os.path.join(workspace_path, image_file))

    def _strip_blocking_show_calls(self, code):
        # Remove blocking matplotlib display calls during batch experiments.
        patterns = [
            r'(?m)^[ \t]*plt\.show\s*\([^)]*\)\s*;?\s*$',
            r'(?m)^[ \t]*matplotlib\.pyplot\.show\s*\([^)]*\)\s*;?\s*$',
            r'(?m)^[ \t]*from matplotlib import pyplot as plt\s*;?\s*$',
        ]

        cleaned_code = code
        for pattern in patterns[:2]:
            cleaned_code = re.sub(pattern, '', cleaned_code)

        # Handle inline cases such as `foo(); plt.show()`.
        cleaned_code = re.sub(r';\s*plt\.show\s*\([^)]*\)\s*', '', cleaned_code)
        cleaned_code = re.sub(r';\s*matplotlib\.pyplot\.show\s*\([^)]*\)\s*', '', cleaned_code)
        return cleaned_code

    def _ensure_entrypoint(self, code):
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code

        has_main_guard = False
        top_level_functions = []
        called_functions = set()

        for node in tree.body:
            if isinstance(node, ast.If):
                test = node.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "__name__"
                    and len(test.comparators) == 1
                    and isinstance(test.comparators[0], ast.Constant)
                    and test.comparators[0].value == "__main__"
                ):
                    has_main_guard = True
            elif isinstance(node, ast.FunctionDef):
                top_level_functions.append(node)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name):
                    called_functions.add(func.id)

        if has_main_guard:
            return code

        candidate = None
        for func in reversed(top_level_functions):
            if func.name in called_functions:
                return code
            if not func.args.args and not func.args.posonlyargs and not func.args.kwonlyargs:
                candidate = func.name
                break

        if candidate is None:
            return code

        return code.rstrip() + f"\n\n{candidate}()\n"

    def generate(self, user_prompt, model_type, query_type, file_name):

        workspace_structure = print_filesys_struture(self._workspace_path())
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
            'query': user_prompt
        }

        if query_type == 'initial':
            messages = []
            messages.append({"role": "system", "content": fill_in_placeholders(INITIAL_SYSTEM_PROMPT, information)})
            messages.append({"role": "user", "content": fill_in_placeholders(INITIAL_USER_PROMPT, information)})
            # print(messages)
        else:
            messages = []
            messages.append({"role": "system", "content": fill_in_placeholders(VIS_SYSTEM_PROMPT, information)})
            messages.append({"role": "user", "content": fill_in_placeholders(VIS_USER_PROMPT, information)})
            # print(messages)

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

    def run(self, query=None, model_type='google/gemini-3-flash-preview', query_type='initial', file_name='plot.png', queries=None, individual_workspace=None):
        try_count = 0
        image_file = file_name
        code = ''
        if query is None:
            if isinstance(queries, dict):
                query = queries.get('simple_instruction') or queries.get('expert_instruction') or str(queries)
            else:
                query = queries
        if query is None:
            query = self.query
        result = self.generate(query, model_type=model_type, query_type=query_type, file_name=file_name)
        while try_count < 4:
            
            if not isinstance(result, str):  # 如果返回的不是字符串，那么就是出错了
                return 'TOO LONG FOR MODEL', code
            if model_type != 'gpt-4':
                code = self.get_code(result)
                if code.strip() == '':
                    code = self.get_code2(result,image_file) #第二次尝试获得代码
                    if code.strip() == '':
                        code = result  #只能用原始回答
                        if code.strip() == '' and try_count == 0: #有可能是因为没有extend query写好了代码，所以他不写代码
                            code = self.get_code(query)
            else:
                code = self.get_code(result)
            code = self._strip_blocking_show_calls(code)
            code = self._ensure_entrypoint(code)
            self.chat_history.append({"role": "assistant", "content": result if result.strip() != '' else ''})


            safe_model_type = self._sanitize_model_type(model_type)
            file_name = f'code_action_{safe_model_type}_{query_type}_{try_count}.py'
            workspace_path = self._workspace_path()
            with open(os.path.join(workspace_path, file_name), 'w', encoding='utf-8') as f:
                f.write(code)
            error = None
            log = run_code(workspace_path, file_name)

            if is_run_code_success(log):
                if not self._target_image_exists(workspace_path, image_file):
                    log = log + '\n' + 'No plot generated.'
                    
                    self.chat_history.append({"role": "user", "content": fill_in_placeholders(ERROR_PROMPT,
                                                                                          {'error_message': f'No plot generated. When you complete a plot, remember to save it to a png file. The file name should be """{image_file}""".',
                                                                                           'data_information': self.data_information})})
                    try_count += 1
                    result = completion_with_backoff(self.chat_history, model_type=model_type)


                else:
                    return log, code

            else:
                error = get_error_message(log) if error is None else error
                # TODO error prompt
                self.chat_history.append({"role": "user", "content": fill_in_placeholders(ERROR_PROMPT,
                                                                                          {'error_message': error,
                                                                                           'data_information': self.data_information})})
                try_count += 1
                result = completion_with_backoff(self.chat_history, model_type=model_type)
                # print(result)

        return log, ''

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
        workspace_structure = print_filesys_struture(self._workspace_path())
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
            'query': self.query
        }
        if no_sysprompt:
            message.append({"role": "system", "content": ''''''})
        message.append({"role": "user", "content": fill_in_placeholders(INITIAL_USER_PROMPT, information)})
        result = completion_with_backoff(message, model_type)
        if not isinstance(result, str):
            return 'TOO LONG FOR MODEL', ''
        if model_type != 'gpt-4':
            code = self.get_code(result)
            if code == '':
                code = self.get_code2(result,file_name)
                if code == '':
                    code = result
        else:
            code = self.get_code(result)


        code = self._strip_blocking_show_calls(code)
        safe_model_type = self._sanitize_model_type(model_type)
        file_name = f'code_action_{safe_model_type}_{query_type}_0.py'
        workspace_path = self._workspace_path()
        with open(os.path.join(workspace_path, file_name), 'w', encoding='utf-8') as f:
            f.write(code)
        log = run_code(workspace_path, file_name)
        return log, code
    def run_one_time_zero_shot_COT(self, model_type, file_name,query_type='novice',no_sysprompt=False):
        
        print('========Plot AGENT Novice RUN========')
        message = []
        workspace_structure = print_filesys_struture(self._workspace_path())
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
            'query': self.query
        }
        message.append({"role": "system", "content": ''''''})
        message.append({"role": "user", "content": fill_in_placeholders(ZERO_SHOT_COT_PROMPT, information)})
        result = completion_with_backoff(message, model_type)
        if not isinstance(result, str):
            return 'TOO LONG FOR MODEL', ''
        if model_type != 'gpt-4':
            code = self.get_code(result)
            if code == '':
                code = self.get_code2(result,file_name)
                if code == '':
                    code = result
        else:
            code = self.get_code(result)

        code = self._strip_blocking_show_calls(code)
        safe_model_type = self._sanitize_model_type(model_type)
        file_name = f'code_action_{safe_model_type}_{query_type}_0.py'
        workspace_path = self._workspace_path()
        with open(os.path.join(workspace_path, file_name), 'w', encoding='utf-8') as f:
            f.write(code)
        log = run_code(workspace_path, file_name)
        return log, code
