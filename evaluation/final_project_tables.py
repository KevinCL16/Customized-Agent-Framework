import argparse
import json
import re
from pathlib import Path

from final_project_runner import MODEL_ALIASES, SETTINGS, generated_model_name, workspace_name


REPRO_SETTINGS = ["direct", "cot", "default"]
IMPROVEMENT_SETTINGS = ["default", "capimagine"]
ABLATION_SETTINGS = [
    "cap_full",
    "cap_no_imagination",
    "cap_no_root_cause",
    "cap_no_revision_checklist",
    "cap_no_preserve_correct_parts",
]
EVAL_MODELS = ["gpt-4o", "gpt-5.4"]
SCORE_TYPES = ["legacy", "rubric", "combined"]
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


def collect_scores(repo_root, model_alias, setting, eval_model, legacy_weight, rubric_weight):
    workspace_dir = repo_root / workspace_name(model_alias, setting)
    generated_name = generated_model_name(model_alias, setting)
    sanitized_generated = sanitize_label(generated_name)
    sanitized_eval = sanitize_label(eval_model)
    per_example = []

    for example_id in range(1, 101):
        example_dir = workspace_dir / f"example_{example_id}"
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
        per_example.append(
            {
                "id": example_id,
                "legacy": legacy_score,
                "rubric": rubric_score,
                "combined": combined_score,
            }
        )

    summary = {}
    for score_type in SCORE_TYPES:
        values = [row[score_type] for row in per_example if row[score_type] is not None]
        summary[score_type] = {
            "average": (sum(values) / len(values)) if values else None,
            "count": len(values),
            "missing_ids": [row["id"] for row in per_example if row[score_type] is None],
        }

    return {
        "workspace": str(workspace_dir),
        "generated_model_name": generated_name,
        "eval_model": eval_model,
        "summary": summary,
        "per_example": per_example,
    }


def build_full_matrix(repo_root, legacy_weight, rubric_weight):
    matrix = {}
    for model_alias in MODEL_ALIASES:
        matrix[model_alias] = {}
        for setting in SETTINGS:
            matrix[model_alias][setting] = {}
            for eval_model in EVAL_MODELS:
                matrix[model_alias][setting][eval_model] = collect_scores(
                    repo_root=repo_root,
                    model_alias=model_alias,
                    setting=setting,
                    eval_model=eval_model,
                    legacy_weight=legacy_weight,
                    rubric_weight=rubric_weight,
                )
    return matrix


def build_reproduction_table(matrix):
    rows = []
    for model_alias, model_name in MODEL_ALIASES.items():
        row = {"model_alias": model_alias, "model_name": model_name}
        for setting in REPRO_SETTINGS:
            row[setting] = matrix[model_alias][setting]["gpt-5.4"]["summary"]["combined"]["average"]
        rows.append(row)
    return rows


def build_appendix_breakdown(matrix):
    rows = []
    for model_alias, model_name in MODEL_ALIASES.items():
        for setting in REPRO_SETTINGS:
            row = {"model_alias": model_alias, "model_name": model_name, "setting": setting}
            for eval_model in EVAL_MODELS:
                for score_type in SCORE_TYPES:
                    row[f"{score_type}@{eval_model}"] = matrix[model_alias][setting][eval_model]["summary"][score_type]["average"]
            rows.append(row)
    return rows


def build_improvement_table(matrix):
    rows = []
    for model_alias, model_name in MODEL_ALIASES.items():
        default_score = matrix[model_alias]["default"]["gpt-5.4"]["summary"]["combined"]["average"]
        cap_score = matrix[model_alias]["capimagine"]["gpt-5.4"]["summary"]["combined"]["average"]
        delta = None if default_score is None or cap_score is None else cap_score - default_score
        rows.append(
            {
                "model_alias": model_alias,
                "model_name": model_name,
                "default_combined@gpt-5.4": default_score,
                "capimagine_combined@gpt-5.4": cap_score,
                "delta_cap_minus_default": delta,
            }
        )
    return rows


