import argparse
from tqdm import tqdm
from agents.query_expansion_agent import QueryExpansionAgent
from agents.plot_agent import PlotAgent
from agents.visual_refine_agent import VisualRefineAgent
import logging
import os
from agents.utils import is_run_code_success, run_code, get_code
from matplotbench_runtime import (
    copy_benchmark_inputs,
    ensure_example_workspace,
    filter_benchmark_items,
    load_benchmark_instructions,
)

parser = argparse.ArgumentParser()
parser.add_argument('--workspace', type=str, default='./workspace')
parser.add_argument('--model_type', type=str, default='google/gemini-3-flash-preview')
parser.add_argument('--visual_refine', type=lambda x: str(x).lower() == 'true', default=True)
parser.add_argument(
    '--visual_refine_prompt_variant',
    type=str,
    default='default',
    choices=[
        'default',
        'capimagine',
        'cap_full',
        'cap_no_imagination',
        'cap_no_root_cause',
        'cap_no_revision_checklist',
        'cap_no_preserve_correct_parts',
    ],
)
parser.add_argument('--benchmark_dir', type=str, default=None)
parser.add_argument('--start_id', type=int, default=None)
parser.add_argument('--end_id', type=int, default=None)
parser.add_argument('--data_ids', nargs='*', type=int, default=None)
args = parser.parse_args()


def log_text_block(title, content):
    text = content if content and str(content).strip() else "<empty>"
    logging.info("========= %s =========\n%s", title, text)


def build_refinement_instruction(simple_instruction, expanded_instruction, original_code, visual_feedback):
    return f'''[Original User Query]
"""
{simple_instruction}
"""

[Expanded Planning Instruction]
"""
{expanded_instruction}
"""

[Current Plot Code]
```python
{original_code}
```

[CapImagine-Style Visual Reasoning]
"""
{visual_feedback}
"""

Rewrite the plotting code so that it satisfies the original user query, preserves any correct existing logic, and applies the visual reasoning feedback above.
'''


def uses_structured_visual_reasoning(prompt_variant):
    return prompt_variant != 'default'


def mainworkflow(
    expert_instruction,
    simple_instruction,
    workspace,
    update_callback=None,
    max_try=3,
    model='google/gemini-3-flash-preview',
    visual_refine_prompt_variant=None,
):
    # output_buffer = io.StringIO()
    # original_stdout = sys.stdout
    # sys.stdout = output_buffer

    '''def flush_output():
        output = output_buffer.getvalue()
        if output and update_callback:
            update_callback(terminal_output=output)
        output_buffer.truncate(0)
        output_buffer.seek(0)'''


    print('=========Query Expansion AGENT=========')
    config = {'workspace': workspace}
    print(f"config: {config}")
    print(f"Using model: {model}")


    query_expansion_agent = QueryExpansionAgent(config, model_type=model)
    expanded_simple_instruction = query_expansion_agent.run(simple_instruction)
    if isinstance(expanded_simple_instruction, list):
        expanded_simple_instruction = expanded_simple_instruction[0] if expanded_simple_instruction else simple_instruction
    print('=========Expanded Simple Instruction=========')
    log_text_block("Expanded Simple Instruction", expanded_simple_instruction)


    if update_callback:
        update_callback(expanded_instruction=expanded_simple_instruction)

    print('=========Plotting=========')
    action_agent = PlotAgent(config, query=expanded_simple_instruction)
    print(f'========={model} Plotting=========')

    novice_log, novice_code = action_agent.run_initial(model, 'novice.png')
    logging.info(novice_log)
    print('=========Using Original Code for Visual Feedback=========')


    if update_callback:
        update_callback(code=novice_code)

    prompt_variant = visual_refine_prompt_variant or args.visual_refine_prompt_variant
    visual_feedback = ""
    if args.visual_refine and os.path.exists(f'{workspace}/novice.png'):
        if update_callback:
            update_callback(figure=os.path.join(workspace, 'novice.png'))
        print('Use original code for visual feedback')
        logging.info("Using visual refine prompt variant: %s", prompt_variant)

        visual_refine_agent = VisualRefineAgent(
            plot_file='novice.png',
            workspace=config,
            query=simple_instruction,
            code=novice_code,
            prompt_variant=prompt_variant,
        )
        visual_feedback = visual_refine_agent.run(model, 'novice', 'novice_final.png')
        log_text_block("Visual Feedback", visual_feedback)

        if update_callback:
            update_callback(visual_feedback=visual_feedback)

        print('=========Plotting with Visual Feedback=========')

        if uses_structured_visual_reasoning(prompt_variant):
            final_instruction = build_refinement_instruction(
                simple_instruction=simple_instruction,
                expanded_instruction=expanded_simple_instruction,
                original_code=novice_code,
                visual_feedback=visual_feedback,
            )
        else:
            final_instruction = '\n\n' + visual_feedback
        log_text_block("Final Refinement Instruction", final_instruction)
        action_agent = PlotAgent(config, query=final_instruction)
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


    return result


def check_refined_code_executable(refined_code, model_type, query_type, workspace):
    file_name = f'code_action_{model_type}_{query_type}_refined.py'
    with open(os.path.join(workspace, file_name), 'w') as f1:
        f1.write(refined_code)
    log = run_code(workspace, file_name)

    return is_run_code_success(log)


if __name__ == "__main__":
    workspace_base = args.workspace
    data = load_benchmark_instructions(args.benchmark_dir)
    data = filter_benchmark_items(
        data,
        start_id=args.start_id,
        end_id=args.end_id,
        data_ids=args.data_ids,
    )
    failed_ids = []

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
        try:
            mainworkflow(
                expert_instruction,
                novice_instruction,
                workspace=str(directory_path),
                model=args.model_type,
            )
        except Exception as exc:
            failed_ids.append(example_id)
            logging.exception("Workflow failed for example %s", example_id)
            print(f"Example {example_id} failed: {exc}")

    if failed_ids:
        print(f"Failed example ids: {failed_ids}")