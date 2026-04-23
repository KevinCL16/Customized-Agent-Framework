import argparse
import json
import re
from pathlib import Path


DEFAULT_OVERRIDE_IDS = []
BUCKETS = [
    ("0-20", 0, 20),
    ("20-40", 20, 40),
    ("40-60", 40, 60),
    ("60+", 60, None),
]


def sanitize_label(value):
    return value.replace("/", "_").replace(":", "_").replace(".", "_").replace("-", "_")


def extract_last_score(log_path, pattern):
    if not log_path.exists():
        return None
    contents = log_path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(pattern, contents, re.DOTALL)
    if not matches:
        return None
    return float(matches[-1])


def resolve_example_dir(base_workspace, override_workspace, example_id, override_ids):
    if override_workspace is not None and example_id in override_ids:
        candidate = override_workspace / f"example_{example_id}"
        if candidate.exists():
            return candidate
    return base_workspace / f"example_{example_id}"


def load_score_from_candidate_names(example_dir, generated_model_names, eval_model):
    legacy_pattern = r"\[FINAL SCORE\]: (\d{1,3}(?:\.\d+)?)"
    rubric_pattern = r"\[RUBRIC SCORE\]: (\d{1,3}(?:\.\d+)?)"
    for generated_model_name in generated_model_names:
        legacy_log_name = f"eval_{sanitize_label(generated_model_name)}_by_{sanitize_label(eval_model)}.log"
        rubric_log_name = f"eval_rubric_{sanitize_label(generated_model_name)}_by_{sanitize_label(eval_model)}.log"
        legacy_score = extract_last_score(example_dir / legacy_log_name, legacy_pattern)
        rubric_score = extract_last_score(example_dir / rubric_log_name, rubric_pattern)
        if legacy_score is not None or rubric_score is not None:
            return legacy_score, rubric_score, generated_model_name
    return None, None, None


def load_scores_for_setting(
    base_workspace,
    override_workspace,
    override_ids,
    base_generated_model_name,
    override_generated_model_name,
    eval_model,
    legacy_weight,
    rubric_weight,
):
    data = {}
    for example_id in range(1, 101):
        example_dir = resolve_example_dir(base_workspace, override_workspace, example_id, override_ids)
        is_override = (
            override_workspace is not None
            and example_id in override_ids
            and (override_workspace / f"example_{example_id}").exists()
        )
        generated_model_names = [override_generated_model_name, base_generated_model_name] if is_override else [base_generated_model_name]
        legacy_score, rubric_score, resolved_model_name = load_score_from_candidate_names(
            example_dir,
            generated_model_names,
            eval_model,
        )
        combined_score = None
        if legacy_score is not None and rubric_score is not None:
            combined_score = (legacy_weight * legacy_score) + (rubric_weight * rubric_score)
        data[example_id] = {
            "example_dir": str(example_dir),
            "resolved_model_name": resolved_model_name,
            "legacy": legacy_score,
            "rubric": rubric_score,
            "combined": combined_score,
        }
    return data


def assign_bucket(score):
    if score is None:
        return "missing"
    for label, lower, upper in BUCKETS:
        if upper is None and score >= lower:
            return label
        if upper is not None and lower <= score < upper:
            return label
    return "missing"


def average(values):
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return sum(valid_values) / len(valid_values)


def build_bucket_summary(default_scores, cap_scores):
    grouped = {label: [] for label, _, _ in BUCKETS}
    grouped["missing"] = []

    for example_id, scores in default_scores.items():
        grouped[assign_bucket(scores["legacy"])].append(example_id)

    bucket_summary = []
    for bucket_name, example_ids in grouped.items():
        if bucket_name == "missing":
            continue
        default_bucket = [default_scores[example_id] for example_id in example_ids]
        cap_bucket = [cap_scores[example_id] for example_id in example_ids]
        default_legacy = average([item["legacy"] for item in default_bucket])
        default_rubric = average([item["rubric"] for item in default_bucket])
        default_combined = average([item["combined"] for item in default_bucket])
        cap_legacy = average([item["legacy"] for item in cap_bucket])
        cap_rubric = average([item["rubric"] for item in cap_bucket])
        cap_combined = average([item["combined"] for item in cap_bucket])
        bucket_summary.append(
            {
                "bucket": bucket_name,
                "count": len(example_ids),
                "example_ids": example_ids,
                "default": {
                    "legacy": default_legacy,
                    "rubric": default_rubric,
                    "combined": default_combined,
                },
                "capimagine": {
                    "legacy": cap_legacy,
                    "rubric": cap_rubric,
                    "combined": cap_combined,
                },
                "delta_cap_minus_default": {
                    "legacy": None if default_legacy is None or cap_legacy is None else cap_legacy - default_legacy,
                    "rubric": None if default_rubric is None or cap_rubric is None else cap_rubric - default_rubric,
                    "combined": None if default_combined is None or cap_combined is None else cap_combined - default_combined,
                },
            }
        )
    return bucket_summary


