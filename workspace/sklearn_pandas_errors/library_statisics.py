import openai
import json
from collections import Counter
import pandas as pd

# 设置 OpenAI API 密钥
from tqdm import tqdm

openai.api_key = ""  # 替换为您的 OpenAI API 密钥
openai.base_url = ''

# 读取 JSONL 文件
file_path = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\InfiAgent\sklearn_pandas_errors\bench_final_annotation_v1.jsonl"  # 替换为您的文件路径
with open(file_path, 'r') as file:
    data = [json.loads(line) for line in file]

# 提取 cause_error_line 字段
cause_error_lines = []
for item in data:
    if 'error_versions' in item:
        for version in item['error_versions']:
            if 'cause_error_line' in version:
                cause_error_lines.append(version['cause_error_line'])

# 使用 OpenAI GPT 分析每段代码的库使用情况
def analyze_libraries_with_openai(code_snippet):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # 可以选择更高版本的模型
            messages=[
                {"role": "system", "content": "You are a Python expert."},
                {"role": "user", "content": f"Given the following Python code:\n{code_snippet}\n"
                                             f"Determine which data science libraries (e.g., pandas, numpy, sklearn, matplotlib) "
                                             f"are being used in this code snippet. Return only the name of the used library, e.g., pandas/numpy/sklearn/matplotlib ."}
            ]
        )
        # 提取生成的结果
        libraries = response.choices[0].message.content
        print("\nsuccess api call\n")
        return libraries.strip().split(", ")
    except Exception as e:
        print(f"Error analyzing code snippet: {e}")
        return []

# 分析每段代码
library_usage_counter = Counter()
for line in tqdm(cause_error_lines):
    libraries = analyze_libraries_with_openai(line)
    library_usage_counter.update(libraries)

# 转换为 DataFrame 格式并保存
library_usage_df = pd.DataFrame(library_usage_counter.items(), columns=["Library", "Usage"])
output_path = "library_usage_statistics.csv"
library_usage_df.to_csv(output_path, index=False)

# 输出统计结果
print(f"Library usage statistics saved to {output_path}")
