import json

def calculate_ground_truth_error_counts(ground_truth_file_path):
    """
    Calculates the number of ground truth errors for each ID from the ground truth JSONL file.
    (rest of the function remains the same)
    """
    gt_error_counts = {}
    with open(ground_truth_file_path, 'r') as f:
        for line in f:
            gt_data = json.loads(line)
            id_val = gt_data['id']
            # Assuming cause_error_lines (or effect_error_lines) indicates the number of GT errors
            gt_error_count = len(gt_data.get('cause_error_lines', []) or gt_data.get('effect_error_lines', []))
            gt_error_counts[id_val] = gt_error_count
    return gt_error_counts


def calculate_evaluation_scores_with_metrics(eval_jsonl_file_path, ground_truth_file_path):
    """
    Calculates evaluation metrics (Precision, Recall, F1-score, Accuracy) for each dimension
    (cause_line, effect_line, error_type, error_message) separately.

    Args:
        eval_jsonl_file_path (str): Path to the evaluation JSONL file.
        ground_truth_file_path (str): Path to the ground truth JSONL file.

    Returns:
        dict: A dictionary containing aggregated metrics for each dimension.
    """

    id_level_metrics = {}
    all_ids = []
    gt_error_counts_dict = calculate_ground_truth_error_counts(ground_truth_file_path)

    dimension_metrics_overall = {  # Initialize overall metrics for each dimension
        "cause_line": {"TP": 0, "FP": 0, "FN": 0},
        "effect_line": {"TP": 0, "FP": 0, "FN": 0},
        "error_type": {"TP": 0, "FP": 0, "FN": 0},
        "error_message": {"TP": 0, "FP": 0, "FN": 0},
    }

    with open(eval_jsonl_file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            id_val = data['id']
            eval_results_list = data['eval_result']

            all_ids.append(id_val)
            gt_error_count = gt_error_counts_dict.get(id_val, 0)

            dimension_metrics_id = {  # Metrics per dimension per ID - not used for final output, but helpful for debugging
                "cause_line": {"TP": 0, "FP": 0, "FN": 0},
                "effect_line": {"TP": 0, "FP": 0, "FN": 0},
                "error_type": {"TP": 0, "FP": 0, "FN": 0},
                "error_message": {"TP": 0, "FP": 0, "FN": 0},
            }

            for error_version_eval_results in eval_results_list:
                for single_error_eval in error_version_eval_results:

                    # For each dimension, update TP, FP, FN independently
                    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                        score_key = f"{dimension}_score"
                        if dimension != "error_message":
                            is_tp_dimension = single_error_eval[score_key] == 1
                        else: # For error_message, use relaxed TP condition
                            is_tp_dimension = single_error_eval[score_key] >= 0.75

                        if is_tp_dimension:
                            dimension_metrics_overall[dimension]["TP"] += 1
                            dimension_metrics_id[dimension]["TP"] += 1
                        else:
                            dimension_metrics_overall[dimension]["FP"] += 1
                            dimension_metrics_id[dimension]["FP"] += 1


            # Calculate dimension-wise FN (same for all dimensions as FN is about missed *errors*, not dimensions)
             # Using cause_line TP as proxy for correctly identified errors
            for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                fn_errors = max(0, gt_error_count - dimension_metrics_id[dimension]["TP"])
                dimension_metrics_overall[dimension]["FN"] += fn_errors


    aggregated_dimension_metrics = {}
    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
        tp = dimension_metrics_overall[dimension]["TP"]
        fp = dimension_metrics_overall[dimension]["FP"]
        fn = dimension_metrics_overall[dimension]["FN"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0

        aggregated_dimension_metrics[dimension] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
            "TP": tp,
            "FP": fp,
            "FN": fn
        }

    return aggregated_dimension_metrics


def calculate_ground_truth_error_counts(ground_truth_file_path):
    """
    Calculates the number of ground truth errors for each ID from the ground truth JSONL file.
    (rest of the function remains the same)
    """
    gt_error_counts = {}
    with open(ground_truth_file_path, 'r') as f:
        for line in f:
            gt_data = json.loads(line)
            id_val = gt_data['id']
            # Assuming cause_error_lines (or effect_error_lines) indicates the number of GT errors
            gt_error_count = len(gt_data.get('cause_error_lines', []) or gt_data.get('effect_error_lines', []))
            gt_error_counts[id_val] = gt_error_count
    return gt_error_counts


# Example usage:
if __name__ == '__main__':
    eval_jsonl_file = 'eval_gpt-4o_multi_rubber_duck_on_multi_bench_v2.jsonl'  # Replace with your evaluation JSONL file path
    ground_truth_jsonl_file = 'bench_final_annotation_with_multi_errors_v2.jsonl' # Replace with your ground truth JSONL file path

    # Calculate and print dimension-wise metrics
    dimension_wise_metrics = calculate_evaluation_scores_with_metrics(eval_jsonl_file, ground_truth_jsonl_file)
    print("Dimension-wise Metrics (Precision, Recall, F1, Accuracy):")
    print(json.dumps(dimension_wise_metrics, indent=4))