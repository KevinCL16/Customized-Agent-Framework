from agents.plot_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, VIS_SYSTEM_PROMPT, VIS_USER_PROMPT, ERROR_PROMPT
from agents.query_expansion_agent.prompt import SYSTEM_PROMPT, EXPERT_USER_PROMPT

AGENT_CONFIG = {
    'workspace': './workspace',
    'agents': [
        {
            'name': 'query_expansion_agent',
            'prompts': {
                'system': SYSTEM_PROMPT,
                'user': EXPERT_USER_PROMPT
            },
            'kwargs': {
                'model_type': 'gpt-4o'
            }
        },
        {
            'name': 'plot_agent',
            'prompts': {
                'initial': {
                    'system': INITIAL_SYSTEM_PROMPT,
                    'user': INITIAL_USER_PROMPT
                },
                'vis_refined': {
                    'system': VIS_SYSTEM_PROMPT,
                    'user': VIS_USER_PROMPT
                },
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
        'agent': 'query_expansion_agent',
        'method': 'run',
        'args': {'model_type': 'gpt-4o'},
        'input': {'data': 'benchmark_data/benchmark_instructions.json'},
        'data_ids': [1],  # Specify individual data ids
        # 'data_range': (1, 10),  # Specify a range of data ids (uncomment to use)
        'output': 'expanded_query'
    },
    {
        'agent': 'plot_agent',
        'method': 'run',
        'args': {
            'query': {'from': 'expanded_query'},
            'model_type': 'gpt-4o',
            'query_type': 'initial',
            'file_name': 'plot.png'
        },
        'output': 'plot_result'
    },
    # Add more workflow steps here
]