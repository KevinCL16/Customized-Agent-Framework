import pandas as pd
import json
import os
import shutil
import subprocess
import sys
from agents.utils import change_directory

def prepare_data(input_data, data_ids=None, data_range=None):
    with open(input_data, 'r') as f:
        instructions = json.load(f)
    
    if data_ids:
        instructions = [inst for inst in instructions if inst['id'] in data_ids]
    elif data_range:
        start, end = data_range
        instructions = [inst for inst in instructions if start <= inst['id'] <= end]
    
    return instructions

class AgentEnvironment:
    def __init__(self, workspace, config):
        self.workspace = workspace
        self.config = config
        self.agents = {}
        self.data_store = {}
        self.instructions = None
        self.data_folder = config.get('data_folder', './InfiAgent_data/da-dev-tables')

    def add_agent(self, agent_name, agent_class, **kwargs):
        self.agents[agent_name] = agent_class(self.workspace, **kwargs)

    def process_instruction_file(self, input_file, data_ids=None, data_range=None):
        with open(input_file, 'r') as f:
            instructions = [json.loads(line) for line in f]
        
        if data_ids:
            instructions = [inst for inst in instructions if inst['id'] in data_ids]
        elif data_range:
            start, end = data_range
            instructions = [inst for inst in instructions if start <= inst['id'] <= end]
        
        self.instructions = instructions

    def copy_data_files(self, data_ids, data_range):
        if data_ids:
            for d_id in data_ids:
                individual_directory = self.workspace + f'/example {d_id}'
                if not os.path.exists(individual_directory):
                    os.makedirs(individual_directory, exist_ok=True)
                    print(f"Directory '{individual_directory}' created successfully.")

        elif data_range:
            for d_id in data_range:
                individual_directory = self.workspace + f'/example {d_id}'
                if not os.path.exists(individual_directory):
                    os.makedirs(individual_directory, exist_ok=True)
                    print(f"Directory '{individual_directory}' created successfully.")

        workspace_list = []
        for instruction in self.instructions:
            d_id = instruction['id']
            individual_directory = self.workspace + f'/example {d_id}'
            workspace_list.append(individual_directory)

            file_name = instruction.get('file_name')
            if file_name:
                src = os.path.join(self.data_folder, file_name)
                dst = os.path.join(individual_directory, file_name)
                if os.path.exists(src):
                    shutil.copy(src, dst)
                else:
                    print(f"Warning: File {file_name} not found in data folder.")

        return workspace_list

    def execute_code(self, file_name, individual_workspace):
        with change_directory(individual_workspace):
            file_path = os.path.join(individual_workspace, file_name)
            if not os.path.exists(file_path):
                return f"Error: File {file_name} not found in workspace."

            try:
                # TODO: save execution artifacts into log and png
                result = subprocess.run(
                    [sys.executable, file_path],
                    capture_output=True,
                    text=True,
                    cwd=self.workspace
                )
                return result.stdout + result.stderr
            except Exception as e:
                return f"Error executing {file_name}: {str(e)}"


    def is_execution_successful(self, log):
        return 'Traceback (most recent call last):' not in log or 'Error:' not in log

    def run_workflow(self, workflow):
        results = {}
        
        # Process instruction file
        if 'input' in workflow[0]:
            input_file = workflow[0]['input'].get('data')
            data_ids = workflow[0].get('data_ids')
            data_range = workflow[0].get('data_range')
            if input_file:
                self.process_instruction_file(input_file, data_ids, data_range)
        
        # Copy relevant data files & Get test case workspace
        workspace_list = self.copy_data_files(data_ids, data_range)

        for step in workflow:
            agent_name = step['agent']
            method_name = step['method']
            args = step.get('args', {})
            
            if self.instructions:
                args['queries'] = self.instructions
            else:
                args['queries'] = None

            # See if current input is flowed from previous agent's output
            for arg_name, arg_value in args.items():
                if isinstance(arg_value, dict) and 'from' in arg_value:
                    args[arg_name] = self.data_store[arg_value['from']]

            agent = self.agents[agent_name]
            method = getattr(agent, method_name)
            method_output = method(**args)

            # If the result is a tuple containing code, execute it
            if isinstance(method_output, tuple) and len(method_output) == 2:
                logs, codes = method_output
                result = []
                for log, code, individual_workspace in zip(logs, codes, workspace_list):
                    file_name = f'code_action_{agent_name}_{method_name}.py'
                    with open(os.path.join(individual_workspace, file_name), 'w') as f:
                        f.write(code)
                    execution_log = self.execute_code(file_name, individual_workspace)
                    result.append({'log': log + "\n" + execution_log, 'code': code})

            # Store the output if specified
            if 'output' in step:
                self.data_store[step['output']] = result

            results[f"{agent_name}_{method_name}"] = result
        
        return results
