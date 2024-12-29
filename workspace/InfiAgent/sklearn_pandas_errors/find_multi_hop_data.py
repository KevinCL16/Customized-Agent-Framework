import json
import re


def extract_error_lines(execution_output):
    """
    从 execution_output 中提取每个 '!!!' 标记对应的最近的代码行。
    避免重复提取同一报错对应的代码行。
    """
    error_lines = []
    lines = execution_output.splitlines()
    skip_next = False  # 标志变量，表示是否跳过重复的 '!!!'

    for i, line in enumerate(lines):
        if "!!!" in line:  # 三个感叹号标记
            if skip_next:  # 如果标志为 True，跳过当前 '!!!'
                continue
            # 从最近的代码行开始向上查找，以提取报错行代码
            for j in range(i - 1, -1, -1):
                if "|" in lines[j]:  # 查找带有代码的行
                    error_code_line = lines[j].split("|", 1)[1].strip()  # 提取代码内容
                    if error_code_line not in error_lines:  # 避免重复添加
                        error_lines.append(error_code_line)
                    break
            skip_next = True  # 设置标志变量为 True，跳过后续的 '!!!'
        else:
            skip_next = False  # 如果当前行没有 '!!!'，重置标志变量为 False

    return error_lines


def compare_error_and_modified_line(jsonl_file_path, output_file_path):
    """
    遍历 JSONL 文件，检查 execution_output 中的报错行是否和 modified_line 一致。
    """
    with open(jsonl_file_path, "r", encoding="utf-8") as file:
        entries = []
        consistent_count = 0
        inconsistent_count = 0
        for line in file:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON 解码错误: {e}")
                continue

            error_versions = entry.get("error_versions", [])
            for error_version in error_versions:
                execution_output = error_version.get("execution_output", "")
                modified_line = error_version.get("modified_line", "")

                # 提取 execution_output 中的报错行代码
                error_line_list = extract_error_lines(execution_output)
                error_line = error_line_list[-1]

                # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                error_version["effect_error_line"] = error_line
                error_version["cause_error_line"] = modified_line

                if error_line:
                    # 比较报错行与 modified_code
                    if error_line.strip() == modified_line.strip():
                        print("报错行和修改行一致")
                        consistent_count += 1
                    else:
                        print("报错行和修改行不一致")
                        print(f"报错行代码: {error_line}")
                        print(f"修改代码: {modified_line}")
                        inconsistent_count += 1
                else:
                    print("未找到报错行代码")

            # 修改后的 entry 保留在原位置
            entries.append(entry)

        print(f"\n报错行和修改行一致有：{consistent_count} 条\n报错行和修改行不一致有：{inconsistent_count} 条")

        # 将修改后的数据写回到新的 JSONL 文件
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            for entry in entries:
                output_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_cause_and_effect_error_lines_for_weak_analysis(jsonl_file_path, output_file_path):
    """
    遍历 JSONL 文件，检查 execution_output 中的报错行，并在每个 error_version 中新增 cause_error_line 和 effect_error_line。
    """
    with open(jsonl_file_path, "r", encoding="utf-8") as file:
        entries = []
        count = 0
        consistent_count = 0
        inconsistent_count = 0

        for line in file:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON 解码错误: {e}")
                continue

            error_versions = entry.get("error_versions", [])
            for error_version in error_versions:
                execution_output = error_version.get("execution_output", "")

                # 提取 execution_output 中的报错行代码
                error_line_list = extract_error_lines(execution_output)

                if len(error_line_list) >= 2:
                    effect_error_line = error_line_list[-1]
                    cause_error_line = error_line_list[-2]

                    # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                    error_version["effect_error_line"] = effect_error_line
                    error_version["cause_error_line"] = cause_error_line

                    # 比较报错行与修改行
                    if effect_error_line.strip() == cause_error_line.strip():
                        print("报错行和修改行一致")
                        consistent_count += 1
                    else:
                        print("报错行和修改行不一致")
                        print(f"报错行代码: {effect_error_line}")
                        print(f"修改代码: {cause_error_line}")
                        inconsistent_count += 1
                else:
                    effect_error_line = error_line_list[-1]
                    cause_error_line = error_line_list[-1]

                    # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                    error_version["effect_error_line"] = effect_error_line
                    error_version["cause_error_line"] = cause_error_line
                    print("未找到足够的报错行代码")

            # 修改后的 entry 保留在原位置
            entries.append(entry)

    # 输出统计结果
    print(f"\n报错行和修改行一致有：{consistent_count} 条\n报错行和修改行不一致有：{inconsistent_count} 条")

    # 将修改后的数据写回到新的 JSONL 文件
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        for entry in entries:
            output_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

# 测试函数，传入包含 JSONL 数据的文件路径
jsonl_file_path = "filtered_llama-3.1-8b-instant_monitored_errors.jsonl"  # 替换为您的 JSONL 文件路径
jsonl_output_path = "test.jsonl"
find_cause_and_effect_error_lines_for_weak_analysis(jsonl_file_path, jsonl_output_path)
