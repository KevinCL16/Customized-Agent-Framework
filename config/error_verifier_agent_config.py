from agents.error_verifier_agent.prompt import RUBBER_DUCK_EVAL_SYSTEM_PROMPT, RUBBER_DUCK_EVAL_USER_PROMPT, RUBBER_DUCK_EVAL_PROMPT
from agents.error_verifier_agent.agent import ErrorVerifierAgent


AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'rubber_duck_eval_agent',
            'class': ErrorVerifierAgent,
            'prompts': {
                'system': RUBBER_DUCK_EVAL_SYSTEM_PROMPT,
                'user': RUBBER_DUCK_EVAL_USER_PROMPT,
                'eval': RUBBER_DUCK_EVAL_PROMPT
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
        'agent': 'rubber_duck_eval_agent',
        'method': 'rubber_duck_eval',
        'args': {
            'model_type': 'gpt-4o',
            'eval_folder': 'workspace/InfiAgent/sklearn_pandas_errors'
        },
        'input': {'data': 'workspace/InfiAgent/sklearn_pandas_errors/final_llama-3.1-8b_direct_generate_dabench_hard_annotation.jsonl'},
        'data_range': [23, 743],
        'output': 'rubber_duck_eval_result',
        'output_type': 'analysis'
    },
]

# [144, 178, 550]