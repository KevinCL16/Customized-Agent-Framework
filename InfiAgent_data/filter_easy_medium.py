import json

# 文件路径
input_file = "easy_medium_modified_da-dev-questions.jsonl"
output_file = "easy_medium_modified_da-dev-questions.jsonl"

# 打开文件并修改键名
with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        data = json.loads(line.strip())
        if "answer" in data:
            data["answers"] = data.pop("answer")  # 修改键名
        json.dump(data, outfile, ensure_ascii=False)
        outfile.write('\n')

print(f"修改完成，结果保存至 {output_file}")
