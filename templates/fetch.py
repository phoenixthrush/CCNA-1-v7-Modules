import re
import sys
import json
import os
import urllib.request
from html import unescape

SITES = {
    "1-3": "https://itexamanswers.net/ccna-1-v7-modules-1-3-basic-network-connectivity-and-communications-exam-answers.html",
    "4-7": "https://itexamanswers.net/ccna-1-v7-modules-4-7-ethernet-concepts-exam-answers.html",
    "8-10": "https://itexamanswers.net/ccna-1-v7-modules-8-10-communicating-between-networks-exam-answers.html",
    "11-13": "https://itexamanswers.net/ccna-1-v7-modules-11-13-ip-addressing-exam-answers-full.html",
    "14-15": "https://itexamanswers.net/ccna-1-v7-modules-14-15-network-application-communications-exam-answers.html",
    "16-17": "https://itexamanswers.net/ccna-1-v7-modules-16-17-building-and-securing-a-small-network-exam-answers.html",
}

# -----------------------------
# Precompiled regex patterns
# -----------------------------

TAG_REAL = re.compile(r"<[^>]+>")
TAG_ENCODED = re.compile(r"&lt;[^&gt;]+&gt;")

EXPLANATION_LABEL = re.compile(r"(?i)\bExplanation\s*:?\s*(.*)", re.DOTALL)

RED_MARKER = re.compile(
    r"ff0000|color\s*:\s*#?ff0000|class\s*=\s*\"correct_answer\"",
    re.IGNORECASE,
)

STRONG_RED = re.compile(
    r"(?:<|&lt;)strong(?:\s+[^>]*?)?(?:>|&gt;).*?(?:<|&lt;)/strong(?:>|&gt;)",
    re.DOTALL | re.IGNORECASE,
)

QUESTION_HEADER = re.compile(
    r"(?:<p>|&lt;p&gt;)\s*(?:<strong>|&lt;strong&gt;)\s*(\d+)\.\s*(.*?)\s*(?:</strong>|&lt;/strong&gt;)\s*(?:</p>|&lt;/p&gt;)",
    re.DOTALL | re.IGNORECASE,
)

UL_PATTERN = re.compile(
    r"(?:<ul[^>]*>|&lt;ul[^&gt;]*&gt;)(.*?)(?:</ul>|&lt;/ul&gt;)",
    re.DOTALL | re.IGNORECASE,
)

LI_PATTERN = re.compile(
    r"(?:<li[^>]*>|&lt;li[^&gt;]*&gt;)(.*?)(?:</li>|&lt;/li&gt;)",
    re.DOTALL | re.IGNORECASE,
)

MESSAGE_BOX = re.compile(
    r"(?:<div[^>]*message_box[^>]*>|&lt;div[^&gt;]*message_box[^&gt;]*&gt;)(.*?)(?:</div>|&lt;/div&gt;)",
    re.DOTALL | re.IGNORECASE,
)

# -----------------------------
# Utility functions
# -----------------------------


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("–", "-")).strip()


def strip_tags(text: str) -> str:
    text = TAG_REAL.sub("", text)
    text = TAG_ENCODED.sub("", text)
    return text.strip()


def clean(text: str) -> str:
    return normalize_ws(unescape(strip_tags(text)))


# -----------------------------
# Explanation extraction
# -----------------------------


def extract_explanation(snippet: str):
    box = MESSAGE_BOX.search(snippet)
    if box:
        body = clean(box.group(1))
        m = EXPLANATION_LABEL.search(body)
        return m.group(1).strip() if m else body

    for p in re.findall(
        r"(?:<p>|&lt;p&gt;)(.*?)(?:</p>|&lt;/p&gt;)", snippet, re.DOTALL
    ):
        text = clean(p)
        m = EXPLANATION_LABEL.search(text)
        if m:
            return m.group(1).strip()

    return None


# -----------------------------
# Main extraction
# -----------------------------


def extract_questions(html: str):
    questions = []
    matches = list(QUESTION_HEADER.finditer(html))

    for i, m in enumerate(matches):
        qtext = clean(m.group(2))

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        snippet = html[start:end]

        options = []
        correct_idx = []

        ul = UL_PATTERN.search(snippet)
        if ul:
            ul_body = ul.group(1)

            for idx, li in enumerate(LI_PATTERN.findall(ul_body)):
                raw = li
                text = clean(raw)
                options.append(text)

                if RED_MARKER.search(raw) or (
                    STRONG_RED.search(raw) and RED_MARKER.search(raw)
                ):
                    correct_idx.append(idx)

        correct_answers = [options[i] for i in correct_idx]

        explanation = extract_explanation(snippet)

        q_obj = {
            "question": qtext,
            "options": options,
            "correct_answers": correct_answers,
        }
        if explanation:
            q_obj["explanation"] = explanation

        questions.append(q_obj)

    return questions


# -----------------------------
# Main
# -----------------------------


def main():
    print("Fetching all CCNA module pages...")

    for module, url in SITES.items():
        print(f"\n=== Processing module {module} ===")
        print(f"Downloading: {url}")

        try:
            with urllib.request.urlopen(url) as r:
                html = r.read().decode("utf-8")
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            continue

        questions = extract_questions(html)

        # Output directory
        out_dir = f"Modules/CCNA_MODULES_{module}"
        os.makedirs(out_dir, exist_ok=True)

        out_path = f"{out_dir}/ccna-1-v7-modules-{module}.json"

        with open(out_path, "w", encoding="utf-8") as out:
            json.dump(questions, out, indent=2, ensure_ascii=False)

        print(f"Saved {len(questions)} questions -> {out_path}")

    print("\nAll modules processed.")


if __name__ == "__main__":
    main()
