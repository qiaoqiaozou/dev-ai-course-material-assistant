from src.services.ai_service import generate_response


EVALUATION_CASES = [
    {
        "case": "course concept",
        "question": "What is retrieval-augmented generation?",
        "expected_evidence_status": "supported",
        "expected_paths": [
            "/docs/chapters/02-reliable-model-interaction",
            "/docs/chapters/04-grounding-and-rag",
        ],
    },
    {
        "case": "project submission",
        "question": "What must be included in the final project submission?",
        "expected_evidence_status": "supported",
        "expected_paths": [
            "/docs/project/submission",
        ],
    },
    {
        "case": "insufficient evidence",
        "question": "What is today's cafeteria menu?",
        "expected_evidence_status": "insufficient",
        "expected_paths": [],
    },
]


def run_quick_evaluation(model_id):
    rows = []

    for case in EVALUATION_CASES:
        result = generate_response(
            case["question"],
            history=[],
            model_id=model_id,
        )

        status_ok = (
            result.success
            and result.evidence_status == case["expected_evidence_status"]
        )

        if case["expected_evidence_status"] == "supported":
            source_ok = any(
                source["url"].rstrip("/").endswith(path)
                for source in result.sources
                for path in case["expected_paths"]
            )

            citation_ok = (
                bool(result.citations)
                and len(result.citations) == len(result.sources)
            )
        else:
            source_ok = not result.sources
            citation_ok = (
                not result.citations
                and result.needs_human is True
            )

        automatic_pass = status_ok and source_ok and citation_ok

        source_text = "\n\n".join(
            f"[{number}] {source['title']}\n"
            f"{source['url']}\n"
            f"{source['text']}"
            for number, source in zip(result.citations, result.sources)
        )

        rows.append([
            case["case"],
            case["question"],
            result.evidence_status if result.success else "error",
            automatic_pass,
            result.content,
            source_text or "No cited sources.",
            result.elapsed_s,
        ])

    return rows