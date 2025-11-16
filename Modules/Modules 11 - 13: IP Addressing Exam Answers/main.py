#!/usr/bin/env python3

import re
import sys
import json
from html import unescape
import random


def strip_tags(text: str) -> str:
    # remove HTML tags
    return re.sub(r"<[^>]+>", "", text).strip()


def extract_questions(html: str):
    # find question headings like: <p><strong>1. Question text</strong></p>
    q_pattern = re.compile(
        r"<p>\s*<strong>\s*(\d+)\.\s*(.*?)</strong>\s*</p>", re.DOTALL | re.IGNORECASE
    )
    questions = []
    matches = list(q_pattern.finditer(html))

    for i, m in enumerate(matches):
        num = int(m.group(1))
        qtext_raw = m.group(2)
        qtext = strip_tags(qtext_raw)

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        snippet = html[start:end]

        # look for first <ul>...</ul> after the question
        ul_match = re.search(
            r"<ul(?: [^>]*)?>(.*?)</ul>", snippet, re.DOTALL | re.IGNORECASE
        )
        options = []
        correct = []
        if ul_match:
            ul_html = ul_match.group(1)
            # find all <li>...</li>
            li_items = re.findall(
                r"<li(?: [^>]*)?>(.*?)</li>", ul_html, re.DOTALL | re.IGNORECASE
            )
            for idx, li in enumerate(li_items):
                li_clean = strip_tags(li)
                li_clean = unescape(li_clean)
                options.append(li_clean)
                # detect correctness marker (red color or strong wrapped red)
                if re.search(
                    r"ff0000|color:\s*#ff0000|class=\"correct_answer\"",
                    li,
                    re.IGNORECASE,
                ):
                    correct.append(idx)
                else:
                    # sometimes bold alone indicates correct in this HTML (rare) — check for <strong> inside li raw
                    if re.search(r"<strong>.*?</strong>", li, re.DOTALL):
                        # if the strong contains the full answer text and appears to be highlighted, treat as correct
                        if re.search(r"ff0000", li, re.IGNORECASE):
                            correct.append(idx)

        # if no options found, try to capture answers given as plain text choices later (fallback)
        # Store correct answers by value instead of index
        correct_answers = (
            [options[idx] for idx in correct] if correct and options else []
        )

        questions.append(
            {
                "question": qtext,
                "options": options,
                "correct_answers": correct_answers,
            }
        )

    return questions


def randomize_question_options(question: dict) -> dict:
    """
    Randomize the order of options and update correct_answers to match new positions.
    """
    if not question["options"]:
        return question

    options = question["options"].copy()
    correct_answers = question["correct_answers"].copy()

    # Shuffle options with a seed for reproducibility (optional)
    combined = list(zip(options, [ans in correct_answers for ans in options]))
    random.shuffle(combined)

    shuffled_options, is_correct_flags = zip(*combined)
    question["options"] = list(shuffled_options)
    question["correct_answers"] = [opt for opt, is_correct in combined if is_correct]

    return question


def main():
    # Parse arguments
    path = None
    randomize = False

    for arg in sys.argv[1:]:
        if arg in ("--randomize", "-r"):
            randomize = True
        else:
            path = arg

    path = path or "ccna-1-v7-modules-11-13-ip-addressing-exam-answers-full.html"

    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print(f"HTML file not found: {path}", file=sys.stderr)
        sys.exit(1)

    data = extract_questions(html)

    # Randomize options if requested
    if randomize:
        data = [randomize_question_options(q) for q in data]

    # write JSON to output.json
    output_path = "output.json"
    try:
        with open(output_path, "w", encoding="utf-8") as out_f:
            json.dump(data, out_f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Failed to write output JSON: {e}", file=sys.stderr)
        sys.exit(1)
    # optionally inform the user
    print(f"Saved {len(data)} questions to {output_path}")

    

if __name__ == "__main__":
    main()
