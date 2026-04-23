import os
import base64
import re

from mimetypes import guess_type
from .prompt import (
    SYSTEM_PROMPT,
    USER_PROMPT,
    CAPIMAGINE_SYSTEM_PROMPT,
    CAPIMAGINE_USER_PROMPT,
    CAP_FULL_SYSTEM_PROMPT,
    CAP_FULL_USER_PROMPT,
    CAP_NO_IMAGINATION_SYSTEM_PROMPT,
    CAP_NO_IMAGINATION_USER_PROMPT,
    CAP_NO_ROOT_CAUSE_SYSTEM_PROMPT,
    CAP_NO_ROOT_CAUSE_USER_PROMPT,
    CAP_NO_REVISION_CHECKLIST_SYSTEM_PROMPT,
    CAP_NO_REVISION_CHECKLIST_USER_PROMPT,
    CAP_NO_PRESERVE_CORRECT_PARTS_SYSTEM_PROMPT,
    CAP_NO_PRESERVE_CORRECT_PARTS_USER_PROMPT,
)
from agents.openai_chatComplete import completion_for_4v
from agents.utils import fill_in_placeholders
from agents.generic_agent import GenericAgent

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def local_image_to_data_url(image_path):
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{base64_encoded_data}"


def get_code(response):

    all_python_code_blocks_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```', re.MULTILINE)


    all_code_blocks = all_python_code_blocks_pattern.findall(response)
    all_code_blocks_combined = '\n'.join(all_code_blocks)
    return all_code_blocks_combined


class VisualRefineAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.plot_file = kwargs.get('plot_file', '')
        self.code = kwargs.get('code', '')
        self.query = kwargs.get('query', '')
        self.prompt_variant = kwargs.get('prompt_variant', 'default')

    def _get_prompts(self):
        prompt_map = {
            'default': (SYSTEM_PROMPT, USER_PROMPT),
            'capimagine': (CAPIMAGINE_SYSTEM_PROMPT, CAPIMAGINE_USER_PROMPT),
            'cap_full': (CAP_FULL_SYSTEM_PROMPT, CAP_FULL_USER_PROMPT),
            'cap_no_imagination': (CAP_NO_IMAGINATION_SYSTEM_PROMPT, CAP_NO_IMAGINATION_USER_PROMPT),
            'cap_no_root_cause': (CAP_NO_ROOT_CAUSE_SYSTEM_PROMPT, CAP_NO_ROOT_CAUSE_USER_PROMPT),
            'cap_no_revision_checklist': (
                CAP_NO_REVISION_CHECKLIST_SYSTEM_PROMPT,
                CAP_NO_REVISION_CHECKLIST_USER_PROMPT,
            ),
            'cap_no_preserve_correct_parts': (
                CAP_NO_PRESERVE_CORRECT_PARTS_SYSTEM_PROMPT,
                CAP_NO_PRESERVE_CORRECT_PARTS_USER_PROMPT,
            ),
        }
        if self.prompt_variant not in prompt_map:
            raise ValueError(f"Unsupported prompt variant: {self.prompt_variant}")
        return prompt_map[self.prompt_variant]

    def run(self, model_type, query_type, file_name):
        plot = os.path.join(self.workspace['workspace'], self.plot_file)

        print(f"Plot directory: {plot}\n")
        chen_img_url = local_image_to_data_url(f"{plot}")

        information = {
            'query': self.query,
            'file_name': file_name,
            'code': self.code
        }
        system_prompt, user_prompt = self._get_prompts()

        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(system_prompt, information)})
        messages.append({"role": "user",
                        "content": [{"type": "text", "text": fill_in_placeholders(user_prompt, information)},
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        # "url": f"data:image/jpeg;base64,{base64_image1}"
                                        "url": chen_img_url
                                    }
                                    },
                                    ]
                        })
        visual_feedback = completion_for_4v(messages, model_type)

        return visual_feedback