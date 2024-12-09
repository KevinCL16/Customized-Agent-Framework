import json

# Read JSONL file
with open('gpt-4o-mini_method_eval_result.jsonl', 'r') as file:
    records = [json.loads(line) for line in file]

# Calculate score
total_score = 0
for record in records:
    start_index = record["eval_result"].find('[')
    end_index = record["eval_result"].find(']')
    score_str = record["eval_result"][start_index + 1:end_index]
    score = float(score_str)
    total_score += score

# Calculate the percentage score
max_score = len(records) * 1  # Each record has a max score of 1
percentage_score = (total_score / max_score) * 100

print(f"Overall score: {percentage_score:.2f}%")
