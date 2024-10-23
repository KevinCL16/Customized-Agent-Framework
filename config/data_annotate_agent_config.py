from agents.plot_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT
from agents.data_analysis_agent.agent import DataAnalysisAgent
from agents.correctness_ensuring_agent.agent import CorrectnessEnsuringAgent

AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'data_annotate_agent',
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
    ]
}

#
WORKFLOW = [
    {
        'agent': 'data_annotate_agent',
        'method': 'run',
        'args': {
            'model_type': 'Qwen/Qwen2.5-7B-Instruct',
            'file_name': 'plot.png'
        },
        'input': {'data': 'InfiAgent_data/hard_modified_da-dev-questions.jsonl'},
        'data_range': [7, 39],  # Specify the question IDs you want to process
        'output': 'data_analysis_result',
        'output_type': 'code'  # Specify the output type here
    },
]