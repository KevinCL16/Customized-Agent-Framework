from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_log
from agents.utils import fill_in_placeholders
from agents.query_expansion_agent.prompt import SYSTEM_PROMPT, EXPERT_USER_PROMPT

class QueryExpansionAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.model_type = kwargs.get('model_type', 'gpt-4o')

    def run(self, instruction, **kwargs):
        expanded_queries = []

        information = {
            'query': instruction,
        }

        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(SYSTEM_PROMPT, information)})
        messages.append({"role": "user", "content": fill_in_placeholders(EXPERT_USER_PROMPT, information)})
        expanded_query_instruction = completion_with_log(messages, self.model_type)
        expanded_queries.append(expanded_query_instruction)

        return expanded_queries
