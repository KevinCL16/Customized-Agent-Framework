import logging
import traceback

import openai
from agents.config.openai import get_api_config, global_temperature
from models.model_config import MODEL_CONFIG


def print_chat_message(messages):
    for message in messages:
        logging.info(f"{message['role']}: {message['content']}")


def completion_with_backoff(messages, model_type, backend='OpenRouter', temperature=0.0):

    if model_type in MODEL_CONFIG.keys():

        port = MODEL_CONFIG[model_type]['port']
        model_full_path= MODEL_CONFIG[model_type]['model']
        
        openai_api_key = "EMPTY"
        openai_api_base = f"http://localhost:{port}/v1"

        client = openai.OpenAI(

            api_key=openai_api_key,
            base_url=openai_api_base,
        )
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(

                    model=model_full_path,
                    messages=messages,
                    temperature=temperature,
                    timeout=30*60,
                    max_tokens=4096,
                    
                )
                result = response.choices[0].message
                answer = result.content
                if answer:  # 如果answer不为空，直接返回
                    return answer
                # 如果answer为空且不是最后一次尝试，继续下一次循环
                if attempt < max_attempts - 1:
                    print("API CALL Empty response received. Retrying...")
                    continue
            except KeyError:

                return None
            except openai.BadRequestError as e:

                return e
        
        # 如果所有尝试都失败，返回None
        return None

    else:
        api_config = get_api_config(model_type)
        client = openai.OpenAI(
            api_key=api_config["api_key"],
            base_url=api_config["base_url"],
        )

        try:
            response = client.chat.completions.create(
            model=model_type,
            messages=messages,
            temperature=temperature,
        )
            result = response.choices[0].message
            answer = result.content
            return answer

        # except TypeError as e:
        #     print(e)
        #     return e

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return e


def completion_with_log(messages, model_type, enable_log=False):
    if enable_log:
        logging.info('========CHAT HISTORY========')
        print_chat_message(messages)
    response = completion_with_backoff(messages, model_type)
    if enable_log:
        logging.info('========RESPONSE========')
        logging.info(response)
        logging.info('========RESPONSE END========')
    return response


def completion_for_4v(messages, model_type):
    api_config = get_api_config(model_type)
    client = openai.OpenAI(
        api_key=api_config["api_key"],
        base_url=api_config["base_url"],
    )

    response = client.chat.completions.create(
        model=model_type,
        messages=messages,
        temperature=global_temperature,
        # max_tokens=2000
    )

    result = response.choices[0].message
    answer = result.content
    return answer
