from agents.plot_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT
from agents.data_analysis_agent.agent import DataAnalysisAgent
from agents.correctness_ensuring_agent.agent import CorrectnessEnsuringAgent

AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'data_analysis_agent',
            'class': DataAnalysisAgent,
            'prompts': {
                'system': INITIAL_SYSTEM_PROMPT,
                'user': INITIAL_USER_PROMPT,
                'error': ERROR_PROMPT
            },
            'kwargs': {
                'query': 'Your default query here'
            }
        },
        {
            'name': 'correctness_ensuring_agent',
            'class': CorrectnessEnsuringAgent,
            'prompts': {
                'system': INITIAL_SYSTEM_PROMPT,
                'user': INITIAL_USER_PROMPT,
                'error': ERROR_PROMPT
            }
        },
    ]
}

#
WORKFLOW = [
    {
        'agent': 'data_analysis_agent',
        'method': 'run',
        'args': {
            'model_type': 'claude-3-5-sonnet-20240620',
            'file_name': 'plot.png'
        },
        'input': {'data': 'InfiAgent_data/hard_modified_da-dev-questions.jsonl'},
        'data_ids': [23],  # Specify the question IDs you want to process
        'output': 'data_analysis_result',
        'output_type': 'code'  # Specify the output type here
    },
    {
        'agent': 'correctness_ensuring_agent',
        'method': 'run',
        'args': {
            'model_type': 'claude-3-5-sonnet-20240620',
            'file_name': 'plot.png',
            'data_analysis_output': {'from': 'data_analysis_result'}
        },
        'input': {'data': 'InfiAgent_data/hard_modified_da-dev-questions.jsonl'},
        'data_ids': [23],  # Specify the question IDs you want to process
        'output': 'verification_result',
        'output_type': 'analysis'  # Specify the output type here
    },
]