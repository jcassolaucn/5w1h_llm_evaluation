def prepare_basse_tasks(doc_entry: dict):
    """
    Generator that yields evaluation tasks from a BASSE dataset entry.
    An entry can yield multiple tasks (one per model summary).
    """
    doc_id = doc_entry["idx"]
    original_text = doc_entry["original_document"]
    summary_keys = [key for key in doc_entry if key.endswith('_summ')]

    for key in summary_keys:
        model_name = key.replace('-5w1h_summ', '')
        summary_to_evaluate = doc_entry[key]
        # Yield a standardized task tuple
        yield doc_id, original_text, summary_to_evaluate, model_name
