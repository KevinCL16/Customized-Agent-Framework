import argparse
import json
import pdb
import sys
import io
from tqdm import tqdm
from agents.query_expansion_agent import QueryExpansionAgent
from agents.plot_agent import PlotAgent
from agents.visual_refine_agent import VisualRefineAgent
import logging
import os
import matplotlib.pyplot as plt
from agents.utils import is_run_code_success, run_code, get_code

parser = argparse.ArgumentParser()
parser.add_argument('--workspace', type=str, default='./workspace')
parser.add_argument('--model_type', type=str, default='gpt-4o')
parser.add_argument('--visual_refine', type=bool, default=True)
args = parser.parse_args()


def mainworkflow(expert_instruction, simple_instruction, workspace, update_callback=None, max_try=3, model='gpt-4o'):
    output_buffer = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = output_buffer

    def flush_output():
        output = output_buffer.getvalue()
        if output and update_callback:
            update_callback(terminal_output=output)
        output_buffer.truncate(0)
        output_buffer.seek(0)

    try:
        print('=========Query Expansion AGENT=========')
        config = {'workspace': workspace}
        print(f"config: {config}")
        print(f"Using model: {model}")
        flush_output()

        query_expansion_agent = QueryExpansionAgent(expert_instruction, simple_instruction, model_type=model)
        expanded_simple_instruction = query_expansion_agent.run('simple')
        print('=========Expanded Simple Instruction=========')
        flush_output()

        if update_callback:
            update_callback(expanded_instruction=expanded_simple_instruction)

        print('=========Plotting=========')
        action_agent = PlotAgent(config, expanded_simple_instruction)
        print(f'========={model} Plotting=========')
        flush_output()
        novice_log, novice_code = action_agent.run_initial(model, 'novice.png')
        logging.info(novice_log)
        print('=========Using Original Code for Visual Feedback=========')
        flush_output()

        if update_callback:
            update_callback(code=novice_code)

        visual_feedback = ""
        if args.visual_refine and os.path.exists(f'{workspace}/novice.png'):
            if update_callback:
                update_callback(figure=os.path.join(workspace, 'novice.png'))
            print('Use original code for visual feedback')
            flush_output()
            visual_refine_agent = VisualRefineAgent('novice.png', config, '', simple_instruction)
            visual_feedback = visual_refine_agent.run(model, 'novice', 'novice_final.png')

            if update_callback:
                update_callback(visual_feedback=visual_feedback)

            print('=========Plotting with Visual Feedback=========')
            flush_output()
            final_instruction = '' + '\n\n' + visual_feedback
            action_agent = PlotAgent(config, final_instruction)
            novice_log, novice_code = action_agent.run_vis(model, 'novice_final.png')
            logging.info(novice_log)

            if update_callback:
                update_callback(figure=os.path.join(workspace, 'novice_final.png'))

        result = {
            'code': novice_code,
            'visual_feedback': visual_feedback if args.visual_refine and os.path.exists(
                f'{workspace}/novice.png') else '',
            'figure_path': os.path.join(workspace, 'novice_final.png' if args.visual_refine else 'novice.png')
        }

    finally:
        sys.stdout = original_stdout

    return result


def check_refined_code_executable(refined_code, model_type, query_type, workspace):
    file_name = f'code_action_{model_type}_{query_type}_refined.py'
    with open(os.path.join(workspace, file_name), 'w') as f1:
        f1.write(refined_code)
    log = run_code(workspace, file_name)

    return is_run_code_success(log)


if __name__ == "__main__":
    workspace_base = args.workspace
    data_path = '/home/zhoupeng/project/LLM/agent/plotagent/benchmark/newPlotAgent/plot-agent/benchmark_data/'
    data = json.load(open(f'{data_path}/benchmark_instructions.json'))

    for item in tqdm(data):
        novice_instruction = item['simple_instruction']
        expert_instruction = item['expert_instruction']
        example_id = item['id']
        directory_path = f'{workspace_base}/example_{example_id}'

        if not os.path.exists(directory_path):
            os.mkdir(directory_path)
            print(f"Directory '{directory_path}' created successfully.")
            input_path = f'{data_path}/data/{example_id}'
            if os.path.exists(input_path):
                os.system(f'cp -r {input_path}/* {directory_path}')
        else:
            print(f"Directory '{directory_path}' already exists.")
            continue

        logging.basicConfig(level=logging.INFO, filename=f'{directory_path}/workflow.log', filemode='w',
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        mainworkflow(expert_instruction, novice_instruction, workspace=directory_path, model=args.model_type)