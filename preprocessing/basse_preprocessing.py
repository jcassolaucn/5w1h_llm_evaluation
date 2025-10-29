import json
from pathlib import Path


# # BASSE dataset
# Processes a JSONL file of summaries and returns a list of objects (dictionaries). Each object contains the index,
# the original document, and summaries from various models.
def get_list_of_objects_from_basse_dataset(filepath):
    """
    Processes a JSONL file of summaries and returns a list of objects (dictionaries).

    Args:
        filepath (str): The path to the .jsonl file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a processed JSON object.
    """
    data_list = []

    # Convert relative path to absolute path
    abs_path = Path(filepath).resolve()

    if not abs_path.exists():
        raise FileNotFoundError(f"The BASSE dataset file was not found at: {abs_path}\n"
                                f"Please ensure the file exists and the path is correct.")

    with open(abs_path, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, 1):
            try:
                json_object = json.loads(line.strip())

                idx = json_object.get('idx')
                round_val = json_object.get('round')
                original_document = json_object.get('original_document')

                model_summaries = json_object.get('model_summaries', {})

                claude_summ = model_summaries.get('claude-5w1h', {}).get('summ')
                commandr_summ = model_summaries.get('commandr-5w1h', {}).get('summ')
                gpt4o_summ = model_summaries.get('gpt4o-5w1h', {}).get('summ')
                reka_summ = model_summaries.get('reka-5w1h', {}).get('summ')
                llama3_summ = model_summaries.get('llama3-5w1h', {}).get('summ')

                data_list.append({
                    'idx': idx,
                    'round': round_val,
                    'original_document': original_document,
                    'claude-5w1h_summ': claude_summ,
                    'commandr-5w1h_summ': commandr_summ,
                    'gpt4o-5w1h_summ': gpt4o_summ,
                    'reka-5w1h_summ': reka_summ,
                    'llama3-5w1h_summ': llama3_summ
                })
            except json.JSONDecodeError:
                print(f"Warning (Line {line_number}): Skipped line (summaries) due to JSON decoding error: {line.strip()}")
            except Exception as e:
                print(f"Warning (Line {line_number}): Skipped line (summaries) due to an unexpected error ({e}): {line.strip()}")

    return data_list


# Process the JSONL file of summaries and generate a list of dictionaries.
def process_basse_summaries(jsonl_file_path_summaries):
    # Process the JSONL file of summaries
    list_of_summary_objects = get_list_of_objects_from_basse_dataset(jsonl_file_path_summaries)

    # Now 'list_of_summary_objects' is a list of dictionaries.
    if list_of_summary_objects:
        print("First object from the list of extractions:")
        print(json.dumps(list_of_summary_objects[0], indent=2, ensure_ascii=False))

    return list_of_summary_objects


# # -- USAGE EXAMPLE --
# # Path to the BASSE dataset summaries JSONL file
# basse_jsonl_file_path_summaries = '../data/basse/BASSE.jsonl'
# # Process the summaries JSONL file and generate a list of dictionaries.
# list_of_basse_summaries = process_basse_summaries(basse_jsonl_file_path_summaries)
# # Now 'list_of_basse_summaries' is a list of dictionaries,
# # and each dictionary has keys corresponding to the model summaries.
# # Print a summary of the result
# print(f"Processed {len(list_of_basse_summaries)} objects from the BASSE dataset.")
# if list_of_basse_summaries:
#     print("First object from the list of summaries (structure):")
#     print(json.dumps(list_of_basse_summaries[0], indent=2, ensure_ascii=False))