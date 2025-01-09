import json
import glob

# 定义输入的jsonl文件路径模式（比如当前目录下的所有.jsonl文件）
input_files = "bench_final_annotation_v1.jsonl"


def count_errors(files):
    """
    统计多个jsonl文件中所有error_versions的总数。
    """
    total_errors = 0

    with open(files, "r") as f:
        for line in f:
            data = json.loads(line)
            error_versions = data.get("error_versions", [])
            total_errors += len(error_versions)

    return total_errors


def main():
    # 统计错误数量
    total_errors = count_errors(input_files)
    print(f"共有 {total_errors} 个错误版本（error_versions）。")


# 运行脚本
if __name__ == "__main__":
    main()
