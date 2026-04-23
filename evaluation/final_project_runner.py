import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = REPO_ROOT / "benchmark_data"

MODEL_ALIASES = {
    "gpt54mini": "gpt-5.4-mini",
    "gemini3flash": "google/gemini-3-flash-preview",
    "claudehaiku45": "anthropic/claude-haiku-4.5",
}

SETTINGS = {
    "direct": {
        "script": "one_time_generate.py",
        "workspace_suffix": "direct_full",
        "generated_model_name_suffix": "direct",
        "extra_args": [],
    },
    "cot": {
        "script": "one_time_generate_COT.py",
        "workspace_suffix": "cot_full",
        "generated_model_name_suffix": "cot",
        "extra_args": [],
    },
    "default": {
        "script": "workflow.py",
        "workspace_suffix": "default_full",
        "generated_model_name_suffix": "default",
        "extra_args": ["--visual_refine", "true", "--visual_refine_prompt_variant", "default"],
    },
    "capimagine": {
        "script": "workflow.py",
        "workspace_suffix": "capimagine_full",
        "generated_model_name_suffix": "capimagine",
        "extra_args": ["--visual_refine", "true", "--visual_refine_prompt_variant", "capimagine"],
    },
    "cap_full": {
        "script": "workflow.py",
        "workspace_suffix": "cap_full_full",
        "generated_model_name_suffix": "cap_full",
        "extra_args": ["--visual_refine", "true", "--visual_refine_prompt_variant", "cap_full"],
    },
    "cap_no_imagination": {
        "script": "workflow.py",
        "workspace_suffix": "cap_no_imagination_full",
        "generated_model_name_suffix": "cap_no_imagination",
        "extra_args": ["--visual_refine", "true", "--visual_refine_prompt_variant", "cap_no_imagination"],
    },
    "cap_no_root_cause": {
        "script": "workflow.py",
        "workspace_suffix": "cap_no_root_cause_full",
        "generated_model_name_suffix": "cap_no_root_cause",
        "extra_args": ["--visual_refine", "true", "--visual_refine_prompt_variant", "cap_no_root_cause"],
    },
    "cap_no_revision_checklist": {
        "script": "workflow.py",
        "workspace_suffix": "cap_no_revision_checklist_full",
        "generated_model_name_suffix": "cap_no_revision_checklist",
        "extra_args": ["--visual_refine", "true", "--visual_refine_prompt_variant", "cap_no_revision_checklist"],
    },
    "cap_no_preserve_correct_parts": {
        "script": "workflow.py",
        "workspace_suffix": "cap_no_preserve_correct_parts_full",
        "generated_model_name_suffix": "cap_no_preserve_correct_parts",
        "extra_args": ["--visual_refine", "true", "--visual_refine_prompt_variant", "cap_no_preserve_correct_parts"],
    },
}


def run_command(command):
    print("Running:", " ".join(command))
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def try_run_command(command):
    print("Running:", " ".join(command))
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return result.returncode == 0


def workspace_name(model_alias, setting):
    return f"workspace_finalproj_{model_alias}_{SETTINGS[setting]['workspace_suffix']}"


def generated_model_name(model_alias, setting):
    return f"{model_alias}_{SETTINGS[setting]['generated_model_name_suffix']}"


def _is_nonempty_file(path):
    return path.exists() and path.is_file() and path.stat().st_size > 0


def expected_figure_path(workspace_dir, setting, example_id):
    example_dir = workspace_dir / f"example_{example_id}"
    if setting in {"default", "capimagine"}:
        return example_dir / "novice_final.png"
    return example_dir / "novice.png"


def legacy_log_path(workspace_dir, example_id, generated_name, eval_model):
    sanitized_generated = sanitize_label(generated_name)
    sanitized_eval = sanitize_label(eval_model)
    return workspace_dir / f"example_{example_id}" / f"eval_{sanitized_generated}_by_{sanitized_eval}.log"


def rubric_log_path(workspace_dir, example_id, generated_name, eval_model):
    sanitized_generated = sanitize_label(generated_name)
    sanitized_eval = sanitize_label(eval_model)
    return workspace_dir / f"example_{example_id}" / f"eval_rubric_{sanitized_generated}_by_{sanitized_eval}.log"


def sanitize_label(value):
    return value.replace("/", "_").replace(":", "_").replace(".", "_").replace("-", "_")


def parse_id_range(start_id, end_id):
    return list(range(start_id, end_id + 1))


def missing_generation_ids(workspace_dir, setting, ids):
    missing_ids = []
    for example_id in ids:
        if not _is_nonempty_file(expected_figure_path(workspace_dir, setting, example_id)):
            missing_ids.append(example_id)
    return missing_ids


def missing_eval_ids(workspace_dir, ids, generated_name, eval_model, score_mode):
    missing_ids = []
    for example_id in ids:
        if score_mode == "legacy":
            if not legacy_log_path(workspace_dir, example_id, generated_name, eval_model).exists():
                missing_ids.append(example_id)
        elif score_mode == "rubric":
            if not rubric_log_path(workspace_dir, example_id, generated_name, eval_model).exists():
                missing_ids.append(example_id)
        else:
            if not legacy_log_path(workspace_dir, example_id, generated_name, eval_model).exists():
                missing_ids.append(example_id)
            elif not rubric_log_path(workspace_dir, example_id, generated_name, eval_model).exists():
                missing_ids.append(example_id)
    return missing_ids


