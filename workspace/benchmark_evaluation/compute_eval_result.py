import json

def calculate_single_bug_evaluation_metrics(eval_jsonl_file_path, ground_truth_file_path, total_errors):
    """
    Calculates evaluation metrics (Precision, Recall, F1-score, Accuracy) for each dimension
    (cause_line, effect_line, error_type, error_message) for single-bug detection,
    accounting for missing predictions.

    Args:
        eval_jsonl_file_path (str): Path to the evaluation JSONL file.
        ground_truth_file_path (str): Path to the ground truth JSONL file.
        total_errors (int): Total number of ground truth error instances.

    Returns:
        dict: A dictionary containing aggregated metrics for each dimension.
    """

    dimension_metrics_overall = {  # Initialize overall metrics for each dimension
        "cause_line": {"TP": 0, "FP": 0, "FN": 0},
        "effect_line": {"TP": 0, "FP": 0, "FN": 0},
        "error_type": {"TP": 0, "FP": 0, "FN": 0},
        "error_message": {"TP": 0, "FP": 0, "FN": 0},
    }

    num_eval_results = 0 # Count the total number of evaluation results (predictions made)

    with open(eval_jsonl_file_path, 'r') as f:
        records = [json.loads(line) for line in f]

        for record in records:
            eval_results = record["eval_result"]
            for eval_result in eval_results:
                num_eval_results += 1 # Increment for each eval_result
                # For each dimension, update TP, FP, FN independently based on predictions
                for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                    score_key = f"{dimension}_score"
                    if dimension != "error_message":
                        is_tp_dimension = eval_result[score_key] == 1
                    else:  # For error_message, use relaxed TP condition
                        is_tp_dimension = eval_result[score_key] >= 0.75

                    if is_tp_dimension:
                        dimension_metrics_overall[dimension]["TP"] += 1
                    else:
                        dimension_metrics_overall[dimension]["FP"] += 1

    # Calculate FN and metrics for each dimension, considering total_errors
    aggregated_dimension_metrics = {}

    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
        dimension_metrics_overall[dimension]["FN"] = max(0, total_errors - dimension_metrics_overall[dimension]["TP"]) # Correct FN calculation based on total_errors
        tp = dimension_metrics_overall[dimension]["TP"]
        fp = dimension_metrics_overall[dimension]["FP"]
        fn = dimension_metrics_overall[dimension]["FN"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = tp / num_eval_results if num_eval_results > 0 else 0 # Simplified accuracy: TP / Total Positives (total_errors)

        aggregated_dimension_metrics[dimension] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
            "TP": tp,
            "FP": fp,
            "FN": fn,
            #"TN": 0 # TN is not meaningful in this context, can be removed
        }

    return aggregated_dimension_metrics


eval_jsonl_file = 'eval_llama-3.1-8b-instant_rubber_duck_on_bench_v3_succint_err_msg.jsonl'
ground_truth_jsonl_file = 'bench_final_annotation_v3.jsonl'

with open(ground_truth_jsonl_file, "r") as f:
    total_errors = 0
    for line in f:
        data = json.loads(line)
        error_versions = data.get("error_versions", [])
        total_errors += len(error_versions)

# Read JSONL file to count eval results (predictions made) - optional, but good to know
with open(eval_jsonl_file, 'r') as file:
    records = [json.loads(line) for line in file]
num_eval_results_counted = 0
for record in records:
    num_eval_results_counted += len(record["eval_result"])

# Initialize total scores and max scores (rest of the code remains mostly the same)
total_cause_line_score = 0
total_effect_line_score = 0
total_error_type_score = 0
total_error_message_score = 0
max_error_line_score = 0
max_error_message_score = 0

# Calculate scores
for record in records:
    for eval_result in record["eval_result"]:
        total_cause_line_score += eval_result["cause_line_score"]
        total_effect_line_score += eval_result["effect_line_score"]
        total_error_type_score += eval_result["error_type_score"]
        total_error_message_score += eval_result["error_message_score"]
        max_error_line_score += 1  # Each eval_result has a max error_line_score of 1
        max_error_message_score += 1  # Each eval_result has a max error_message_score of 1

# Calculate the percentage scores
cause_line_percentage = (total_cause_line_score / total_errors) * 100
effect_line_percentage = (total_effect_line_score / total_errors) * 100
error_type_percentage = (total_error_type_score / total_errors) * 100
error_message_percentage = (total_error_message_score / total_errors) * 100

# Print the overall scores
print(f"Total annotated error number: {total_errors}")
print(f"Total detected error number (predictions made): {max_error_line_score}") # Number of predictions made (should be 578)
print(f"Number of eval_results counted: {num_eval_results_counted}") # Verify prediction count
print(f"\nOverall Cause Line Score: {cause_line_percentage:.2f}%")
print(f"Overall Effect Line Score: {effect_line_percentage:.2f}%")
print(f"Overall Error Type Score: {error_type_percentage:.2f}%")
print(f"Overall Error Message Score: {error_message_percentage:.2f}%")

# Calculate and print dimension-wise metrics for single-bug
dimension_wise_metrics = calculate_single_bug_evaluation_metrics(eval_jsonl_file, ground_truth_jsonl_file, total_errors)
print("\nDimension-wise Metrics (Precision, Recall, F1, Accuracy) for Single-Bug Detection:")
print(json.dumps(dimension_wise_metrics, indent=4))