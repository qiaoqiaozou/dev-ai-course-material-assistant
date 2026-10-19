# Evaluation Results Summary



## Summary Overview

- **Date of Evaluation:** 2026-10-19
- **Model Evaluated:** `qwen3:8b` and `qwen3.5:2b`
- **Total Test Cases Executed:** 6
- **Passed:** 5
- **Failed:** 1
- **Pass Rate:** 83.3%
  
We asked each model the same three questions.
Each question started with an empty chat history.

The numbers above are based on our manual review.
One answer was not complete, so we marked it as failed.

The evaluation button showed "true" for all six answers.
It checked the response status, source links, and citations.
It did not check whether the answer included every required item.
We found the missing item by reading the answer and the source.

We also ran 8 automated tests with `python -m pytest`.
All 8 tests passed. These tests are separate from the 6 model answers.


## Performance by Category

| Category | Total Cases | Passed | Failed | Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| Successful Cases | 2 | 2 | 0 | 100% |
| Difficult Cases | 2 | 1 | 1 | 50% |
| Failure / Edge Cases | 2 | 2 | 0 | 100% |

- Successful case: "What is retrieval-augmented generation?"
- Difficult case: "What must be included in the final project submission?"
- Failure / edge case: "What is today's cafeteria menu?"

Each question was tested with both models, so each category has two results.
For the cafeteria question, a pass means the app says it has no information.
It must not invent a menu.

## Key Findings & Failure Analysis

### What worked well
- Both models gave a correct answer about RAG.
- Both models used a relevant course source for the RAG answer.
- `qwen3:8b` listed all six required project-submission items.
- Both models said the course documents had no cafeteria menu.
- Both cafeteria answers had no citations.
- We read the answers and sources to check relevance, source quality,
  answer correctness, and citation support.
- The sources were from the official course website.


### Automated tests

The starter project had 5 tests.
We added 3 tests because RAG introduced source citations.

The new tests check that:

1. An answer marked "supported" cannot have an empty citation list.
2. An answer marked "insufficient" cannot include citations.
3. A citation must refer to an evidence passage that exists.
   For example, citation [2] is not allowed when only passage [1] is supplied.

These tests use fixed evidence and fake model replies.
They check our program rules, not the quality of a real model answer.

All 8 tests passed.

### Observed failure modes

- `qwen3.5:2b` missed "limitations" when listing the final project
  requirements. We marked this answer as failed because it was incomplete.
- The cited source included this item. This means retrieval found the
  needed information, but the model left it out of the answer.
  We do not know the exact reason.
- The evaluation button still showed "true". It checks the response status,
  source links, and citations, but not whether every required item is included.
  We found the missing item by reading the answer and comparing it with the source.
- Earlier tests also showed wrong categories and missing citations.
  The app rejects supported answers with no citations, but it cannot
  guarantee that every answer is complete or correctly classified.

## Action Items & Improvements
- [x] Add 3 tests to check missing, unexpected, and invalid citations.
- [x] Run the same 3 evaluation cases with 2 models.
- [x] Read the answers and compare them with the cited sources.
- [x] Compare the results after changing the model.
- [ ] Run the same cases again after future changes.
- [ ] Keep manual review because automatic checks can miss wrong or incomplete answers.
