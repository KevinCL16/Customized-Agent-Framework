import os
import base64
import pdb
import re

from mimetypes import guess_type
from .prompt import SYSTEM_PROMPT, USER_PROMPT, ERROR_PROMPT
from agents.openai_chatComplete import  completion_for_4v
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

    def run(self, model_type, query_type, file_name):
        plot = os.path.join(self.workspace['workspace'], self.plot_file)

        print(f"Plot directory: {plot}\n")
        # pdb.set_trace()
        base64_image1 = encode_image(f"{plot}")
        chen_img_url = local_image_to_data_url(f"{plot}")

        information = {
            'query': self.query,
            'file_name': file_name,
            'code': self.code
        }

        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(SYSTEM_PROMPT, information)})
        messages.append({"role": "user",
                        "content": [{"type": "text", "text": fill_in_placeholders(USER_PROMPT, information)},
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        # "url": f"data:image/jpeg;base64,{base64_image1}"
                                        "url": chen_img_url
                                    }
                                    },
                                    ]
                        })
        visual_feedback = completion_for_4v(messages, 'gpt-4o')

        return visual_feedback