def build_overall_summary(default_scores, cap_scores):
    return {
        "default": {
            "legacy": average([entry["legacy"] for entry in default_scores.values()]),
            "rubric": average([entry["rubric"] for entry in default_scores.values()]),
            "combined": average([entry["combined"] for entry in default_scores.values()]),
        },
        "capimagine": {
            "legacy": average([entry["legacy"] for entry in cap_scores.values()]),
            "rubric": average([entry["rubric"] for entry in cap_scores.values()]),
            "combined": average([entry["combined"] for entry in cap_scores.values()]),
        },
    }


def build_summary_result(args, overall, bucket_summary, override_ids):
    return {
        "eval_model": args.eval_model,
        "weights": {
            "legacy": args.legacy_weight,
            "rubric": args.rubric_weight,
        },
        "override_ids": sorted(override_ids),
        "overall": overall,
        "overall_delta_cap_minus_default": {
            "legacy": overall["capimagine"]["legacy"] - overall["default"]["legacy"],
            "rubric": overall["capimagine"]["rubric"] - overall["default"]["rubric"],
            "combined": overall["capimagine"]["combined"] - overall["default"]["combined"],
        },
        "buckets": bucket_summary,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--default_base_workspace", required=True)
    parser.add_argument("--default_override_workspace", default=None)
    parser.add_argument("--cap_base_workspace", required=True)
    parser.add_argument("--cap_override_workspace", default=None)
    parser.add_argument("--override_ids", nargs="*", type=int, default=DEFAULT_OVERRIDE_IDS)
    parser.add_argument("--eval_model", type=str, default="gpt-4o")
    parser.add_argument("--default_generated_model_name", type=str, default="gpt-5.4-mini")
    parser.add_argument("--default_override_generated_model_name", type=str, default="gpt-5.4-mini_default")
    parser.add_argument("--cap_generated_model_name", type=str, default="gpt-5.4-mini_capimagine")
    parser.add_argument("--cap_override_generated_model_name", type=str, default="gpt-5.4-mini_capimagine")
    parser.add_argument("--legacy_weight", type=float, default=0.5)
    parser.add_argument("--rubric_weight", type=float, default=0.5)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--summary_output_path", type=str, default=None)
    args = parser.parse_args()

    override_ids = set(args.override_ids)
    default_scores = load_scores_for_setting(
        base_workspace=Path(args.default_base_workspace),
        override_workspace=Path(args.default_override_workspace) if args.default_override_workspace else None,
        override_ids=override_ids,
        base_generated_model_name=args.default_generated_model_name,
        override_generated_model_name=args.default_override_generated_model_name,
        eval_model=args.eval_model,
        legacy_weight=args.legacy_weight,
        rubric_weight=args.rubric_weight,
    )
    cap_scores = load_scores_for_setting(
        base_workspace=Path(args.cap_base_workspace),
        override_workspace=Path(args.cap_override_workspace) if args.cap_override_workspace else None,
        override_ids=override_ids,
        base_generated_model_name=args.cap_generated_model_name,
        override_generated_model_name=args.cap_override_generated_model_name,
        eval_model=args.eval_model,
        legacy_weight=args.legacy_weight,
        rubric_weight=args.rubric_weight,
    )

    overall = build_overall_summary(default_scores, cap_scores)
    bucket_summary = build_bucket_summary(default_scores, cap_scores)
    summary_result = build_summary_result(args, overall, bucket_summary, override_ids)

    result = {
        **summary_result,
        "buckets": bucket_summary,
        "per_example": {
            "default": default_scores,
            "capimagine": cap_scores,
        },
    }

    output_path = Path(args.output_path)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote analysis to {output_path}")
    if args.summary_output_path:
        summary_output_path = Path(args.summary_output_path)
        summary_output_path.write_text(json.dumps(summary_result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote summary analysis to {summary_output_path}")


if __name__ == "__main__":
    main()
