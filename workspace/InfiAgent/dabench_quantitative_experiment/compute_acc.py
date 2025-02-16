import json
import re


def parse_output_string(output_str):
    """
    Parses the output string format and extracts key-value pairs.

    Args:
        output_str: The output string in the format "@key[value]\n@key[value]...".

    Returns:
        A dictionary where keys are the extracted keys and values are the extracted values.
    """
    output_dict = {}
    lines = output_str.strip().split('\n')
    for line in lines:
        match = re.match(r'@(\w+)\[([\d.]+)\]', line)
        if match:
            key = match.group(1)
            value = match.group(2)
            output_dict[key] = value
    return output_dict


def parse_ground_truth_list(ground_truth_list):
    """
    Parses the ground truth list format and extracts key-value pairs.

    Args:
        ground_truth_list: The ground truth list of lists in the format [["key", "value"], ["key", "value"], ...].

    Returns:
        A dictionary where keys are the extracted keys and values are the extracted values.
    """
    gt_dict = {}
    for item in ground_truth_list:
        if len(item) == 2:
            key = item[0]
            value = item[1]
            gt_dict[key] = value
    return gt_dict


def calculate_accuracy(output_str, ground_truth_list, tolerance=1e-6):
    """
    Calculates the accuracy between the output string and the ground truth list.

    Args:
        output_str: The output string.
        ground_truth_list: The ground truth list of lists.
        tolerance: The tolerance for comparing float values (default 1e-6).

    Returns:
        The accuracy as a float between 0 and 1.
    """
    output_dict = parse_output_string(output_str)
    gt_dict = parse_ground_truth_list(ground_truth_list)

    correct_matches = 0
    total_pairs = len(gt_dict)

    if total_pairs == 0:
        return 1.0 if len(output_dict) == 0 else 0.0 # Handle empty GT case

    for key, gt_value in gt_dict.items():
        if key in output_dict:
            output_value = output_dict[key]
            try:
                gt_value_float = float(gt_value)
                output_value_float = float(output_value)
                if abs(gt_value_float - output_value_float) <= tolerance: # Compare as floats with tolerance
                    correct_matches += 1
            except ValueError:
                if gt_value == output_value: # If not float, compare as strings
                    correct_matches += 1

    accuracy = correct_matches / total_pairs if total_pairs > 0 else 0.0
    return accuracy, correct_matches


file_name = 'claude-3-5-sonnet-20240620_dabench_quantitative_experiment_ablation.jsonl'
with open(file_name, 'r') as f:
    records = [json.loads(line) for line in f]
    total_gt_count = 0
    total_hit_count = 0
    no_cause_hit_count = 0
    no_effect_hit_count = 0
    no_message_hit_count = 0

    for record in records:
        ground_truth = record["answers"]
        total_gt_count += len(ground_truth)
        for attempt in record["analysis_attempts"]:
            # output = attempt['task_result']

            no_cause_output = attempt['task_result'][0]
            no_effect_output = attempt['task_result'][1]
            no_message_output = attempt['task_result'][2]

            # accuracy_score, correct_match = calculate_accuracy(output, ground_truth)

            accuracy_score, no_cause_correct_match = calculate_accuracy(no_cause_output, ground_truth)
            accuracy_score, no_effect_correct_match = calculate_accuracy(no_effect_output, ground_truth)
            accuracy_score, no_message_correct_match = calculate_accuracy(no_message_output, ground_truth)

            # total_hit_count += correct_match

            no_cause_hit_count += no_cause_correct_match
            no_effect_hit_count += no_effect_correct_match
            no_message_hit_count += no_message_correct_match

    model_name = file_name.split('_')[0]

    # macro_acc = total_hit_count / total_gt_count

    no_cause_acc = no_cause_hit_count / total_gt_count
    no_effect_acc = no_effect_hit_count / total_gt_count
    no_message_acc = no_message_hit_count / total_gt_count

    if "no_refine" in file_name:
        print(f"{model_name} direct solution Accuracy: {macro_acc}")
    if "scaling" in file_name:
        print(f"{model_name} self refine with rubber duck debug info 2 turn Accuracy:\n {macro_acc}")
    else:
        print(f"{model_name} self refine with rubber duck debug info Accuracy:\n No Cause: {no_cause_acc}; No Effect: {no_effect_acc}; No Message: {no_message_acc}")