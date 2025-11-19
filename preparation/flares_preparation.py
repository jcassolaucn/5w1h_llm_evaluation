def prepare_flares_tasks(doc_entry: dict):
    """
    Generator that yields an evaluation task from a FLARES dataset entry.
    An entry yields only one task.
    """
    doc_id = doc_entry["Id"]
    original_text = doc_entry["Text"]
    model_name = "flares_ground_truth"
    extraction_to_evaluate = f"""
                        Qué: {doc_entry.get("What", "No especificado")}
                        Quién: {doc_entry.get("Who", "No especificado")}
                        Cuándo: {doc_entry.get("When", "No especificado")}
                        Dónde: {doc_entry.get("Where", "No especificado")}
                        Por qué: {doc_entry.get("Why", "No especificado")}
                        Cómo: {doc_entry.get("How", "No especificado")}
                        """.strip()
    # Yield a standardized task tuple
    yield doc_id, original_text, extraction_to_evaluate, model_name
