import datetime
import os
import json

# Same module list as your scraper
SITES = {
    "1-3": "https://itexamanswers.net/ccna-1-v7-modules-1-3-basic-network-connectivity-and-communications-exam-answers.html",
    "4-7": "https://itexamanswers.net/ccna-1-v7-modules-4-7-ethernet-concepts-exam-answers.html",
    "8-10": "https://itexamanswers.net/ccna-1-v7-modules-8-10-communicating-between-networks-exam-answers.html",
    "11-13": "https://itexamanswers.net/ccna-1-v7-modules-11-13-ip-addressing-exam-answers-full.html",
    "14-15": "https://itexamanswers.net/ccna-1-v7-modules-14-15-network-application-communications-exam-answers.html",
    "16-17": "https://itexamanswers.net/ccna-1-v7-modules-16-17-building-and-securing-a-small-network-exam-answers.html",
}

INPUT_FILE = "templates/index.html"
CSS_FILE = "templates/styles.css"
JS_FILE = "templates/main.js"

YEAR_VALUE = str(datetime.datetime.now().year)


def build_module(module):
    json_path = f"Modules/CCNA_MODULES_{module}/ccna-1-v7-modules-{module}.json"
    output_path = f"Modules/CCNA_MODULES_{module}/index.html"

    if not os.path.exists(json_path):
        print(f"JSON missing for module {module}: {json_path}")
        return

    # Load template HTML
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Load CSS
    with open(CSS_FILE, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Load JS
    with open(JS_FILE, "r", encoding="utf-8") as f:
        js_content = f.read()

    # Load JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Pretty JSON
    json_string = json.dumps(json_data, indent=4)

    # Indent JSON for JS embedding
    indented_json = "\n".join(" " * 12 + line for line in json_string.splitlines())

    # Insert JSON into JS
    js_content = js_content.replace(" " * 12 + "{{ JSON_CONTENT }}", indented_json)

    # Replace placeholders in HTML
    content = content.replace("{{ MODULE }}", module)
    content = content.replace("{{ YEAR }}", YEAR_VALUE)

    # Inline CSS
    indented_css = "\n".join(" " * 8 + line for line in css_content.splitlines())
    content = content.replace(
        '<link rel="stylesheet" href="styles.css">',
        f"<style>\n{indented_css}\n    </style>",
    )

    # Inline JS
    indented_js = "\n".join(" " * 8 + line for line in js_content.splitlines())
    content = content.replace(
        '<script src="main.js"></script>',
        f"<script>\n{indented_js}\n    </script>",
    )

    # Ensure output folder exists
    os.makedirs(f"Modules/CCNA_MODULES_{module}", exist_ok=True)

    # Write final HTML
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Built HTML for module {module} -> {output_path}")


def main():
    print("Building HTML for all CCNA modules...\n")

    for module in SITES.keys():
        build_module(module)

    print("\nAll modules processed.")


if __name__ == "__main__":
    main()
