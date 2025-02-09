from agents.error_verifier_agent.prompt import MULTI_RUBBER_DUCK_EVAL_SYSTEM_PROMPT, MULTI_RUBBER_DUCK_EVAL_USER_PROMPT, MULTI_RUBBER_DUCK_EVAL_PROMPT, MULTI_RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT, MULTI_RUBBER_DUCK_ZERO_COT_USER_PROMPT
from agents.error_verifier_agent.agent import ErrorVerifierAgent


AGENT_CONFIG = {
    'workspace': './workspace/benchmark_evaluation',
    'agents': [
        {
            'name': 'multi_rubber_duck_eval_agent',
            'class': ErrorVerifierAgent,
            'prompts': {
                'system': MULTI_RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT,
                'user': MULTI_RUBBER_DUCK_ZERO_COT_USER_PROMPT,
                'eval': MULTI_RUBBER_DUCK_EVAL_PROMPT
            },
            'kwargs': {
                'query': 'Your default query here'
            }
        },
    ]
}

#
WORKFLOW = [
    {
        'agent': 'multi_rubber_duck_eval_agent',
        'method': 'multi_rubber_duck_eval',
        'args': {
            'model_type': 'Qwen/Qwen2.5-72B-Instruct',
            'eval_folder': 'workspace/benchmark_evaluation'
        },
        'input': {'data': 'workspace/benchmark_evaluation/bench_final_annotation_with_multi_errors_v2.jsonl'},
        'data_ids': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310],
        'output': 'multi_rubber_duck_eval_result',
        'output_type': 'analysis'
    },
]
