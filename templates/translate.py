import json
import ollama

SITES = {
    "1-3": "https://itexamanswers.net/ccna-1-v7-modules-1-3-basic-network-connectivity-and-communications-exam-answers.html",
    "4-7": "https://itexamanswers.net/ccna-1-v7-modules-4-7-ethernet-concepts-exam-answers.html",
    "8-10": "https://itexamanswers.net/ccna-1-v7-modules-8-10-communicating-between-networks-exam-answers.html",
    "11-13": "https://itexamanswers.net/ccna-1-v7-modules-11-13-ip-addressing-exam-answers-full.html",
    "14-15": "https://itexamanswers.net/ccna-1-v7-modules-14-15-network-application-communications-exam-answers.html",
    "16-17": "https://itexamanswers.net/ccna-1-v7-modules-16-17-building-and-securing-a-small-network-exam-answers.html",
}

_translation_cache = {}


def translate_ollama(text, model="gemma3:4b-it-qat"):
    if not text.strip():
        return text

    if text.isdigit():
        return text

    if text in _translation_cache:
        return _translation_cache[text]

    prompt = (
        "You are a professional translation engine specialized in Cisco CCNA, networking, "
        "and transport-layer terminology.\n"
        "Translate the input text to German using the following strict rules:\n\n"
        "GENERAL RULES\n"
        "- Return ONLY the translated text. No explanations, no comments, no labels, no quotes.\n"
        "- Do NOT convert numbers into German words. Keep all numbers exactly as they appear.\n"
        "- Preserve technical meaning precisely. Do NOT invent synonyms or reinterpret terms.\n"
        "- Keep protocol names, flags, and acronyms unchanged (TCP, UDP, HTTP, ACK, SYN, FIN, SMB, DNS, etc.).\n"
        "- Translate consistently and literally, not creatively.\n\n"
        "NETWORKING TERMINOLOGY RULES\n"
        "Use the correct German technical terms for networking concepts. Examples:\n"
        '- "Source Port" → "Quellport"\n'
        '- "Destination Port" → "Zielport"\n'
        '- "Length" → "Länge"\n'
        '- "Checksum" → "Prüfsumme"\n'
        '- "Acknowledgment Number" → "Bestätigungsnummer"\n'
        '- "Sequence Number" → "Sequenznummer"\n'
        '- "Window Size" → "Fenstergröße"\n'
        '- "3-way handshake" → "3-Wege-Handshake"\n'
        '- "segment" → "Segment"\n'
        '- "datagram" → "Datagramm"\n'
        '- "socket" → "Socket"\n'
        '- "transport layer" → "Transportschicht"\n'
        '- "application layer" → "Anwendungsschicht"\n'
        '- "session establishment" → "Sitzungsaufbau"\n'
        '- "reliable delivery" → "zuverlässige Zustellung"\n\n'
        "Incorrect translations to avoid:\n"
        '- "Source Port" ≠ "Rückwärtsport"\n'
        '- "Length" ≠ "Die Rückgabe"\n'
        '- "Acknowledgment Number" ≠ "Aktenzeichen"\n'
        '- "1 segment" must stay "1 Segment" (NOT "Ein Segment")\n\n'
        "STYLE RULES\n"
        "- Keep the tone technical and concise.\n"
        "- Do not add punctuation that was not present.\n"
        "- Do not reorder or summarize content.\n\n"
        f"INPUT:\n{text}"
    )

    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])

    translated = response["message"]["content"].strip()
    _translation_cache[text] = translated
    return translated


def translate_and_print(text):
    translated = translate_ollama(text)
    print(text)
    print(translated)
    print()
    return translated


def walk(obj, translate_func):
    if isinstance(obj, dict):
        return {k: walk(v, translate_func) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(i, translate_func) for i in obj]
    if isinstance(obj, str):
        return translate_func(obj)
    return obj


if __name__ == "__main__":
    for module_range in SITES.keys():
        input_file = (
            f"Modules/CCNA_MODULES_{module_range}/ccna-1-v7-modules-{module_range}.json"
        )
        output_file = f"Modules/CCNA_MODULES_{module_range}/ccna-1-v7-modules-{module_range}-de.json"

        print(f"\n=== Translating module {module_range} ===")
        print(f"Input:  {input_file}")
        print(f"Output: {output_file}\n")

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Skipping {module_range}: file not found.")
            continue

        translated = walk(data, translate_and_print)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)

        print(f"Finished module {module_range}\n")
