from pydantic import BaseModel, Field


class Scores(BaseModel):
    """Contains numerical scores for each evaluation criterion."""

    factual_accuracy: int = Field(
        ...,
        description="Score (1–5) for: Is the extracted information correct and does it faithfully reflect the facts presented in the source text?",
        ge=1,  # ge = Greater than or equal to 1
        le=5   # le = Less than or equal to 5
    )

    completeness: int = Field(
        ...,
        description="Score (1–5) for: Does the extraction capture all essential information from the source text that answers the specific 5W1H question?",
        ge=1,
        le=5
    )

    relevance_and_conciseness: int = Field(
        ...,
        description="Score (1–5) for: Does the extraction focus only on the answer, avoiding superfluous information or content that would belong to another 5W1H element?",
        ge=1,
        le=5
    )

    clarity_and_readability: int = Field(
        ...,
        description="Score (1–5) for: Is the extracted segment grammatically correct, coherent, and easy to understand on its own?",
        ge=1,
        le=5
    )

    source_faithfulness: int = Field(
        ...,
        description="Score (1–5) for: Is the extraction strictly based on the source text information, without adding interpretations or hallucinations?",
        ge=1,
        le=5
    )

    overall_coherence: int = Field(
        ...,
        description="Score (1–5) for: When considering all extractions together, do they form a logically connected and coherent set?",
        ge=1,
        le=5
    )


class Justifications(BaseModel):
    """Contains textual justifications for each assigned score."""

    factual_accuracy: str = Field(
        ...,
        description="Brief justification for the Factual Accuracy score."
    )

    completeness: str = Field(
        ...,
        description="Brief justification for the Completeness score."
    )

    relevance_and_conciseness: str = Field(
        ...,
        description="Brief justification for the Relevance and Conciseness score."
    )

    clarity_and_readability: str = Field(
        ...,
        description="Brief justification for the Clarity and Readability score."
    )

    source_faithfulness: str = Field(
        ...,
        description="Brief justification for the Source Faithfulness score."
    )

    overall_coherence: str = Field(
        ...,
        description="Brief justification for the Overall Coherence score."
    )

class ConfidenceLevel(BaseModel):
    """
    Contains the confidence level for the source text.
    """
    score: int = Field(
        ...,
        description="Score (1-5) for: The suitability of the source for a a 5W1H extraction.",
        ge=1,
        le=5
    )

    justification: str = Field(
        ...,
        description="Brief justification for the Confidence Level score (e.g 'The text is an editorial, not a news story')."
    )


class DetailedEvaluation(BaseModel):
    """
    Root model for a structured and detailed evaluation of a 5W1H extraction,
    based on a set of research-driven metrics.
    """
    scores: Scores = Field(..., description="The set of all numerical scores for the evaluation.")
    justifications: Justifications = Field(..., description="The set of all textual justifications supporting the scores.")
    confidence_level: ConfidenceLevel = Field(..., description="The confidence level for the source text.")