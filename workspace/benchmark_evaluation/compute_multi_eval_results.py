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


def calculate_evaluation_scores_with_metrics_corrected(eval_jsonl_file_path, ground_truth_file_path):
    """
    Corrected function to calculate dimension-level evaluation metrics (Precision, Recall, F1-score, Accuracy).
    FN is calculated correctly at the dimension level. Accuracy denominator is corrected.
    """

    gt_error_counts_dict = calculate_ground_truth_error_counts(ground_truth_file_path) # Get GT error counts per ID
    dimension_metrics_overall = { # Initialize overall dimension metrics
        "cause_line": {"TP": 0, "FP": 0, "FN": 0, "GT_Instances": 0}, # Added GT_Instances to track total GT instances per dimension
        "effect_line": {"TP": 0, "FP": 0, "FN": 0, "GT_Instances": 0},
        "error_type": {"TP": 0, "FP": 0, "FN": 0, "GT_Instances": 0},
        "error_message": {"TP": 0, "FP": 0, "FN": 0, "GT_Instances": 0},
    }

    processed_ids = set() # To avoid recounting GT instances for the same ID
    with open(eval_jsonl_file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            id_val = data['id']
            eval_results_list = data['eval_result']
            gt_error_count = gt_error_counts_dict.get(id_val, 0) # Get GT error count for this ID

            if id_val not in processed_ids: # Count GT instances only once per ID
                for dimension in dimension_metrics_overall:
                    dimension_metrics_overall[dimension]["GT_Instances"] += gt_error_count # Assuming each error version in GT contributes to GT_Instances
                processed_ids.add(id_val)

            for error_version_eval_results in eval_results_list:
                for single_error_eval in error_version_eval_results:
                    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                        score_key = f"{dimension}_score"
                        try:
                            is_tp_dimension = (single_error_eval[score_key] == 1 if dimension != "error_message" else single_error_eval[score_key] >= 0.75)
                        except KeyError as e:
                            print(f"{e}\nid:{id_val}")

                        if is_tp_dimension:
                            dimension_metrics_overall[dimension]["TP"] += 1
                        else:
                            dimension_metrics_overall[dimension]["FP"] += 1

    aggregated_dimension_metrics = {}
    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
        tp = dimension_metrics_overall[dimension]["TP"]
        fp = dimension_metrics_overall[dimension]["FP"]
        # Corrected FN calculation: FN = Total Ground Truth Instances - (TP + FP) for each dimension
        fn = max(0, dimension_metrics_overall[dimension]["GT_Instances"] - (tp + fp))
        dimension_metrics_overall[dimension]["FN"] = fn # Update FN in overall metrics

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn + fp) if (tp + fn + fp) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        # Corrected Accuracy calculation: Accuracy = TP / Total Ground Truth Instances for this dimension
        accuracy = tp / dimension_metrics_overall[dimension]["GT_Instances"] if dimension_metrics_overall[dimension]["GT_Instances"] > 0 else 0

        aggregated_dimension_metrics[dimension] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "GT_Instances": dimension_metrics_overall[dimension]["GT_Instances"] # Added GT_Instances to output
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
    eval_jsonl_file = 'eval_o1-mini_multi_rubber_duck_on_multi_bench_v2.jsonl'
    ground_truth_jsonl_file = 'bench_final_annotation_with_multi_errors_v2.jsonl'

    model_type = eval_jsonl_file.split("_")[1]
    dimension_wise_metrics_corrected = calculate_evaluation_scores_with_metrics_corrected(eval_jsonl_file, ground_truth_jsonl_file)
    print(f"\n{model_type} Dimension-wise Metrics (Precision, Recall, F1, Accuracy) for Multi-Bug Detection:")
    print(json.dumps(dimension_wise_metrics_corrected, indent=4))