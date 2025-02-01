import json

def add_matplotlib_imports(input_file, output_file):
    """
    Reads a JSONL file, adds 'import matplotlib' and 'matplotlib.use('Agg')'
    to the beginning of the 'modified_code' in each error_versions entry,
    and saves the modified data to a new JSONL file.

    Args:
        input_file (str): Path to the input JSONL file.
        output_file (str): Path to the output JSONL file.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            try:
                data = json.loads(line.strip())
                if 'error_versions' in data and isinstance(data['error_versions'], list):
                    for error_version in data['error_versions']:
                        if 'modified_code' in error_version and isinstance(error_version['modified_code'], str):
                            imports_to_add = "import matplotlib\nmatplotlib.use('Agg')  # Use the 'Agg' backend to avoid GUI issues\n"
                            # 检查是否已存在 (可选)
                            if "import matplotlib" or "matplotlib.use('agg')" not in error_version['modified_code']:
                                modified_code = imports_to_add + error_version['modified_code']
                            else:
                                modified_code = error_version['modified_code']  # 已存在则不添加
                            error_version['modified_code'] = modified_code
                outfile.write(json.dumps(data) + '\n')
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON line: {line.strip()}")
                outfile.write(line) # Write the original line to output if parsing fails

if __name__ == "__main__":
    input_jsonl_file = r'gpt-4o_dabench_hard_library_errors.jsonl'  # Replace with your input file name
    output_jsonl_file = r'gpt-4o_dabench_hard_library_errors_with_use_agg.jsonl' # Replace with your desired output file name
    add_matplotlib_imports(input_jsonl_file, output_jsonl_file)
    print(f"Modified data saved to {output_jsonl_file}")