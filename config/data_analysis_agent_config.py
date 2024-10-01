from agents.plot_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT

AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'data_analysis_agent',
            'prompts': {
                'system': INITIAL_SYSTEM_PROMPT,
                'user': INITIAL_USER_PROMPT,
                'error': ERROR_PROMPT
            },
            'kwargs': {
                'query': 'Your default query here'
            }
        },
        # Add more agents here
    ]
}

WORKFLOW = [
    {
        'agent': 'data_analysis_agent',
        'method': 'run',
        'args': {
            'model_type': 'gpt-4o',
            'file_name': 'plot.png'
        },
        'input': {'data': 'InfiAgent_data/hard_modified_da-dev-questions.jsonl'},
        'data_ids': [7, 23],  # Specify the question IDs you want to process
        'output': 'analysis_result'
    },
    # Add more workflow steps here
]