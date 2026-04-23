import argparse
import base64
import logging
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.plot_agent import PlotAgent
from openai import OpenAI
from agents.config.openai import get_api_config
from matplotbench_runtime import (
    copy_benchmark_inputs,
    ensure_example_workspace,
    load_benchmark_instructions,
    resolve_benchmark_dir,
)


def sanitize_label(value):
    return value.replace("/", "_").replace(":", "_").replace(".", "_").replace("-", "_")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def resolve_eval_images(ground_truth, image, rollback, benchmark_dir):
    benchmark_dir = resolve_benchmark_dir(benchmark_dir)
    ground_truth_dir = benchmark_dir / "ground_truth"

    if not os.path.exists(f'{image}'):
        if os.path.exists(f'{rollback}'):
            reference_path = str(ground_truth_dir / ground_truth)
            generated_path = f"{rollback}"
        else:
            empty_path = str(ground_truth_dir / 'empty.png')
            reference_path = empty_path
            generated_path = empty_path
    else:
        reference_path = str(ground_truth_dir / ground_truth)
        generated_path = f"{image}"

    return benchmark_dir, reference_path, generated_path


def completion_length_kwargs(model_name, token_limit):
    if get_api_config(model_name)["provider"] == "openai":
        return {"max_completion_tokens": token_limit}
    return {"max_tokens": token_limit}


def gpt_4_evaluate(code, query, image, eval_model):
    if not os.path.exists(f'{image}'):
        executable = 'False'
    else:
        executable = 'True'

    api_config = get_api_config(eval_model)
    client = OpenAI(
        api_key=api_config["api_key"],
        base_url=api_config["base_url"], )

    response = client.chat.completions.create(
        model=eval_model,
        temperature=0.2,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f'''You are an excellent judge at evaluating generated code given an user query. You will be giving scores on how well a piece of code adheres to an user query by carefully reading each line of code and determine whether each line of code succeeds in carrying out the user query.
                        
                        A user query, a piece of code and an executability flag will be given to you. If the Executability is False, then the final score should be 0.


                         **User Query**: {query}

                         **Code**:
                         """
                         {code}
                         """
                         
                         **Executability**: {executable}
                         

 Carefully read through each line of code. Scoring can be carried out in the following aspect:
1. Code correctness (Code executability): Can the code correctly achieve the requirements in the user query? You should carefully read each line of the code, think of the effect each line of code would achieve, and determine whether each line of code contributes to the successful implementation of requirements in the user query. If the Executability is False, then the final score should be 0.

After scoring from the above aspect, please give a final score. The final score is preceded by the [FINAL SCORE] token.
For example [FINAL SCORE]: 40. A final score must be generated.''',
                    },
                ],
            }
        ],
        **completion_length_kwargs(eval_model, 1000),
    )
    return response.choices[0].message


