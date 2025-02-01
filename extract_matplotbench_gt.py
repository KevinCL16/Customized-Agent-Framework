import json
import os
import glob


def process_files():
    # 读取benchmark_instructions.json
    with open('benchmark_data/benchmark_instructions.json', 'r', encoding='utf-8') as f:
        instructions = json.load(f)

    # 获取所有包含gt.py的example文件夹
    gt_codes = {}
    for folder in glob.glob('workspace/example_*'):
        gt_path = os.path.join(folder, 'gt.py')
        if os.path.exists(gt_path):  # 只处理存在gt.py的文件夹
            try:
                # 从文件夹名称中提取id
                example_id = int(folder.split('example_')[1])

                # 读取gt.py文件
                with open(gt_path, 'r', encoding='utf-8') as f:
                    gt_code = f.read()
                gt_codes[example_id] = gt_code
                print(f"成功处理 example_{example_id}")
            except Exception as e:
                print(f"Error processing {folder}: {e}")

    # 将gt代码添加到对应的instruction中
    processed_count = 0
    new_ins_set = []
    for instruction in instructions:
        if 'id' in instruction:
            instruction_id = instruction['id']
            if instruction_id in gt_codes:
                new_dict = {
                    "id": instruction['id'],
                    "question": instruction['simple_instruction'],
                    "correct_analysis_code": gt_codes[instruction_id]
                }
                # instruction['correct_analysis_code'] = gt_codes[instruction_id]
                processed_count += 1
                new_ins_set.append(new_dict)

    # 保存为jsonl文件
    output_path = 'benchmark_data/matplotbench-q-code.jsonl'
    with open(output_path, 'w', encoding='utf-8') as f:
        for instruction in new_ins_set:
            f.write(json.dumps(instruction, ensure_ascii=False) + '\n')

    print(f"\n处理完成:")
    print(f"- 共找到 {len(gt_codes)} 个包含gt.py的example文件夹")
    print(f"- 成功添加了 {processed_count} 个correct_code")
    print(f"- 结果已保存到 {output_path}")


if __name__ == "__main__":
    process_files()