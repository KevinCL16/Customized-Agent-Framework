import pandas as pd
import json
import os
import shutil
import subprocess
import sys
from agents.utils import change_directory
from datetime import datetime
from abc import ABC, abstractmethod

def prepare_data(input_data, data_ids=None, data_range=None):
    with open(input_data, 'r') as f:
        instructions = json.load(f)
    
    if data_ids:
        instructions = [inst for inst in instructions if inst['id'] in data_ids]
    elif data_range:
        start, end = data_range
        instructions = [inst for inst in instructions if start <= inst['id'] <= end]
    
    return instructions

class OutputHandler(ABC):
    @abstractmethod
    def handle(self, method_output, agent_name, method_name, individual_workspace, args):
        pass

class CodeOutputHandler(OutputHandler):
    def handle(self, method_output, agent_name, method_name, individual_workspace, args):
        log, code = method_output
        file_name = f'code_action_{agent_name}_{method_name}.py'
        with open(os.path.join(individual_workspace, file_name), 'w') as f:
            f.write(code)
        return log, code, file_name

class AnalysisOutputHandler(OutputHandler):
    def handle(self, method_output, agent_name, method_name, individual_workspace, args):
        # Assuming the analysis output is a dictionary with 'log' and 'result' keys
        log, verifier_result = method_output
        error_message = verifier_result.get('log', '')
        wrong_code = verifier_result.get('code', '')
        file_name = f'analysis_{agent_name}_{method_name}.txt'
        with open(os.path.join(individual_workspace, file_name), 'w') as f:
            f.write(f"Log:\n{log}\n\nError message:\n{error_message}\n\nWrong code:\n{wrong_code}")
        return log, error_message, file_name

class AgentEnvironment:
    def __init__(self, workspace, config):
        self.workspace = workspace
        self.config = config
        self.agents = {}
        self.data_store = {}
        self.instructions = None
        self.data_folder = config.get('data_folder', './InfiAgent_data/da-dev-tables')
        self.log_file = os.path.join(workspace, 'agent_workflow.log')
        self.output_handlers = {
            'code': CodeOutputHandler(),
            'analysis': AnalysisOutputHandler(),
        }

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
            individual_directory = self.workspace + f'/example {d_id}/'
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
            file_path = file_name
            if not os.path.exists(file_path):
                return f"Error: File {file_name} not found in workspace."

            try:
                result = subprocess.run(
                    [sys.executable, file_path],
                    capture_output=True,
                    text=True
                )
                return result.stdout + result.stderr
            except Exception as e:
                return f"Error executing {file_name}: {str(e)}"

    def log_action(self, action, agent_name, method_name, code, log, individual_workspace):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
{'='*80}
TIMESTAMP: {timestamp}
ACTION: {action.upper()}
AGENT: {agent_name}
METHOD: {method_name}
WORKSPACE: {individual_workspace}
{'='*80}

LOG OUTPUT:
{log}

{'='*80}
"""
        individual_log_file = os.path.join(individual_workspace, f'{agent_name}_{method_name}_log.txt')
        with open(individual_log_file, 'a') as f:
            f.write(log_entry)
        
        return log_entry  # Return the log entry

    def is_execution_successful(self, log):
        return 'Traceback (most recent call last):' not in log and 'Incorrect Answer:' not in log and 'Error:' not in log

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
            output_type = step.get('output_type', 'code')  # Default to 'code' if not specified

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
            
            step_results = []
            for instruction, individual_workspace in zip(self.instructions, workspace_list):
                args['queries'] = instruction
                method_output = method(**args)

                handler = self.output_handlers.get(output_type)
                if handler:
                    log, result, file_name = handler.handle(method_output, agent_name, method_name, individual_workspace, args)
                    
                    # Log output generation
                    generation_log = self.log_action("Generate", agent_name, method_name, result, log, individual_workspace)
                    full_log = generation_log
                    
                    if output_type == 'code':
                        execution_output = self.execute_code(file_name, individual_workspace)
                        
                        # Log code execution
                        execution_log = self.log_action("Execute", agent_name, method_name, result, execution_output, individual_workspace)
                        full_log += execution_log
                        
                        is_successful = self.is_execution_successful(execution_output)
                    else:  # output_type == 'analysis'
                        is_successful = self.is_execution_successful(log)
                    
                    if not is_successful:
                        debug_method = getattr(agent, f"debug_{method_name}", None)
                        if debug_method:  
                            while not is_successful:
                                print(f"Error detected in {file_name}. Initiating debug process.")
                                debug_args = args.copy()
                                debug_args['error_message'] = execution_output if output_type == 'code' else log
                                debug_args['buggy_code'] = result
                                
                                debug_output = debug_method(**debug_args)
                                if isinstance(debug_output, tuple) and len(debug_output) == 2:
                                    debug_log, debug_code = debug_output
                                    if debug_code:
                                        with open(os.path.join(individual_workspace, file_name), 'w') as f:
                                            f.write(debug_code)
                                        
                                        # Log debugging
                                        debug_log_entry = self.log_action("Debug", agent_name, method_name, debug_code, debug_log, individual_workspace)
                                        full_log += debug_log_entry
                                        
                                        if output_type == 'code':
                                            execution_output = self.execute_code(file_name, individual_workspace)
                                            
                                            # Log execution after debugging
                                            execution_log = self.log_action("Execute", agent_name, method_name, debug_code, execution_output, individual_workspace)
                                            full_log += execution_log
                                            
                                            is_successful = self.is_execution_successful(execution_output)
                                        else:
                                            is_successful = self.is_execution_successful(debug_log)
                                        
                                        result = debug_code
                                    else:
                                        print(f"Debug method for {method_name} returned None for debug_code.")
                                        break
                                else:
                                    print(f"Debug method for {method_name} did not return expected output.")
                                    break
                            
                            if not is_successful:
                                print(f"Failed to debug {file_name} after best attempts.")
                        else:
                            print(f"No debug method found for {method_name}.")
                else:
                    print(f"No handler found for output type: {output_type}")

                step_results.append({'log': full_log, 'result': result})

            # Store the output if specified
            if 'output' in step:
                self.data_store[step['output']] = step_results

            results[f"{agent_name}_{method_name}"] = step_results
        
        return results