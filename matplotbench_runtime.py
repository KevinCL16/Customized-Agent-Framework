from pathlib import Path
import json
import shutil


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_BENCHMARK_DIR = REPO_ROOT / "benchmark_data"


def resolve_benchmark_dir(benchmark_dir=None):
    if benchmark_dir is None:
        return DEFAULT_BENCHMARK_DIR
    return Path(benchmark_dir).expanduser().resolve()


def load_benchmark_instructions(benchmark_dir=None):
    benchmark_dir = resolve_benchmark_dir(benchmark_dir)
    instruction_path = benchmark_dir / "benchmark_instructions.json"
    with instruction_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def filter_benchmark_items(items, start_id=None, end_id=None, data_ids=None):
    if data_ids:
        selected_ids = {int(item_id) for item_id in data_ids}
        return [item for item in items if int(item["id"]) in selected_ids]

    if start_id is None and end_id is None:
        return items

    start_id = 1 if start_id is None else int(start_id)
    end_id = max(int(item["id"]) for item in items) if end_id is None else int(end_id)
    return [item for item in items if start_id <= int(item["id"]) <= end_id]


def ensure_example_workspace(workspace_base, example_id):
    directory = Path(workspace_base) / f"example_{example_id}"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def copy_benchmark_inputs(benchmark_dir, example_id, destination):
    benchmark_dir = resolve_benchmark_dir(benchmark_dir)
    source_dir = benchmark_dir / "data" / str(example_id)
    destination = Path(destination)

    if not source_dir.exists():
        return []

    copied_files = []
    for source_path in source_dir.iterdir():
        target_path = destination / source_path.name
        if source_path.is_dir():
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, target_path)
        copied_files.append(target_path)
    return copied_files
