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

def calculate_evaluation_scores_exact_match_per_id(eval_jsonl_file_path, ground_truth_file_path):
    """
    Calculates evaluation metrics based on exact match of predicted and ground truth error sets,
    evaluated PER ID (per data instance).

    TP: For an ID, model predicts exactly the same set of errors as ground truth in at least one version.
    FP: For an ID, model predicts a different set of errors in ALL versions, and at least one version is non-empty.
    FN: For an ID, ground truth has errors, but model predicts an empty set of errors in ALL versions (or eval_result is empty).
    """
    gt_error_counts_dict = calculate_ground_truth_error_counts(ground_truth_file_path) # Get GT error counts per ID
    error_bug_count = {}
    bug_count_dimension_metrics = {}

    with open(eval_jsonl_file_path, 'r') as f:
        records = [json.loads(line) for line in f]
        for idx, bug_count in gt_error_counts_dict.items():
            if bug_count not in error_bug_count:
                error_bug_count[bug_count] = []
                found_record = [record for record in records if record.get("id") == idx]
                if found_record:
                    error_bug_count[bug_count].append(found_record)
            else:
                found_record = [record for record in records if record.get("id") == idx]
                if found_record:
                    error_bug_count[bug_count].append(found_record)

        for bug_count, data in error_bug_count.items():
            dimension_metrics_overall = {  # Initialize overall dimension metrics
                "cause_line": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
                # Added GT_Instances to track total GT instances per dimension
                "effect_line": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
                "error_type": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
                "error_message": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
            }
            for sample in data:
                id_val = sample[0]['id']
                eval_results_list = sample[0]['eval_result'] # list of error versions
                gt_error_count = gt_error_counts_dict.get(id_val, 0)
                for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                    dimension_metrics_overall[dimension]["Total_IDs"] += 1

                is_tp_for_id = False # Flag to check if it's TP for this ID
                all_versions_empty = True # Flag to check if all versions are empty predictions

                if eval_results_list:
                    all_versions_empty = False
                    for error_version_eval_results in eval_results_list:
                        if len(error_version_eval_results) != gt_error_count:
                            for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                                dimension_metrics_overall[dimension]["FP"] += 1
                        else:
                            for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                                for single_error_eval in error_version_eval_results:
                                    score_key = f"{dimension}_score"
                                    try:
                                        is_fp_dimension = (
                                            single_error_eval[score_key] != 1 if dimension != "error_message" else
                                            single_error_eval[score_key] < 0.75)
                                    except KeyError as e:
                                        print(f"{e}\nid:{id_val}")

                                    if is_fp_dimension:
                                        dimension_metrics_overall[dimension]["FP"] += 1
                                        break
                                if not is_fp_dimension:
                                    dimension_metrics_overall[dimension]["TP"] += 1

                else:
                    if all_versions_empty:  # All versions are empty predictions -> FN
                        for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                            dimension_metrics_overall[dimension]["FN"] += 1

            aggregated_dimension_metrics = {}
            for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                tp = dimension_metrics_overall[dimension]["TP"]
                fp = dimension_metrics_overall[dimension]["FP"]
                # Corrected FN calculation: FN = Total Ground Truth Instances - (TP + FP) for each dimension
                fn = dimension_metrics_overall[dimension]["FN"]
                total_ids = dimension_metrics_overall[dimension]["Total_IDs"]

                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn + fp) if (tp + fn + fp) > 0 else 0
                f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                accuracy = tp / total_ids if total_ids > 0 else 0 # Accuracy: Exact match IDs / Total IDs

                aggregated_dimension_metrics[dimension] = {
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score,
                    "accuracy": accuracy,
                    "TP": tp,
                    "FP": fp,
                    "FN": fn,
                    "Total_IDs": dimension_metrics_overall[dimension]["Total_IDs"]
                }
                bug_count_dimension_metrics[bug_count] = aggregated_dimension_metrics

    return bug_count_dimension_metrics


if __name__ == '__main__':
    eval_jsonl_file = 'eval_Qwen2.5-72B-Instruct_multi_rubber_duck_on_multi_bench_v2.jsonl'
    ground_truth_jsonl_file = 'bench_final_annotation_with_multi_errors_v2.jsonl'

    model_type = eval_jsonl_file.split("_")[1]

    # Exact Match Metrics per ID
    exact_match_metrics_per_id = calculate_evaluation_scores_exact_match_per_id(eval_jsonl_file, ground_truth_jsonl_file)
    print(f"\n{model_type} Exact Match Metrics per ID (Precision, Recall, F1, Accuracy) for Multi-Bug Detection:")
    print(json.dumps(exact_match_metrics_per_id, indent=4))