def gpt_4v_evaluate(ground_truth, image, rollback, benchmark_dir, eval_model):
    benchmark_dir, reference_path, generated_path = resolve_eval_images(
        ground_truth,
        image,
        rollback,
        benchmark_dir,
    )

    api_config = get_api_config(eval_model)
    client = OpenAI(
        api_key=api_config["api_key"],
        base_url=api_config["base_url"],)
    base64_image1 = encode_image(reference_path)
    base64_image2 = encode_image(generated_path)

    response = client.chat.completions.create(
      model=eval_model,
      temperature=0.2,
      messages=[
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": f'''You are an excellent judge at evaluating visualization plots between a model generated plot and the ground truth. You will be giving scores on how well it matches the ground truth plot.
               
               The generated plot will be given to you as the first figure. If the first figure is blank, that means the code failed to generate a figure.
               Another plot will be given to you as the second figure, which is the desired outcome of the user query, meaning it is the ground truth for you to reference.
               Please compare the two figures head to head and rate them.
               Suppose the second figure has a score of 100, rate the first figure on a scale from 0 to 100.
               Scoring should be carried out in the following aspect:
               1. Plot correctness: 
               Compare closely between the generated plot and the ground truth, the more resemblance the generated plot has compared to the ground truth, the higher the score. The score should be proportionate to the resemblance between the two plots.
               In some rare occurrence, see if the data points are generated randomly according to the query, if so, the generated plot may not perfectly match the ground truth, but it is correct nonetheless.
               Only rate the first figure, the second figure is only for reference.
               If the first figure is blank, that means the code failed to generate a figure. Give a score of 0 on the Plot correctness.
                After scoring from the above aspect, please give a final score. The final score is preceded by the [FINAL SCORE] token.
               For example [FINAL SCORE]: 40.''',
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image2}",
              },
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image1}",
              },
            },
          ],
        }
      ],
      **completion_length_kwargs(eval_model, 1000),
    )
    return response.choices[0].message


def rubric_vlm_evaluate(query, ground_truth, image, rollback, benchmark_dir, eval_model):
    _, reference_path, generated_path = resolve_eval_images(
        ground_truth,
        image,
        rollback,
        benchmark_dir,
    )

    api_config = get_api_config(eval_model)
    client = OpenAI(
        api_key=api_config["api_key"],
        base_url=api_config["base_url"],
    )
    base64_reference = encode_image(reference_path)
    base64_generated = encode_image(generated_path)

    response = client.chat.completions.create(
      model=eval_model,
      temperature=0.2,
      messages=[
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": f'''You are an expert judge for query-conditioned visualization generation.

Evaluate the first figure against both the user query and the second figure (ground-truth reference).

User query:
"""
{query}
"""

Scoring rubric:
1. Task Compliance (0-100)
- Does the generated figure satisfy the chart type, hierarchy, layout, required text, and required visual elements in the query?

2. Structural Match (0-100)
- Does the generated figure match the reference in subplot count, topology, global layout, hierarchy depth, and major geometry?

3. Visual Encoding Match (0-100)
- Does the generated figure match the reference in colors, legends, axes/scales, projections, markers, fills, and highlighted regions when relevant?

4. Readability (0-100)
- Is the figure legible and well presented, without severe overlap, clutter, or broken layout?

Important rules:
- If the generated figure is blank or effectively missing the main chart content, scores should be near 0.
- If the figure differs from the reference in nonessential styling but clearly satisfies the query structure, do not over-penalize it.
- If the task is stochastic, prioritize semantic correctness and chart structure over exact pixel resemblance.

After a short explanation, output EXACTLY these lines:
[TASK COMPLIANCE]: <0-100>
[STRUCTURAL MATCH]: <0-100>
[VISUAL ENCODING]: <0-100>
[READABILITY]: <0-100>
[RUBRIC SCORE]: <0-100>

Use this weighted formula:
RUBRIC SCORE = 0.4 * Task Compliance + 0.3 * Structural Match + 0.2 * Visual Encoding Match + 0.1 * Readability
''',
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_generated}",
              },
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_reference}",
              },
            },
          ],
        }
      ],
      **completion_length_kwargs(eval_model, 1200),
    )
    return response.choices[0].message


def mainworkflow(
    test_sample_id,
    workspace,
    benchmark_dir=None,
    direct_eval=False,
    eval_model='gpt-5.4',
    generated_model_name='google/gemini-3-flash-preview',
    run_rubric_eval=False,
    skip_legacy_eval=False,
):
    benchmark_dir = resolve_benchmark_dir(benchmark_dir)
    directory = ensure_example_workspace(workspace, test_sample_id)
    eval_log_name = f"eval_{sanitize_label(generated_model_name)}_by_{sanitize_label(eval_model)}.log"
    rubric_log_name = f"eval_rubric_{sanitize_label(generated_model_name)}_by_{sanitize_label(eval_model)}.log"
    initial_log_name = rubric_log_name if skip_legacy_eval and run_rubric_eval else eval_log_name

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(directory, initial_log_name),
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True,
    )
    config = {'workspace': str(directory)}

    data = load_benchmark_instructions(benchmark_dir)
    simple_instruction = data[test_sample_id - 1]["simple_instruction"]
    expert_instruction = data[test_sample_id - 1]["expert_instruction"]

    if direct_eval:
        pass
    else:
        copy_benchmark_inputs(benchmark_dir, test_sample_id, directory)

        logging.info('=========Plotting=========')

        action_agent = PlotAgent(config, query=simple_instruction)
        logging.info('=========Novice 4 Plotting=========')
        logging.info(action_agent.run_initial('gpt-4', 'novice_4.png'))
        action_agent = PlotAgent(config, query=simple_instruction)
        logging.info('=========Novice 3.5 Plotting=========')
        logging.info(action_agent.run_initial('gpt-3.5-turbo', 'novice_35.png'))

    for model_type in [generated_model_name]:
        for query_type in ['novice']:
            print(f'=========Evaluating {model_type} {query_type}=========')
            ground_truth = f"example_{test_sample_id}.png"
            logging.info(f'=========Evaluating {model_type} {query_type}=========')
            query = simple_instruction

            image = f'{directory}/novice_final.png'
            image_rollback = f'{directory}/novice.png'



            if not skip_legacy_eval:
                plot_result = gpt_4v_evaluate(ground_truth, image, image_rollback, benchmark_dir, eval_model)
                logging.info(plot_result)

            if run_rubric_eval:
                logging.basicConfig(
                    level=logging.INFO,
                    filename=os.path.join(directory, rubric_log_name),
                    filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    force=True,
                )
                logging.info(f'=========Rubric Evaluating {model_type} {query_type}=========')
                rubric_result = rubric_vlm_evaluate(
                    query=query,
                    ground_truth=ground_truth,
                    image=image,
                    rollback=image_rollback,
                    benchmark_dir=benchmark_dir,
                    eval_model=eval_model,
                )
                logging.info(rubric_result)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('idx', type=int)
    parser.add_argument('--workspace', type=str, default='./workspace')
    parser.add_argument('--benchmark_dir', type=str, default=None)
    parser.add_argument('--direct_eval', action='store_true')
    parser.add_argument('--eval_model', type=str, default='gpt-5.4')
    parser.add_argument('--generated_model_name', type=str, default='google/gemini-3-flash-preview')
    parser.add_argument('--run_rubric_eval', action='store_true')
    parser.add_argument('--skip_legacy_eval', action='store_true')
    args = parser.parse_args()

    mainworkflow(
        args.idx,
        workspace=args.workspace,
        benchmark_dir=args.benchmark_dir,
        direct_eval=args.direct_eval,
        eval_model=args.eval_model,
        generated_model_name=args.generated_model_name,
        run_rubric_eval=args.run_rubric_eval,
        skip_legacy_eval=args.skip_legacy_eval,
    )
