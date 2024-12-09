from agents.error_verifier_agent.prompt import ERROR_EVAL_SYSTEM_PROMPT, ERROR_EVAL_USER_PROMPT, EVAL_PROMPT
from agents.error_verifier_agent.agent import ErrorVerifierAgent


AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'error_eval_agent',
            'class': ErrorVerifierAgent,
            'prompts': {
                'system': ERROR_EVAL_SYSTEM_PROMPT,
                'user': ERROR_EVAL_USER_PROMPT,
                'eval': EVAL_PROMPT
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
        'agent': 'error_eval_agent',
        'method': 'eval',
        'args': {
            'model_type': 'gpt-4o-mini',
            'eval_folder': 'workspace/InfiAgent/error_code'
        },
        'input': {'data': 'workspace/InfiAgent/error_code/hard_method_level_wrong.jsonl'},
        'data_range': [23, 743],
        'output': 'error_eval_result',
        'output_type': 'analysis'
    },
]

# [144, 178, 550]