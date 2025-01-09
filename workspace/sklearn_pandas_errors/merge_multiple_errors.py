import json
import random


def restore_original_code(modified_code, error_versions):
    """
    Restore the initial error-free code by replacing modified lines with original lines,
    handling missing or empty values.
    """
    lines = modified_code.split("\n")
    for error in error_versions:
        original_line = error.get("original_line", "").strip()
        modified_line = error.get("modified_line", "").strip()
        if original_line and modified_line:
            # Replace modified lines with original lines
            lines = [original_line if line.strip() == modified_line else line for line in lines]
    return "\n".join(lines)


def merge_errors(data_entry):
    """
    Merge multiple errors into one modified_code by randomly selecting some errors from error_versions.
    Handle missing values gracefully and ensure at least two errors are present for merging.
    """
    error_versions = data_entry.get("error_versions", [])
    if len(error_versions) < 2:
        return None  # Skip entries with less than 2 errors

    modified_code = error_versions[0]["modified_code"]  # Take the first version's code as the base

    # Step 1: Restore the original error-free code
    original_code = restore_original_code(modified_code, error_versions)

    # Step 2: Randomly select a few errors to introduce
    num_errors_to_merge = random.randint(2, min(5, len(error_versions)))
    selected_errors = random.sample(error_versions, num_errors_to_merge)

    # Step 3: Apply the selected errors to the original code
    merged_code_lines = original_code.split("\n")
    for error in selected_errors:
        original_line = error.get("original_line", "").strip()
        modified_line = error.get("modified_line", "").strip()
        if original_line and modified_line:
            # Replace the original line with the modified line
            merged_code_lines = [modified_line if line.strip() == original_line else line for line in merged_code_lines]

    # Step 4: Merge other information
    combined_error_info = {
        "merged_code": "\n".join(merged_code_lines),
        "error_count": num_errors_to_merge,
        "merged_errors": [error.get("error_type", "unknown") for error in selected_errors],
        "execution_outputs": [error.get("execution_output", "") for error in selected_errors],
        "effect_error_lines": [error.get("effect_error_line", "") for error in selected_errors],
        "cause_error_lines": [error.get("cause_error_line", "") for error in selected_errors],
        "original_sample_id": data_entry.get("id", "unknown")
    }

    return combined_error_info


def generate_multiple_merged_samples(data_entry, num_samples=4):
    """
    Generate multiple merged error samples from a single data entry.
    """
    merged_samples = []
    for _ in range(num_samples):
        merged_sample = merge_errors(data_entry)
        if merged_sample:
            merged_samples.append(merged_sample)
    return merged_samples


def main(input_file, output_file):
    # Read JSONL data
    with open(input_file, 'r') as file:
        data = [json.loads(line) for line in file]

    # Generate 4 merged error samples for each entry
    all_merged_samples = []
    for entry in data:
        all_merged_samples.extend(generate_multiple_merged_samples(entry, num_samples=4))

    # Save results to a new JSONL file
    with open(output_file, 'w') as file:
        for sample in all_merged_samples:
            file.write(json.dumps(sample) + '\n')

    print(f"Merged samples saved to {output_file}")


if __name__ == "__main__":
    input_file = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\InfiAgent\sklearn_pandas_errors\bench_final_annotation_v1.jsonl"  # 输入文件路径
    output_file = "bench_final_annotation_with_multi_errors_v1.jsonl"  # 输出文件路径
    main(input_file, output_file)
