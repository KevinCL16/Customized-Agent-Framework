import json

# Read JSONL file
with open('eval_result_v2_prompt.jsonl', 'r') as file:
    records = [json.loads(line) for line in file]

# Calculate score
total_score = 0
for record in records:
    score_str = record["eval_result"].split("[")[-1][:-1]
    score = float(score_str)
    total_score += score

# Calculate the percentage score
max_score = len(records) * 1  # Each record has a max score of 1
percentage_score = (total_score / max_score) * 100

print(f"Overall score: {percentage_score:.2f}%")
