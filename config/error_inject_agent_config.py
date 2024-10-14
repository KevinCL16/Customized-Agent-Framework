from agents.error_inject_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT
from agents.error_inject_agent.agent import ErrorInjectAgent


AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'error_inject_agent',
            'class': ErrorInjectAgent,
            'prompts': {
                'system': INITIAL_SYSTEM_PROMPT,
                'user': INITIAL_USER_PROMPT,
                'error': ERROR_PROMPT
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
        'agent': 'error_inject_agent',
        'method': 'run',
        'args': {
            'model_type': 'claude-3-5-sonnet-20240620',
        },
        'input': {'data': 'InfiAgent_data/hard_modified_da-dev-questions.jsonl',
                  'code': 'code_action_data_analysis_agent_run.py'},
        'data_ids': [7, 28],  # Specify the question IDs you want to process
        'output': 'error_injection_result',
        'output_type': 'analysis'  # Specify the output type here
    },
]