# -*- coding: utf-8 -*-
import json


def filter_error_versions(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # 解析每一行的 JSON 数据
            data = json.loads(line)

            # 筛选出 error_versions 中 execution_output 包含 "Traceback (most recent call last):" 的部分
            filtered_error_versions = [
                error_version for error_version in data.get('error_versions', [])
                if "Traceback (most recent call last):" in error_version.get('execution_output', '')
            ]

            # 如果有满足条件的 error_versions，保存到新的 JSON
            if filtered_error_versions:
                # 保持其他数据不变，只替换 error_versions
                data['error_versions'] = filtered_error_versions
                # 写入到输出文件
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')


# 输入和输出文件路径
input_file = 'monitored_errors.jsonl'  # 原始 JSONL 文件
output_file = 'filtered_monitored_errors.jsonl'  # 筛选后的 JSONL 文件

# 执行筛选
filter_error_versions(input_file, output_file)
