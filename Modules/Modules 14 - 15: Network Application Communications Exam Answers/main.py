
#!/usr/bin/env python3

import re
import sys
import json
from html import unescape
import random
import urllib.request



def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("–", "-")).strip()


def tag(name: str, closing: bool = False) -> str:
    """
    Build a regex fragment that matches either a real HTML tag <name ...>
    or an HTML-encoded tag &lt;name ...&gt;.
    If closing=True, matches closing tags </name> or &lt;/name&gt;.
    """
    if closing:
        return rf"(?:</{name}\s*>|&lt;/{name}\s*&gt;)"
    else:
        # opening tag, possibly with attributes
        return rf"(?:<{name}(?:\s+[^>]*?)?>|&lt;{name}(?:\s+[^&gt;]*?)?&gt;)"


def strip_tags(text: str) -> str:
    """
    Remove both real HTML tags and HTML-encoded tags from text.
    """
    # remove real HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # remove encoded tags like &lt;...&gt;
    text = re.sub(r"&lt;[^&gt;]+&gt;", "", text)
    return text.strip()


def extract_explanation(snippet: str):
    """
    Extracts the explanation text (without the 'Explanation:' label) from the
    snippet between the current question and the next one.

    It first tries a div with class containing 'message_box', then falls back
    to any paragraph that contains 'Explanation:' (case-insensitive).
    Returns the cleaned text or None.
    """
    # 1) Try message_box div (real or encoded)
    box_pattern = rf"{tag('div')}(?P<body>.*?){tag('div', closing=True)}"
    for m in re.finditer(box_pattern, snippet, re.DOTALL | re.IGNORECASE):
        # check if this div has class containing message_box
        full_opening = m.group(0)[: m.group(0).find(m.group('body'))]
        if re.search(r'class\s*=\s*"[^"]*message_box[^"]*"', full_opening, re.IGNORECASE):
            raw = m.group("body")
            cleaned = normalize_ws(unescape(strip_tags(raw)))
            # remove leading label
            lab = re.search(r'(?i)\bExplanation\s*:?\s*(.*)', cleaned, re.DOTALL)
            return lab.group(1).strip() if lab else cleaned.strip()

    # 2) Fallback: any <p> with "Explanation:"
    p_pattern = rf"{tag('p')}(?P<pbody>.*?){tag('p', closing=True)}"
    for pm in re.finditer(p_pattern, snippet, re.DOTALL | re.IGNORECASE):
        p_text_clean = normalize_ws(unescape(strip_tags(pm.group("pbody"))))
        m = re.search(r'(?i)\bExplanation\s*:?\s*(.*)', p_text_clean, re.DOTALL)
        if m:
            return m.group(1).strip()

    return None


def extract_questions(html: str):
    """
    Extract questions, options, correct answers, and (if present) explanation
    from HTML that may be either real or HTML-encoded.
    """
    # Normalize for safety (unescape entities into real text where possible)
    # but keep original string to match both forms robustly.
    # We'll primarily rely on dual-form regex patterns.
    questions = []

    # Pattern for question header: <p><strong>n. text</strong></p> (real or encoded)
    q_pattern = re.compile(
        rf"{tag('p')}\s*{tag('strong')}\s*(\d+)\.\s*(.*?)\s*{tag('strong', closing=True)}\s*{tag('p', closing=True)}",
        re.DOTALL | re.IGNORECASE,
    )
    matches = list(q_pattern.finditer(html))

    if not matches:
        # Optional debug: try a looser match to hint at what we saw
        print("No question headers matched. Check if your file uses a different structure.", file=sys.stderr)

    for i, m in enumerate(matches):
        num = int(m.group(1))
        qtext_raw = m.group(2)
        qtext = normalize_ws(unescape(strip_tags(qtext_raw)))

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        snippet = html[start:end]

        # Find first <ul>...</ul> (real or encoded) for options
        ul_match = re.search(
            rf"{tag('ul')}(?P<ulbody>.*?){tag('ul', closing=True)}",
            snippet,
            re.DOTALL | re.IGNORECASE,
        )

        options = []
        correct_idx = []
        if ul_match:
            ul_html = ul_match.group("ulbody")
            # Find all <li>...</li> items
            li_pattern = re.compile(
                rf"{tag('li')}(?P<li>.*?){tag('li', closing=True)}",
                re.DOTALL | re.IGNORECASE,
            )
            for idx, lim in enumerate(li_pattern.finditer(ul_html)):
                li_raw = lim.group("li")
                li_clean = normalize_ws(unescape(strip_tags(li_raw)))
                options.append(li_clean)

                # detect correctness via red color or explicit class
                # check on raw, so we can see inline styles/classes
                if re.search(r"ff0000|color\s*:\s*#?ff0000|class\s*=\s*\"correct_answer\"", li_raw, re.IGNORECASE):
                    correct_idx.append(idx)
                else:
                    # sometimes bold + red combinations; we keep red marker check
                    if re.search(r"(?:<|&lt;)strong(?:\s+[^>]*?)?(?:>|&gt;).*?(?:<|&lt;)/strong(?:>|&gt;)", li_raw, re.DOTALL | re.IGNORECASE):
                        if re.search(r"ff0000|color\s*:\s*#?ff0000", li_raw, re.IGNORECASE):
                            correct_idx.append(idx)

        correct_answers = [options[idx] for idx in correct_idx] if correct_idx and options else []

        # Try to extract an explanation for this question
        explanation = extract_explanation(snippet)

        q_obj = {
            "question": qtext,
            "options": options,
            "correct_answers": correct_answers,
        }
        if explanation:  # ONLY add the field if we found one
            q_obj["explanation"] = explanation

        questions.append(q_obj)

    return questions


def randomize_question_options(question: dict) -> dict:
    """
    Randomize the order of options while keeping correct answers by value.
    """
    if not question.get("options"):
        return question

    options = question["options"].copy()
    correct_answers = set(question.get("correct_answers", []))

    combined = [(opt, opt in correct_answers) for opt in options]
    random.shuffle(combined)

    question["options"] = [opt for opt, _ in combined]
    # keep correct answers as texts (unchanged)
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

    # Ask user for the URL
    url = input("Enter the URL of the CCNA page: ").strip()
    
    if not url:
        print("No URL provided.")
        return 
    
    # Download the HTML
    print("Downloading HTML...")
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print("Failed to download:", e)
        exit()

    with open("ccna.html", "w", encoding="utf-8") as f:
        f.write(html)
    

    path = path or "ccna.html"

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
    match = re.search(r"modules-(\d+-\d+)", path)
    module_range = match.group(1) if match else "unknown"

    output_path = f"ccna-1-v7-modules-{module_range}.json"

    try:
        with open(output_path, "w", encoding="utf-8") as out_f:
            json.dump(data, out_f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Failed to write output JSON: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved {len(data)} questions to {output_path}")


if __name__ == "__main__":
    main()
