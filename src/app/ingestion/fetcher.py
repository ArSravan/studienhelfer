import hashlib
import json
import mimetypes

import requests
import yaml

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

SOURCE_FILE = BASE_DIR / "docs/m2-source-inventory.yaml"
RAW_DATA_DIR = BASE_DIR / "data/raw"
METADATA_FILE = BASE_DIR / "data/metadata.json"

def get_extension(content_type):
    content_type = content_type.split(";")[0].strip().lower()

    if content_type == "application/pdf":
        return ".pdf"
    if content_type == "text/html":
        return ".html"
    if content_type == "text/plain":
        return ".txt"

    extension = mimetypes.guess_extension(content_type)

    if extension:
        return extension
    return ".bin"

def load_metadata():
    if not METADATA_FILE.exists():
        return []

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def find_previous_source(metadata, source_id):
    for item in metadata:
        if item["id"] == source_id:
            return item
    return None

def validate_content(content, expected_format, content_type):

    content_type = content_type.split(";")[0].strip().lower()
    sample = content[:4096].lstrip().lower()

    if expected_format == "pdf":
        return content.startswith(b"%PDF-")

    if expected_format == "html":
        if content_type in ("text/html", "application/xhtml+xml"):
            return True

        return (
            sample.startswith(b"<!doctype html")
            or sample.startswith(b"<html")
            or b"<html" in sample[:1024]
        )

    if expected_format == "txt":
        try:
            content.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False
    return False

def fetch_sources(source, previous_metadata):
    source_id = source["id"]
    url = source["url"]

    previous_source = find_previous_source(
        previous_metadata,
        source_id,
    )

    print(f"\nFetching: {source_id}")
    print(f"URL: {url}")

    try:
        response = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": (
                    "studienhelfer/0.1 "
                    "(educational project)"
                ),
                 "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7"
                ),
            },
        )
        response.raise_for_status()

        print(f"Status: {response.status_code}")

        content_type = response.headers.get(
            "Content-Type",
            "application/octet-stream",
        )

        expected_format = source.get("format")

        if not validate_content(
            response.content,
            expected_format,
            content_type,
        ):
            print(
                f"Failed: expected {expected_format},"
                f"but response content does not match"
            )

            print(f"Final URL: {response.url}")
            print(f"Content-Type: {content_type}")
            print(f"First bytes: {response.content[:100]!r}")

            return {
                "id": source_id,
                "url": url,
                "status": "failed",
                "error": (
                    f"Response does not match expected format"
                    f"'{expected_format}'"
                ),
                "final_url": response.url,
                "content_type": content_type,
            }
        content_hash = hashlib.sha256(response.content).hexdigest()

        print(f"SHA-256: {content_hash}")

        if previous_source is not None:
            old_hash = previous_source.get("sha256")

            if old_hash == content_hash:
                previous_path = previous_source.get("path")

                if previous_path:
                    previous_file = BASE_DIR / previous_path

                    if previous_file.exists():
                        print("UNCHANGED - SKIP")
                        return previous_source
        
                print("UNCHANGED HASH - FILE MISSING, RE-SAVING") 

        extension = get_extension(content_type)

        path = RAW_DATA_DIR / f"{source_id}{extension}"

        with open(path, "wb") as file:  
            file.write(response.content)

        print(f"Saved: {path}")

        return {
             "id": source_id,
             "url": url,
             "final_url": response.url,
             "status": "success",
             "content_type": content_type,
             "path": path.relative_to(BASE_DIR).as_posix(),
             "sha256": content_hash,

        }
    except requests.exceptions.RequestException as error:
        status_code = (
            error.response.status_code
            if error.response is not None
            else None
        )

        print(f"FAILED HTTP {status_code}: {error}")

        return {
              "id": source_id,
              "url": url,
              "status": "failed",
              "error": str(error),
         }

def main():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(SOURCE_FILE, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    sources = config["sources"]

    print(f"Found {len(sources)} sources.")

    previous_metadata = load_metadata()

    metadata = []

    for source in sources:
        result = fetch_sources(
            source,
            previous_metadata,
        )
        metadata.append(result)

    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nRun Complete. ")
    print(f"Metadata saved to : {METADATA_FILE}")

if __name__ == "__main__":
    main()