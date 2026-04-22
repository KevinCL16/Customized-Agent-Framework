from tqdm import tqdm
from agents.plot_agent import PlotAgent
import logging
import os
from agents.utils import is_run_code_success, run_code, get_code
import argparse
from matplotbench_runtime import (
    copy_benchmark_inputs,
    ensure_example_workspace,
    filter_benchmark_items,
    load_benchmark_instructions,
)


def mainworkflow(expert_instruction, simple_instruction, workspace='./workspace',model_type='gpt-3.5-turbo',no_sysprompt=False):

    
    config = {'workspace': workspace}
    # GPT-3.5-turbo Plot Agent
    # Initial plotting
    action_agent = PlotAgent(config, query=simple_instruction)
    logging.info('=========Plotting=========')
    novice_35_log, novice_35_code = action_agent.run_one_time(model_type, 'novice.png',no_sysprompt=no_sysprompt)
    logging.info(novice_35_log)
    logging.info('=========Original Code=========')
    logging.info(novice_35_code)
    


def check_refined_code_executable(refined_code, model_type, query_type, workspace):
    file_name = f'code_action_{model_type}_{query_type}_refined.py'
    with open(os.path.join(workspace, file_name), 'w') as f1:
        f1.write(refined_code)
    log = run_code(workspace, file_name)

    return is_run_code_success(log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=str, default='./workspace')
    parser.add_argument('--model_type', type=str, default='google/gemini-3-flash-preview')
    parser.add_argument('--no_sysprompt',action='store_true')
    parser.add_argument('--benchmark_dir', type=str, default=None)
    parser.add_argument('--start_id', type=int, default=None)
    parser.add_argument('--end_id', type=int, default=None)
    parser.add_argument('--data_ids', nargs='*', type=int, default=None)
    args = parser.parse_args()

    workspace_base = args.workspace
    data = load_benchmark_instructions(args.benchmark_dir)
    data = filter_benchmark_items(
        data,
        start_id=args.start_id,
        end_id=args.end_id,
        data_ids=args.data_ids,
    )
    
    for item in tqdm(data):
        novice_instruction = item['simple_instruction']
        expert_instruction = item['expert_instruction']
        example_id = item['id']
        directory_path = ensure_example_workspace(workspace_base, example_id)
        copy_benchmark_inputs(args.benchmark_dir, example_id, directory_path)

        logging.basicConfig(
            level=logging.INFO,
            filename=os.path.join(directory_path, 'workflow.log'),
            filemode='w',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True,
        )
        mainworkflow(
            expert_instruction,
            novice_instruction,
            workspace=str(directory_path),
            model_type=args.model_type,
            no_sysprompt=args.no_sysprompt,
        )
