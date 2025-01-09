import json

# Read JSONL file
with open('gpt-4o_rubber_duck_eval_on_weak_llm_result.jsonl', 'r') as file:
    records = [json.loads(line) for line in file]

# Initialize total scores and max scores
total_error_line_score = 0
total_error_message_score = 0
max_error_line_score = 0
max_error_message_score = 0

# Calculate scores
for record in records:
    for eval_result in record["eval_result"]:
        total_error_line_score += eval_result["error_line_score"]
        total_error_message_score += eval_result["error_message_score"]
        max_error_line_score += 1  # Each eval_result has a max error_line_score of 1
        max_error_message_score += 1  # Each eval_result has a max error_message_score of 1

# Calculate the percentage scores
error_line_percentage = (total_error_line_score / max_error_line_score) * 100
error_message_percentage = (total_error_message_score / max_error_message_score) * 100

# Print the overall scores
print(f"Total error number: {max_error_line_score}")
print(f"Overall Error Line Score: {error_line_percentage:.2f}%")
print(f"Overall Error Message Score: {error_message_percentage:.2f}%")
