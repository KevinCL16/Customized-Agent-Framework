from agents.error_suggest_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT
from agents.error_suggest_agent.agent import ErrorSuggestAgent


AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'error_suggest_agent',
            'class': ErrorSuggestAgent,
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
        'agent': 'error_suggest_agent',
        'method': 'run',
        'args': {
            'model_type': 'gpt-4o',
        },
        'input': {'data': 'InfiAgent_data/hard_modified_da-dev-questions.jsonl',
                  'code': 'code_action_data_analysis_agent_run.py'},
        'data_ids': [125, 133, 144, 177, 178, 210, 220, 224, 249, 271, 273, 275, 282, 308, 310, 376, 413, 415],  # Specify the question IDs you want to process
        'output': 'error_suggest_result',
        'output_type': 'analysis'  # Specify the output type here
    },
]

# [7, 28, 30, 39, 70, 77, 109, 111, 118, 124, 125, 133, 144, 177, 178, 210, 220, 224, 249, 271, 273, 275, 282, 308, 310, 376, 413, 415]