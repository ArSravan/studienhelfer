from pathlib import Path

import trafilatura
import hashlib

RAW_DIR = Path("data/raw")
PARSED_DIR = Path("data/parsed")

MIN_TEXT_LENGTH = 1000

def text_hash(text: str) -> str:
    """Return a hash of the text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def parse_html(path: Path) -> str | None:

    try:
        html = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f" UTF-8 failed for {path.name}, trying cp1252...")
        html = path.read_text(encoding="cp1252")

    return trafilatura.extract(
        html,
        include_links=False,
        include_images=False,
    )

def main():
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    for path in RAW_DIR.glob("*.html"):
        print(f"Parsing {path.name}...")

        text = parse_html(path)

        if not text:
            print(f" Warning: no text extracted")
            continue
        
        if len(text) < MIN_TEXT_LENGTH:
            print(
                f" REJECTED: {path.name} "
                f"extracted only {len(text)} characters "
                f"(minimum: {MIN_TEXT_LENGTH})"
            )
            continue


        print(f" Extracted characters: {len(text)}")
        print(f" Text hash: {text_hash(text)}")

        output_path = PARSED_DIR / f"{path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")

        print(f" Saved {output_path}")

if __name__ == "__main__":
    main()