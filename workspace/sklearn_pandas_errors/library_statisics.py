import openai
import json
from collections import Counter
import pandas as pd
import re
import os
# 设置 OpenAI API 密钥
from tqdm import tqdm

openai.api_key = ""  # 替换为您的 OpenAI API 密钥
openai.base_url = ''


def extract_traceback(error_str):
    """
    从错误信息字符串中提取 'Traceback (most recent call last):' 及其之后的报错信息。
    """
    pattern = r"Traceback \(most recent call last\):.*"
    match = re.search(pattern, error_str, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return None


def evaluate_annotation_quality(annotation):
    """调用 LLM 评估注释质量，返回评分、建议和原始响应"""
    prompt = f"""
    You are an expert in software debugging and data quality assessment. Your task is to evaluate the quality of data annotations related to code errors. Each annotation consists of the following elements:

Question: A description of the task or problem the code attempts to solve.

Code with Bug: The actual code containing an error.

Cause Error Line: The specific line in the "Code with Bug" where the error originates.

Effect Error Line: The line where the error manifests its observable effect (this can be the same as the "Cause Error Line").

Execution Output: The actual output of running the "Code with Bug", which demonstrates the error.

Your goal is to identify any glaring inconsistencies or obvious errors in these annotations. Specifically, consider the following:

Logic Consistency: Does the "Cause Error Line" logically lead to the "Execution Output"? Is the bug described consistent with the given code and output?

Line Number Accuracy: Are the code lines for "Cause Error Line" and "Effect Error Line" correct and within the content of the "Code with Bug"?

Output Relevance: Does the "Execution Output" clearly demonstrate the presence and impact of the bug?

Input Data:

Question: 
{annotation['question']}

Code with Bug:
{annotation['code_with_bug']}

Cause Error Line: {annotation['cause_error_line']}
Effect Error Line: {annotation['effect_error_line']}

Execution Output: 
{annotation['execution_output']}

## Instructions:

After evaluating the annotation, provide a score and suggestions. Respond in the format:

Score (1-10): [Number]
Suggestions: [Text]

Where:

The score should be between 1 and 10, with 1 being the worst and 10 being the best.

Suggestions should provide specific feedback on any identified problems and include recommendations for improvement.
    """

    message = [
        {"role": "system", "content": ""},
        {"role": "user", "content": prompt}
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=message,
        )
        full_response = response.choices[0].message.content

        # 更稳健的解析方式（使用正则表达式）
        score_match = re.search(r'Score (1-10):\s*(\d+)', full_response)
        suggestion_match = re.search(r'Suggestions:\s*(.+?)(?=\n|$)', full_response, re.DOTALL)

        score = int(score_match.group(1)) if score_match else None
        suggestion = suggestion_match.group(1).strip() if suggestion_match else "无建议"

        return {
            "quality_score": score,
            "improvement_suggestion": suggestion,
            "full_evaluation": full_response  # 保留原始响应以防解析失败
        }

    except Exception as e:
        print(f"API调用失败: {str(e)}")
        return {
            "quality_score": None,
            "improvement_suggestion": "评估失败",
            "full_evaluation": str(e)
        }


# 使用 OpenAI GPT 分析每段代码的库使用情况
def analyze_libraries_with_openai(code_snippet):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # 可以选择更高版本的模型
            messages=[
                {"role": "system", "content": "You are a Python expert."},
                {"role": "user", "content": f"Given the following Python code:\n{code_snippet}\n"
                                             f"Determine which data science libraries (e.g., pandas, numpy, sklearn, matplotlib) "
                                             f"are being used in this code snippet. Return only the name of the used library, e.g., pandas/numpy/sklearn/matplotlib. If you cannot determine which library was used, output your best guess, do not output anything except the above libraries."}
            ]
        )
        # 提取生成的结果
        libraries = response.choices[0].message.content
        print("\nsuccess api call\n")
        return libraries.strip().split(", ")
    except Exception as e:
        print(f"Error analyzing code snippet: {e}")
        return []


