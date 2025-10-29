import json

def create_expert_review_task(
    doc_id: str,
    model_name: str,
    original_text: str,
    extraction_to_evaluate,
    evaluation_object
):
    """
    Builds the expert review task structure from evaluation results.
    """
    scores_dict = evaluation_object.scores.model_dump()
    justifications_dict = evaluation_object.justifications.model_dump()
    confidence_level_dict = evaluation_object.confidence_level.model_dump()

    # 1. Build the nested judgments object for expert review
    judgments_to_review = {
        criterion: {
            "ai_score": scores_dict[criterion],
            "ai_justification": justifications_dict[criterion],
            "expert_feedback": {
                "score_validity_1_to_5": " ",
                "explanation_quality": " ",
                "optional_notes": " "
            },
        }
        for criterion in scores_dict.keys()
    }

    # 2. Build the unique review object containing everything
    extraction_str = (
        json.dumps(extraction_to_evaluate, indent=2, ensure_ascii=False)
        if isinstance(extraction_to_evaluate, dict)
        else extraction_to_evaluate
    )

    review_task = {
        "review_id": f"{doc_id}_{model_name}",
        "document_info": {
            "doc_id": doc_id,
            "full_source_text": original_text,
        },
        "extraction_info": {
            "model_evaluated": model_name,
            "extraction_to_evaluate": extraction_str,
        },
        "confidence_level": {
            "score": confidence_level_dict["score"],
            "justification": confidence_level_dict["justification"],
        },
        "judgments_to_review": judgments_to_review,
    }

    return review_task