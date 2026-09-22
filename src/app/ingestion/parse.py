from pathlib import Path
from pypdf import PdfReader
from lxml import html as lxml_html

import trafilatura
import hashlib
import json
import re

RAW_DIR = Path("data/raw")
PARSED_DIR = Path("data/parsed")
METADATA_PATH = Path("data/parsed_metadata.json")

MIN_TEXT_LENGTH = 1000

def text_hash(text: str) -> str:
    """Return a hash of the text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def fix_missing_word_boundaries(text:str) -> str:

    text = re.sub(r"(?<=[a-zäöüß])(?=[A-ZÄÖÜ])", " ", text)

    text = re.sub(r"(?<!\n)(?<!^)(#+\s)", r"\n\n\1", text)

    return text

def extract_h1_title(html: bytes) -> str | None:
    try:
        tree = lxml_html.fromstring(html)
    except:
        return None

    h1 = tree.find(".//h1")

    if h1 is None:
        return None

    pieces = [piece.strip() for piece in h1.itertext()]
    pieces = [piece for piece in pieces if piece]

    title = " ".join(pieces)

    return title or None

def parse_html(path: Path) -> str | None:

    html = path.read_bytes()

    text = trafilatura.extract(
        html,
        output_format="markdown",
        include_links=False,
        include_images=False,
    )

    if not text:
        return None

    text = fix_missing_word_boundaries(text)

    title = extract_h1_title(html)

    if not title:
        metadata =  trafilatura.extract_metadata(html) 
        title = metadata.title.strip() if metadata and metadata.title else None

    if title:
        # Check whether the extracted body already starts
        # with the same title.
        lines = text.splitlines()

        first_content_index = None

        for i, line in enumerate(lines):
            if line.strip():
                first_content_index = i
                break

        if first_content_index is not None:
            first_line = lines[first_content_index].strip()

            if first_line == title:
                # The title is already present in the body.
                # Convert it into a Markdown heading instead
                # of adding it a second time.
                lines[first_content_index] = f"# {title}"
                text = "\n".join(lines)

            else:
                # The title is missing from the body.
                # Add it as a Markdown heading.
                text = f"# {title}\n\n{text}"

        else:
            text = f"# {title}"

    return text



def parse_pdf(path: Path) -> str | None:
    reader = PdfReader(path)

    pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            pages.append(page_text)

    text = "\n\n".join(pages)

    return text if text.strip() else None

def main():
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    metadata = []

    for path in sorted(RAW_DIR.iterdir()):
        if path.suffix.lower() not in {".html",".pdf"}:
            continue

        try:
            if path.suffix.lower() == ".html":
                text = parse_html(path)
        
            else:
                text = parse_pdf(path)

        except Exception as e:
            print(f" Failed: {e}")

            metadata.append({
                "id": path.stem,
                "status": "failed",
                "character_count": 0,
                "text_hash": None,
                "output_path": None,
                "failure_reason": str(e),
            })
            continue

        if not text:
            print(f" Failed: No text extracted")
            metadata.append({
                "id": path.stem,
                "status": "failed",
                "character_count": 0,
                "text_hash": None,
                "output_path": None,
                "failure_reason": "No text extracted",
            })
            continue
        
        character_count =  len(text)
        hash_value = text_hash(text)

        print(f" Extracted characters: {len(text)}")
        print(f" Text hash: {hash_value}")


        if character_count < MIN_TEXT_LENGTH:
            print(
                f" REJECTED ONLY: {character_count} characters "
                f"(minimum: {MIN_TEXT_LENGTH})"
            )

            metadata.append({

                "id": path.stem,
                "status": "rejected",
                "character_count": character_count,
                "text_hash": hash_value,
                "output_path": None,
                "failure_reason": "below minimum text length",
            })
            continue

        output_path = PARSED_DIR / f"{path.stem}.txt"

        output_path.write_text(
            text, 
            encoding="utf-8",
        )

        print(f" Saved {output_path}")

        metadata.append({

            "id": path.stem,
            "status": "parsed",
            "character_count": len(text),
            "text_hash": hash_value,
            "output_path": str(output_path),
            "failure_reason": None,
        })

    METADATA_PATH.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), 
        encoding="utf-8",
    )

    print(f"\nMetadata saved to {METADATA_PATH}")

if __name__ == "__main__":
    main()