import re
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders

class CorrectnessEnsuringAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)

    def run(self, queries, model_type, file_name, data_analysis_output):
        log = []
        verified_results = []
        data_analysis_output = data_analysis_output[0]

        query = queries  # Since we're now passing a single query

        log.append(f"\n--- Verifying Query ---")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")

        code = data_analysis_output['result']
        execution_log = data_analysis_output['log']

        log.append("Generated code:")
        log.append(code)
        log.append("Execution log:")
        log.append(execution_log)

        # Check correctness
        is_correct, feedback = self.check_correctness(execution_log, query['answers'])

        if is_correct:
            log.append("Correct answer obtained.")
            verified_results.append({'execution_log': execution_log, 'code': code})
        else:
            error_message = f"Incorrect Answer: Answer verification failed. Feedback: {feedback}"
            log.append(error_message)
            verified_results.append({'error_message': error_message, 'code': code})

        return log, verified_results

    def debug_run(self, queries, model_type, file_name, error_message, buggy_code):
        log = []
        debug_code = ""

        query = queries  # Since we're now passing a single query

        log.append(f"\n--- Debugging Query ---")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")

        log.append("Error message:")
        log.append(error_message)

        log.append("Buggy code:")
        log.append(buggy_code)

        # Generate feedback for debugging
        feedback_prompt = self.generate_feedback_prompt(query, error_message, buggy_code)
        result = self.generate(feedback_prompt, model_type=model_type, file_name=file_name)
        debug_code = self.get_code(result)

        log.append("Debug suggestions:")
        log.append(result)

        log.append("Corrected code:")
        log.append(debug_code)

        return log, debug_code

    def check_correctness(self, execution_log, expected_answers):
        matched_answers = self.match_answers(execution_log, expected_answers)
        all_correct = all(correct for _, correct, _ in matched_answers)
        feedback = self.generate_feedback(matched_answers)
        return all_correct, feedback

    def match_answers(self, execution_log, expected_answers):
        # Split the log into lines
        log_lines = execution_log.split('\n')
        
        matched_answers = []
        for key, expected_value in expected_answers:
            found = False
            for line in reversed(log_lines):
                # 修改匹配模式，以适应更多格式，包括方括号内的值
                pattern = rf'{re.escape(key)}.*?[:\[]?\s*([^\s\]\)]+)'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    generated_value = match.group(1).strip()
                    if float(generated_value) == float(expected_value):
                        matched_answers.append((key, True, generated_value))
                    else:
                        matched_answers.append((key, False, generated_value))
                    found = True
                    break
            if not found:
                matched_answers.append((key, False, None))
        
        return matched_answers

    def generate_feedback(self, matched_answers):
        feedback = []
        for key, is_correct, generated_value in matched_answers:
            if is_correct:
                feedback.append(f"Correct: {key}")
            else:
                if generated_value is None:
                    feedback.append(f"Missing: {key}")
                else:
                    feedback.append(f"Incorrect: {key}. Generated: {generated_value}")
        return "; ".join(feedback)

    def generate_feedback_prompt(self, query, error_message, buggy_code):
        prompt = f"""Question ID: {query['id']}
Question: {query['question']}
                
Constraints: {query['constraints']}

Data File Name: {query['file_name']}
                
Format: {query['format']}

Expected Answers: {query['answers']}

Buggy code:
{buggy_code}

Error message:
{error_message}

Please analyze the buggy code and the error message, and provide suggestions to fix the code.
Ensure that the corrected code adheres to the question constraints and produces output in the specified format.
Make sure the code generates the expected answers.
"""
        return prompt

    def generate(self, user_prompt, model_type, file_name):
        workspace_structure = self.get_workspace_structure()
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
            'query': user_prompt
        }

        messages = [
            {"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)},
            {"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)}
        ]

        return completion_with_backoff(messages, model_type)

    def get_code(self, response):
        code_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```')
        matches = code_pattern.findall(response)
        return '\n'.join(matches) if matches else ''

    def get_workspace_structure(self):
        # Implement this method to return the workspace structure
        pass