def find_low_scoring_annotations(file_path):
    """
    Reads a JSON file containing data annotations, evaluates the scores, and
    returns a list of annotation ids and error_version_ids with scores <= 5.

    Args:
        file_path (str): The path to the JSON file containing annotations.

    Returns:
        list: A list of dictionaries, each containing "id" and "error_version_id"
              for annotations with scores less or equal to 5.
    """
    low_scoring_annotations = []

    if not os.path.exists(file_path):
        print(f"Error: File not found at path '{file_path}'.")
        return low_scoring_annotations

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            annotations = json.load(f)
    except json.JSONDecodeError:
        print(
            f"Error: Could not decode JSON from file '{file_path}'. Please make sure that the file has a correct JSON format.")
        return low_scoring_annotations
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return low_scoring_annotations

    for annotation in annotations:
        for error_version in annotation:
            try:
                full_evaluation = error_version.get('full_evaluation', '')
                if not full_evaluation:
                    print(
                        f"Warning: 'full_evaluation' field missing for annotation id: {error_version.get('id', 'N/A')}, error_version_id: {error_version.get('error_version_id', 'N/A')}")
                    continue

                score_line = next(
                    (line for line in full_evaluation.splitlines() if line.strip().startswith("Score (1-10):")), None)

                if score_line:
                    score = int(score_line.split(":")[-1].strip())
                    if score <= 5:
                        low_scoring_annotations.append({
                            "id": error_version.get("id"),
                            "error_version_id": error_version.get("error_version_id"),
                            "score": score
                        })
            except Exception as e:
                print(
                    f"Warning: Error processing annotation with id: {error_version.get('id', 'N/A')}, error_version_id: {error_version.get('error_version_id', 'N/A')}. Error: {e}")

    return low_scoring_annotations


def library_statistics():
    # 读取 JSONL 文件
    file_path = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\benchmark_evaluation\bench_final_annotation_v4.jsonl"  # 替换为您的文件路径
    with open(file_path, 'r') as file:
        data = [json.loads(line) for line in file]

    # 提取 cause_error_line 字段
    cause_error_lines = []
    for item in data:
        if 'error_versions' in item:
            for version in item['error_versions']:
                if 'cause_error_line' in version:
                    cause_error_lines.append(version['cause_error_line'])

    '''for line in cause_error_lines:
        print(line + '\n')'''

    # 分析每段代码
    library_usage_counter = Counter()
    for line in tqdm(cause_error_lines):
        if line != "main()":
            libraries = analyze_libraries_with_openai(line)
            library_usage_counter.update(libraries)
        else:
            library_usage_counter.update("undetermined")

    # 转换为 DataFrame 格式并保存
    library_usage_df = pd.DataFrame(library_usage_counter.items(), columns=["Library", "Usage"])
    output_path = "library_usage_statistics.csv"
    library_usage_df.to_csv(output_path, index=False)

    # 输出统计结果
    print(f"Library usage statistics saved to {output_path}")


def annotation_quality_check():
    # 读取 JSONL 文件
    file_path = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\InfiAgent\sklearn_pandas_errors\bench_final_annotation_v2.jsonl"
    output_path = r"annotation_check_results.jsonl"
    with open(file_path, 'r') as file:
        data = [json.loads(line) for line in file]

    # 提取 annotation
    for item in tqdm(data):
        error_versions = item['error_versions']
        question = item['question']
        evaluation_results = []
        for idx, error_version in enumerate(tqdm(error_versions)):
            modified_code = error_version['modified_code']
            error_message = extract_traceback(error_version['execution_output'])
            if error_message is not None:
                annotation = {
                    "question": question,
                    "code_with_bug": modified_code,
                    "cause_error_line": error_version["cause_error_line"],
                    "effect_error_line": error_version["effect_error_line"],
                    "execution_output": error_message
                }
                # 分析每条数据
                evaluation = evaluate_annotation_quality(annotation)
                # 将评估结果存储到新字典中
                evaluation_result = {
                    "id": item['id'],
                    "error_version_id": idx,
                    "full_evaluation": evaluation["full_evaluation"]
                }

                # 添加到结果列表
                evaluation_results.append(evaluation_result)

        # 保存评估结果到新的 JSONL 文件
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(evaluation_results, ensure_ascii=False, indent=4) + '\n')

    print(f"评估完成！结果已保存至: {output_path}")


if __name__ == "__main__":
    '''file_path = 'annotation_check_results.jsonl'  # Replace with the path to your annotations file
    low_scores = find_low_scoring_annotations(file_path)

    if low_scores:
        print("Annotations with scores <= 5:")
        print(f"Number of low quality data: {len(low_scores)}")
        for annotation in low_scores:
            print(annotation)
    else:
        print("No annotations found with scores <= 5.")'''

    library_statistics()