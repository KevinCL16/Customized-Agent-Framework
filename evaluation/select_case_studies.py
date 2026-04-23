import argparse
import json
import re
from pathlib import Path

from final_project_runner import generated_model_name, workspace_name


LEGACY_PATTERN = r"\[FINAL SCORE\]: (\d{1,3}(?:\.\d+)?)"
RUBRIC_PATTERN = r"\[RUBRIC SCORE\]: (\d{1,3}(?:\.\d+)?)"


def sanitize_label(value):
    return value.replace("/", "_").replace(":", "_").replace(".", "_").replace("-", "_")


def extract_last_score(path, pattern):
    if not path.exists():
        return None
    contents = path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(pattern, contents, re.DOTALL)
    if not matches:
        return None
    return float(matches[-1])


def average_score(example_dir, generated_name, eval_model, legacy_weight, rubric_weight):
    sanitized_generated = sanitize_label(generated_name)
    sanitized_eval = sanitize_label(eval_model)
    legacy_score = extract_last_score(
        example_dir / f"eval_{sanitized_generated}_by_{sanitized_eval}.log",
        LEGACY_PATTERN,
    )
    rubric_score = extract_last_score(
        example_dir / f"eval_rubric_{sanitized_generated}_by_{sanitized_eval}.log",
        RUBRIC_PATTERN,
    )
    combined_score = None
    if legacy_score is not None and rubric_score is not None:
        combined_score = (legacy_weight * legacy_score) + (rubric_weight * rubric_score)
    return legacy_score, rubric_score, combined_score


def figure_path(example_dir):
    final_path = example_dir / "novice_final.png"
    if final_path.exists():
        return final_path
    return example_dir / "novice.png"


def collect_setting_examples(repo_root, model_alias, setting, eval_model, legacy_weight, rubric_weight):
    workspace_dir = repo_root / workspace_name(model_alias, setting)
    generated_name = generated_model_name(model_alias, setting)
    rows = []
    for example_id in range(1, 101):
        example_dir = workspace_dir / f"example_{example_id}"
        legacy_score, rubric_score, combined_score = average_score(
            example_dir,
            generated_name,
            eval_model,
            legacy_weight,
            rubric_weight,
        )
        rows.append(
            {
                "id": example_id,
                "example_dir": str(example_dir),
                "image_path": str(figure_path(example_dir)),
                "legacy": legacy_score,
                "rubric": rubric_score,
                "combined": combined_score,
            }
        )
    return rows


def sort_valid(rows, key_name, reverse):
    return sorted(
        [row for row in rows if row[key_name] is not None],
        key=lambda row: row[key_name],
        reverse=reverse,
    )


def pick_reproduction_cases(rows, top_k):
    valid_rows = sort_valid(rows, "combined", reverse=False)
    if not valid_rows:
        return {"best": [], "typical": [], "failures": []}

    best = sort_valid(rows, "combined", reverse=True)[:top_k]
    failures = valid_rows[:top_k]

    midpoint = len(valid_rows) // 2
    start = max(0, midpoint - (top_k // 2))
    typical = valid_rows[start : start + top_k]

    return {
        "best": best,
        "typical": typical,
        "failures": failures,
    }


def pick_capimagine_cases(default_rows, cap_rows, top_k):
    paired = []
    default_by_id = {row["id"]: row for row in default_rows}
    for cap_row in cap_rows:
        default_row = default_by_id[cap_row["id"]]
        default_combined = default_row["combined"]
        cap_combined = cap_row["combined"]
        combined_delta = None if default_combined is None or cap_combined is None else cap_combined - default_combined
        divergence = None
        if cap_row["legacy"] is not None and cap_row["rubric"] is not None:
            divergence = cap_row["rubric"] - cap_row["legacy"]
        paired.append(
            {
                "id": cap_row["id"],
                "default": default_row,
                "capimagine": cap_row,
                "combined_delta": combined_delta,
                "rubric_minus_legacy": divergence,
            }
        )

    biggest_gains = sorted(
        [row for row in paired if row["combined_delta"] is not None],
        key=lambda row: row["combined_delta"],
        reverse=True,
    )[:top_k]
    biggest_regressions = sorted(
        [row for row in paired if row["combined_delta"] is not None],
        key=lambda row: row["combined_delta"],
    )[:top_k]
    biggest_divergence = sorted(
        [row for row in paired if row["rubric_minus_legacy"] is not None],
        key=lambda row: abs(row["rubric_minus_legacy"]),
        reverse=True,
    )[:top_k]

    return {
        "biggest_gains": biggest_gains,
        "biggest_regressions": biggest_regressions,
        "largest_rubric_legacy_divergence": biggest_divergence,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_root", type=str, default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--model_alias", required=True)
    parser.add_argument("--eval_model", default="gpt-5.4")
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--legacy_weight", type=float, default=0.5)
    parser.add_argument("--rubric_weight", type=float, default=0.5)
    parser.add_argument("--output_path", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    reproduction = {}
    for setting in ["direct", "cot", "default"]:
        rows = collect_setting_examples(
            repo_root,
            args.model_alias,
            setting,
            args.eval_model,
            args.legacy_weight,
            args.rubric_weight,
        )
        reproduction[setting] = pick_reproduction_cases(rows, args.top_k)

    default_rows = collect_setting_examples(
        repo_root,
        args.model_alias,
        "default",
        args.eval_model,
        args.legacy_weight,
        args.rubric_weight,
    )
    cap_rows = collect_setting_examples(
        repo_root,
        args.model_alias,
        "capimagine",
        args.eval_model,
        args.legacy_weight,
        args.rubric_weight,
    )
    capimagine = pick_capimagine_cases(default_rows, cap_rows, args.top_k)

    result = {
        "model_alias": args.model_alias,
        "eval_model": args.eval_model,
        "top_k": args.top_k,
        "reproduction": reproduction,
        "capimagine": capimagine,
    }
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
