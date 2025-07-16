import json
from collections import defaultdict


# ---------------------------------------------------------------------------
# FUNCTION 1: Load, process, and merge datasets from files
# ---------------------------------------------------------------------------

def _process_flares_single_object(json_object):
    """
    (Internal Helper) Processes a single JSON object, enumerating its tags.
    """
    processed_object = {
        'Id': json_object.get('Id'),
        'Text': json_object.get('Text'),
        'Processed_Tags': []
    }
    tags = json_object.get('Tags', [])
    w5h1_label_counts = defaultdict(int)

    if tags:
        for tag_item in tags:
            original_w5h1_label = tag_item.get('5W1H_Label')
            processed_tag = {
                '5W1H_Label': original_w5h1_label,
                'Enumerated_Tag_Id': None,
                'Reliability_Label': tag_item.get('Reliability_Label'),
                'Tag_Text': tag_item.get('Tag_Text'),
                'Tag_Start': tag_item.get('Tag_Start')
            }
            if original_w5h1_label:
                w5h1_label_counts[original_w5h1_label] += 1
                current_count = w5h1_label_counts[original_w5h1_label]
                processed_tag['Enumerated_Tag_Id'] = f"{original_w5h1_label}_{current_count}"
            processed_object['Processed_Tags'].append(processed_tag)
    return processed_object


def _get_objects_from_jsonl(filepath):
    """
    (Internal Helper) Processes a JSONL file and returns a list of processed objects.
    """
    all_processed_objects = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, 1):
            try:
                json_object = json.loads(line.strip())
                processed_data = _process_flares_single_object(json_object)
                all_processed_objects.append(processed_data)
            except json.JSONDecodeError:
                print(
                    f"Warning (Line {line_number}): Skipped line due to JSON decoding error.")
            except Exception as e:
                print(f"Warning (Line {line_number}): Skipped line due to unexpected error ({e}).")
    return all_processed_objects


def load_and_merge_datasets(file_paths):
    """
    Loads data from a list of JSONL file paths, processes them, and
    merges them into a single dataset.

    Args:
        file_paths (list): A list of strings with the paths to the files.

    Returns:
        list: A list of dictionaries (merged_dataset) with the combined data.
    """
    merged_dataset = []
    for path in file_paths:
        merged_dataset.extend(_get_objects_from_jsonl(path))

    print(f"Processed and merged {len(merged_dataset)} objects from {len(file_paths)} file(s).")
    if merged_dataset:
        print("Example of the first object in 'merged_dataset':")
        print(json.dumps(merged_dataset[0], indent=2, ensure_ascii=False))

    return merged_dataset


# ---------------------------------------------------------------------------
# FUNCTION 2: Filter, select, and flatten the combined dataset
# ---------------------------------------------------------------------------

def _select_best_combination(list_of_objects):
    """
    (Internal Helper) Filters for each object the first 'reliable' tag of
    each required 5W1H type.
    """
    best_combinations_list = []
    REQUIRED_LABELS = {'WHO', 'WHAT', 'WHEN', 'WHERE'}

    for obj in list_of_objects:
        grouped_tags = defaultdict(list)
        for tag in obj.get('Processed_Tags', []):
            label = tag.get('5W1H_Label')
            if label:
                grouped_tags[label].append(tag)

        if not REQUIRED_LABELS.issubset(grouped_tags.keys()):
            continue

        best_tags_for_this_object = []
        is_complete_with_reliable = True
        for label in REQUIRED_LABELS:
            reliable_tags = [t for t in grouped_tags[label] if t.get('Reliability_Label') == 'confiable']
            if not reliable_tags:
                is_complete_with_reliable = False
                break
            reliable_tags.sort(key=lambda x: x['Tag_Start'])
            best_tags_for_this_object.append(reliable_tags[0])

        if is_complete_with_reliable:
            best_tags_for_this_object.sort(key=lambda x: x['Tag_Start'])
            new_object = {'Id': obj['Id'], 'Text': obj['Text'], 'Processed_Tags': best_tags_for_this_object}
            best_combinations_list.append(new_object)

    return best_combinations_list


def _flatten_objects(optimal_list):
    """
    (Internal Helper) Transforms a list of nested objects into a flat format.
    """
    flattened_list = []
    for obj in optimal_list:
        new_flattened_obj = {'Id': obj.get('Id'), 'Text': obj.get('Text')}
        for tag in obj.get('Processed_Tags', []):
            label = tag.get('5W1H_Label')
            if label:
                new_flattened_obj[label.title()] = tag.get('Tag_Text')
        flattened_list.append(new_flattened_obj)
    return flattened_list


def process_and_flatten_data(merged_dataset):
    """
    Takes the combined dataset, filters it to get the best 5W1H tag combination,
    and transforms it into a flat format.

    Args:
        merged_dataset (list): The list generated by load_and_merge_datasets.

    Returns:
        list: A list of dictionaries in flat format (final_flat_list).
    """
    # 1. Filter and select the best tag combination
    optimal_list = _select_best_combination(merged_dataset)
    print(f"\nAfter applying the 'best combination' filter, {len(optimal_list)} objects remained.")

    # 2. Flatten the resulting objects
    final_flat_list = _flatten_objects(optimal_list)
    print(f"Transformed {len(final_flat_list)} objects to flat format.")

    if final_flat_list:
        print("\nExample of the first object in 'final_flat_list':")
        print(json.dumps(final_flat_list[0], indent=2, ensure_ascii=False))

    return final_flat_list