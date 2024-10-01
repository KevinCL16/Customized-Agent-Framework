from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_log
from agents.utils import fill_in_placeholders

class QueryExpansionAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.model_type = kwargs.get('model_type', 'gpt-4o')

    def run(self, data, **kwargs):
        expanded_queries = []
        for instruction in data:
            information = {
                'query': instruction['simple_instruction'],
            }

            messages = []
            messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)})
            messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)})
            expanded_query_instruction = completion_with_log(messages, self.model_type)
            expanded_queries.append(expanded_query_instruction)

        return expanded_queries