def maybe_filter_ids(ids, workspace_dir, skip_existing, mode, setting=None, generated_name=None, eval_model=None):
    if not skip_existing:
        return ids
    if mode == "generation":
        return missing_generation_ids(workspace_dir, setting, ids)
    return missing_eval_ids(workspace_dir, ids, generated_name, eval_model, mode)


def command_for_generation(model_alias, setting, ids):
    model_name = MODEL_ALIASES[model_alias]
    config = SETTINGS[setting]
    workspace = workspace_name(model_alias, setting)
    command = [
        sys.executable,
        str(REPO_ROOT / config["script"]),
        "--model_type",
        model_name,
        "--workspace",
        workspace,
        "--benchmark_dir",
        str(BENCHMARK_DIR),
    ]
    if ids:
        command += ["--data_ids", *[str(item_id) for item_id in ids]]
    command += config["extra_args"]
    return command


def command_for_eval(model_alias, setting, example_id, eval_model, score_mode):
    workspace = workspace_name(model_alias, setting)
    generated_name = generated_model_name(model_alias, setting)
    command = [
        sys.executable,
        str(REPO_ROOT / "evaluation" / "api_eval.py"),
        str(example_id),
        "--workspace",
        workspace,
        "--benchmark_dir",
        str(BENCHMARK_DIR),
        "--direct_eval",
        "--generated_model_name",
        generated_name,
        "--eval_model",
        eval_model,
    ]
    if score_mode == "rubric":
        command += ["--run_rubric_eval", "--skip_legacy_eval"]
    elif score_mode == "combined":
        command += ["--run_rubric_eval"]
    return command


def command_for_summary(model_alias, setting, eval_model, score_type):
    workspace = workspace_name(model_alias, setting)
    generated_name = generated_model_name(model_alias, setting)
    return [
        sys.executable,
        str(REPO_ROOT / "evaluation" / "average_score_calc.py"),
        "--workspace",
        workspace,
        "--start_id",
        "1",
        "--end_id",
        "100",
        "--generated_model_name",
        generated_name,
        "--eval_model",
        eval_model,
        "--score_type",
        score_type,
    ]


def build_manifest():
    rows = []
    for model_alias, model_name in MODEL_ALIASES.items():
        for setting in SETTINGS:
            rows.append(
                {
                    "model_alias": model_alias,
                    "model_name": model_name,
                    "setting": setting,
                    "workspace": workspace_name(model_alias, setting),
                    "generated_model_name": generated_model_name(model_alias, setting),
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--output", type=str, default=None)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--model_alias", choices=MODEL_ALIASES.keys(), required=True)
    generate_parser.add_argument("--setting", choices=SETTINGS.keys(), required=True)
    generate_parser.add_argument("--start_id", type=int, default=1)
    generate_parser.add_argument("--end_id", type=int, default=100)
    generate_parser.add_argument("--skip_existing", action="store_true")

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument("--model_alias", choices=MODEL_ALIASES.keys(), required=True)
    eval_parser.add_argument("--setting", choices=SETTINGS.keys(), required=True)
    eval_parser.add_argument("--eval_model", choices=["gpt-4o", "gpt-5.4"], required=True)
    eval_parser.add_argument("--score_mode", choices=["legacy", "rubric", "combined"], default="combined")
    eval_parser.add_argument("--start_id", type=int, default=1)
    eval_parser.add_argument("--end_id", type=int, default=100)
    eval_parser.add_argument("--skip_existing", action="store_true")

    summary_parser = subparsers.add_parser("summarize")
    summary_parser.add_argument("--model_alias", choices=MODEL_ALIASES.keys(), required=True)
    summary_parser.add_argument("--setting", choices=SETTINGS.keys(), required=True)
    summary_parser.add_argument("--eval_model", choices=["gpt-4o", "gpt-5.4"], required=True)
    summary_parser.add_argument("--score_type", choices=["legacy", "rubric", "combined"], required=True)

    args = parser.parse_args()

    if args.command == "manifest":
        manifest = build_manifest()
        text = json.dumps(manifest, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text)
        return

    ids = parse_id_range(args.start_id, args.end_id)

    if args.command == "generate":
        workspace_dir = REPO_ROOT / workspace_name(args.model_alias, args.setting)
        ids = maybe_filter_ids(ids, workspace_dir, args.skip_existing, "generation", setting=args.setting)
        if not ids:
            print("No generation work needed.")
            return
        run_command(command_for_generation(args.model_alias, args.setting, ids))
        return

    if args.command == "eval":
        workspace_dir = REPO_ROOT / workspace_name(args.model_alias, args.setting)
        generated_name = generated_model_name(args.model_alias, args.setting)
        ids = maybe_filter_ids(
            ids,
            workspace_dir,
            args.skip_existing,
            args.score_mode,
            generated_name=generated_name,
            eval_model=args.eval_model,
        )
        if not ids:
            print("No evaluation work needed.")
            return
        failed_ids = []
        for example_id in ids:
            command = command_for_eval(args.model_alias, args.setting, example_id, args.eval_model, args.score_mode)
            if not try_run_command(command):
                failed_ids.append(example_id)
        if failed_ids:
            print("Evaluation failed for ids:")
            print(failed_ids)
            raise SystemExit(1)
        return

    if args.command == "summarize":
        run_command(command_for_summary(args.model_alias, args.setting, args.eval_model, args.score_type))


if __name__ == "__main__":
    main()
