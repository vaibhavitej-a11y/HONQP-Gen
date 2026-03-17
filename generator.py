from __future__ import annotations

import argparse
import re
from typing import Dict, Iterable, List, Optional

_MODEL_NAME = "valhalla/t5-base-qg-hl"


def _require_spacy():
    try:
        import spacy  # type: ignore

        return spacy
    except ModuleNotFoundError as e:
        raise RuntimeError("Missing dependency: spacy. Install with: pip install spacy") from e


def _get_nlp() -> "spacy.language.Language":
    """
    Loads SpaCy English pipeline.

    Notes:
      - Requires: python -m spacy download en_core_web_sm
    """
    spacy = _require_spacy()
    try:
        return spacy.load("en_core_web_sm")
    except OSError as e:
        raise RuntimeError(
            "SpaCy model 'en_core_web_sm' is not installed. "
            "Install it with: python -m spacy download en_core_web_sm"
        ) from e


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_keywords(
    paragraph: str,
    *,
    nlp: "spacy.language.Language",
    max_keywords: int = 12,
    min_len: int = 3,
) -> List[str]:
    doc = nlp(paragraph)

    candidates: List[str] = []

    # Prefer named entities
    for ent in doc.ents:
        t = _normalize_ws(ent.text)
        if len(t) >= min_len:
            candidates.append(t)

    # Then noun chunks (key phrases)
    for chunk in doc.noun_chunks:
        t = _normalize_ws(chunk.text)
        if len(t) < min_len:
            continue
        # Skip chunks that are basically stopwords/punctuation
        if all(tok.is_stop or tok.is_punct or tok.like_num for tok in chunk):
            continue
        candidates.append(t)

    # Deduplicate, preserve order, avoid trivial repeats/casing variants
    seen = set()
    keywords: List[str] = []
    for c in candidates:
        k = c.casefold()
        if k in seen:
            continue
        seen.add(k)
        keywords.append(c)
        if len(keywords) >= max_keywords:
            break

    return keywords


_tokenizer = None
_model = None


def _require_transformers():
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore

        return AutoTokenizer, AutoModelForSeq2SeqLM
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Missing dependency: transformers (and torch). Install with: pip install transformers torch"
        ) from e


def _get_t5():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        AutoTokenizer, AutoModelForSeq2SeqLM = _require_transformers()
        # T5 uses SentencePiece; disabling the "fast" Rust tokenizer avoids occasional
        # Windows-specific tokenization crashes and also matches the model's expected setup.
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME, use_fast=False)
        _model = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_NAME)
    return _tokenizer, _model


def _highlight(paragraph: str, answer: str) -> str:
    # Highlight the first match (case-insensitive) if possible, else append answer highlighted.
    pat = re.compile(re.escape(answer), re.IGNORECASE)
    m = pat.search(paragraph)
    if not m:
        return f"{_normalize_ws(paragraph)} <hl> {answer} <hl>"
    return paragraph[: m.start()] + " <hl> " + paragraph[m.start() : m.end()] + " <hl> " + paragraph[m.end() :]


def _classify_question_type(question: str) -> str:
    q = question.strip().casefold()
    if "____" in question or "blank" in q:
        return "Fill in the blank"
    if q.startswith("which of the following") or q.startswith("choose") or q.startswith("select"):
        return "MCQ"
    return "Descriptive"


def _make_fill_in_blank(paragraph: str, answer: str) -> Optional[str]:
    """
    Creates a simple fill-in-the-blank question by replacing the answer
    in the paragraph with '____' (first occurrence only).
    """
    pat = re.compile(re.escape(answer), re.IGNORECASE)
    m = pat.search(paragraph)
    if not m:
        return None
    return _normalize_ws(paragraph[: m.start()] + "____" + paragraph[m.end() :])


def _make_mcq_options(answer: str, pool: List[str], *, max_options: int = 4) -> List[str]:
    """
    Makes basic MCQ options from other extracted keywords (no external knowledge).
    Ensures the answer is included.
    """
    opts: List[str] = []
    seen = set()

    def add(x: str):
        k = x.casefold()
        if not x or k in seen:
            return
        seen.add(k)
        opts.append(x)

    add(answer)
    for kw in pool:
        if len(opts) >= max_options:
            break
        if kw.casefold() == answer.casefold():
            continue
        add(kw)

    return opts


def _generate_one(
    highlighted_text: str,
    *,
    max_new_tokens: int = 64,
    num_beams: int = 4,
) -> str:
    tokenizer, model = _get_t5()
    inputs = tokenizer.encode(highlighted_text, return_tensors="pt", truncation=True)
    outputs = model.generate(
        inputs,
        max_new_tokens=max_new_tokens,
        num_beams=num_beams,
        early_stopping=True,
        no_repeat_ngram_size=3,
    )
    q = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return _normalize_ws(q)


def generate_questions(
    paragraph: str,
    *,
    max_questions: int = 10,
    max_keywords: int = 12,
) -> List[Dict[str, object]]:
    """
    Takes a paragraph, extracts keywords with SpaCy, then uses T5 QG-HL to generate questions.
    Returns a list of items with question, answer, and question type.
    """
    paragraph = _normalize_ws(paragraph)
    if not paragraph:
        return []

    nlp = _get_nlp()
    keywords = _extract_keywords(paragraph, nlp=nlp, max_keywords=max_keywords)
    if not keywords:
        return []

    results: List[Dict[str, object]] = []
    seen_questions = set()

    for kw in keywords:
        if len(results) >= max_questions:
            break
        inp = _highlight(paragraph, kw)
        q = _generate_one(inp)
        if not q:
            continue
        q = q if q.endswith("?") else (q + "?")
        key = q.casefold()
        if key in seen_questions:
            continue
        seen_questions.add(key)

        qtype = _classify_question_type(q)

        item: Dict[str, object] = {
            "question": q,
            "answer": kw,
            "type": qtype,
        }

        # If the model produced a descriptive question, also try to produce a fill-in-the-blank variant.
        if qtype == "Descriptive":
            fib = _make_fill_in_blank(paragraph, kw)
            if fib:
                item["fill_in_blank"] = fib

        # Always include simple MCQ options pool (answer + other keywords).
        item["options"] = _make_mcq_options(kw, keywords)

        results.append(item)

    return results


def _read_stdin_all() -> str:
    import sys

    return sys.stdin.read()


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate questions from a paragraph.")
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Paragraph text. If omitted, reads from stdin.",
    )
    parser.add_argument("--max-questions", type=int, default=10)
    parser.add_argument("--max-keywords", type=int, default=12)

    args = parser.parse_args(list(argv) if argv is not None else None)
    text = args.text if args.text is not None else _read_stdin_all()

    qs = generate_questions(text, max_questions=args.max_questions, max_keywords=args.max_keywords)
    for item in qs:
        print(item["question"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
