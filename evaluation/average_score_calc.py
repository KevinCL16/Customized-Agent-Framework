import argparse
import json
from pathlib import Path
import re


def sanitize_label(value):
    return value.replace("/", "_").replace(":", "_").replace(".", "_").replace("-", "_")


def extract_last_score(log_contents, pattern):
    matches = re.findall(pattern, log_contents, re.DOTALL)
    if matches:
        return float(matches[-1])
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=str, default='./workspace')
    parser.add_argument('--start_id', type=int, default=1)
    parser.add_argument('--end_id', type=int, default=100)
    parser.add_argument('--generated_model_name', type=str, default='google/gemini-3-flash-preview')
    parser.add_argument('--eval_model', type=str, default='gpt-5.4')
    parser.add_argument('--score_type', type=str, default='legacy', choices=['legacy', 'rubric', 'combined'])
    parser.add_argument('--legacy_weight', type=float, default=0.5)
    parser.add_argument('--rubric_weight', type=float, default=0.5)
    args = parser.parse_args()

    workspace_dir = Path(args.workspace)
    all_scores = []
    label = f'{args.generated_model_name} novice {args.score_type}'
    legacy_log_name = f"eval_{sanitize_label(args.generated_model_name)}_by_{sanitize_label(args.eval_model)}.log"
    rubric_log_name = f"eval_rubric_{sanitize_label(args.generated_model_name)}_by_{sanitize_label(args.eval_model)}.log"
    legacy_pattern = r'\[FINAL SCORE\]: (\d{1,3}(?:\.\d+)?)'
    rubric_pattern = r'\[RUBRIC SCORE\]: (\d{1,3}(?:\.\d+)?)'

    for idx in range(args.start_id, args.end_id + 1):
        scores = {'id': idx}
        example_dir = workspace_dir / f'example_{idx}'

        legacy_score = None
        rubric_score = None

        legacy_log_path = example_dir / legacy_log_name
        if legacy_log_path.exists():
            with legacy_log_path.open('r', encoding='utf-8', errors='replace') as file:
                legacy_contents = file.read()
            legacy_score = extract_last_score(legacy_contents, legacy_pattern)

        rubric_log_path = example_dir / rubric_log_name
        if rubric_log_path.exists():
            with rubric_log_path.open('r', encoding='utf-8', errors='replace') as file:
                rubric_contents = file.read()
            rubric_score = extract_last_score(rubric_contents, rubric_pattern)

        if args.score_type == 'legacy':
            if legacy_score is not None:
                scores[label] = legacy_score
        elif args.score_type == 'rubric':
            if rubric_score is not None:
                scores[label] = rubric_score
        else:
            if legacy_score is not None and rubric_score is not None:
                combined_score = (args.legacy_weight * legacy_score) + (args.rubric_weight * rubric_score)
                scores[label] = combined_score

        all_scores.append(scores)

    output_path = workspace_dir / (
        f"automatic_eval_{args.score_type}_{sanitize_label(args.generated_model_name)}_by_"
        f"{sanitize_label(args.eval_model)}.json"
    )
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(all_scores, f, indent=4, ensure_ascii=False)

    total_scores = {}
    count = {}
    undone_list = []

    for entry in all_scores:
        if len(entry) > 1:
            for setting, score in entry.items():
                if setting == 'id':
                    continue
                if setting not in total_scores:
                    total_scores[setting] = 0
                    count[setting] = 0
                total_scores[setting] += score
                count[setting] += 1
        else:
            undone_list.append(entry['id'])

    average_scores = {
        setting: total_scores[setting] / count[setting]
        for setting in total_scores
        if count[setting] > 0
    }

    print('average scores:')
    print(average_scores)
    if undone_list:
        print('missing evaluation logs for ids:')
        print(undone_list)


if __name__ == "__main__":
    main()