def build_improvement_appendix(matrix):
    rows = []
    for model_alias, model_name in MODEL_ALIASES.items():
        row = {"model_alias": model_alias, "model_name": model_name}
        for eval_model in EVAL_MODELS:
            for score_type in SCORE_TYPES:
                default_score = matrix[model_alias]["default"][eval_model]["summary"][score_type]["average"]
                cap_score = matrix[model_alias]["capimagine"][eval_model]["summary"][score_type]["average"]
                row[f"default_{score_type}@{eval_model}"] = default_score
                row[f"capimagine_{score_type}@{eval_model}"] = cap_score
                row[f"delta_{score_type}@{eval_model}"] = None if default_score is None or cap_score is None else cap_score - default_score
        rows.append(row)
    return rows


def build_ablation_table(matrix):
    rows = []
    carrier_model = "gpt54mini"
    for setting in ABLATION_SETTINGS:
        row = {"model_alias": carrier_model, "setting": setting}
        for eval_model in EVAL_MODELS:
            for score_type in SCORE_TYPES:
                row[f"{score_type}@{eval_model}"] = matrix[carrier_model][setting][eval_model]["summary"][score_type]["average"]
        rows.append(row)
    return rows


def render_markdown_table(rows, columns):
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(format_cell(row.get(column)) for column in columns) + " |")
    return "\n".join([header, divider, *body])


def format_cell(value):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def write_outputs(output_dir, stem, rows, columns):
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{stem}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / f"{stem}.md").write_text(render_markdown_table(rows, columns), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_root", type=str, default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--legacy_weight", type=float, default=0.5)
    parser.add_argument("--rubric_weight", type=float, default=0.5)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix = build_full_matrix(repo_root, args.legacy_weight, args.rubric_weight)

    (output_dir / "final_project_score_matrix.json").write_text(
        json.dumps(matrix, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    reproduction_rows = build_reproduction_table(matrix)
    write_outputs(
        output_dir,
        "main_table_reproduction",
        reproduction_rows,
        ["model_alias", "model_name", "direct", "cot", "default"],
    )

    appendix_rows = build_appendix_breakdown(matrix)
    write_outputs(
        output_dir,
        "appendix_table_reproduction_breakdown",
        appendix_rows,
        [
            "model_alias",
            "model_name",
            "setting",
            "legacy@gpt-4o",
            "rubric@gpt-4o",
            "combined@gpt-4o",
            "legacy@gpt-5.4",
            "rubric@gpt-5.4",
            "combined@gpt-5.4",
        ],
    )

    improvement_rows = build_improvement_table(matrix)
    write_outputs(
        output_dir,
        "main_table_capimagine_improvement",
        improvement_rows,
        [
            "model_alias",
            "model_name",
            "default_combined@gpt-5.4",
            "capimagine_combined@gpt-5.4",
            "delta_cap_minus_default",
        ],
    )

    improvement_appendix_rows = build_improvement_appendix(matrix)
    write_outputs(
        output_dir,
        "appendix_table_capimagine_breakdown",
        improvement_appendix_rows,
        [
            "model_alias",
            "model_name",
            "default_legacy@gpt-4o",
            "capimagine_legacy@gpt-4o",
            "delta_legacy@gpt-4o",
            "default_rubric@gpt-4o",
            "capimagine_rubric@gpt-4o",
            "delta_rubric@gpt-4o",
            "default_combined@gpt-4o",
            "capimagine_combined@gpt-4o",
            "delta_combined@gpt-4o",
            "default_legacy@gpt-5.4",
            "capimagine_legacy@gpt-5.4",
            "delta_legacy@gpt-5.4",
            "default_rubric@gpt-5.4",
            "capimagine_rubric@gpt-5.4",
            "delta_rubric@gpt-5.4",
            "default_combined@gpt-5.4",
            "capimagine_combined@gpt-5.4",
            "delta_combined@gpt-5.4",
        ],
    )

    ablation_rows = build_ablation_table(matrix)
    write_outputs(
        output_dir,
        "appendix_table_capimagine_ablation",
        ablation_rows,
        [
            "model_alias",
            "setting",
            "legacy@gpt-4o",
            "rubric@gpt-4o",
            "combined@gpt-4o",
            "legacy@gpt-5.4",
            "rubric@gpt-5.4",
            "combined@gpt-5.4",
        ],
    )


if __name__ == "__main__":
    main()
