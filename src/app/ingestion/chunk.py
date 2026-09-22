from pathlib import Path

import re
import hashlib
import json
import statistics
import yaml

PARSED_DIR = Path("data/parsed")
SOURCE_INVENTORY_PATH = Path("docs/m2-source-inventory.yaml")
FETCH_METADATA_PATH = Path("data/metadata.json")
CHUNKS_OUTPUT_PATH = Path("data/chunks.jsonl")

MAX_CHUNK_CHARS = 1000  
MIN_CHUNK_CHARS = 200
LEGAL_SOURCE_STEMS = {"9", "13"}
EXCLUDED_SOURCE_STEMS = {"6"}

def load_source_inventory() -> dict:
    with open(SOURCE_INVENTORY_PATH, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return {str(source["id"]): source for source in config["sources"]}


def load_fetch_metadata() -> dict:
    with open(FETCH_METADATA_PATH, "r", encoding="utf-8") as file:
        entries = json.load(file)

    return {str(entry["id"]): entry for entry in entries}


def chunk_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def build_chunk_record(
    chunk: dict,
    index: int,
    source_id: str,
    source_meta: dict,
    fetch_meta: dict,
) -> dict:
    embedded_text = build_chunk_text(chunk)

    return {
        "chunk_id": f"{source_id}_{index:03d}",
        "source_id": int(source_id),
        "url": fetch_meta.get("final_url") or source_meta.get("url"),
        "jurisdiction": source_meta.get("jurisdiction"),
        "authority_level": source_meta.get("authority_level"),
        "topics": source_meta.get("topic"),
        "language": source_meta.get("language"),
        "title": chunk["title"],
        "hierarchy": chunk["hierarchy"],
        "text": chunk["text"],
        "char_count": len(embedded_text),
        "text_hash": chunk_text_hash(embedded_text),
    }

def merge_small_sections(sections: list[dict]) -> list[dict]:

    result = []
    i = 0

    while i < len(sections):

        current = sections[i]

        # Already large enough.
        if len(current["text"]) >= MIN_CHUNK_CHARS:
            result.append(current)
            i += 1
            continue

        # Start with the small section.
        merged_text = current["text"]
        merged_hierarchy = [" > ".join(current["hierarchy"])]
        merged_title = [current["title"]]

        # Keep adding following sections until
        # the merged section reaches MIN.
        while (
            len(merged_text) < MIN_CHUNK_CHARS
            and i + 1 < len(sections)
        ):

            i += 1
            next_section = sections[i]

            merged_text = (
                merged_text
                + "\n\n"
                + next_section["text"]
            )

            # The last section becomes the representative title.
            merged_title.append(next_section["title"])
            merged_hierarchy.append(" > ".join(next_section["hierarchy"]))

        result.append({
            "title": " | ".join(merged_title),
            "hierarchy": [" | ".join(merged_hierarchy)],
            "text": merged_text.strip(),
        })

        i += 1

    return result

def split_sentences(text: str) -> list[str]: 
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def split_large_section(
    section: dict,
    max_chars: int = MAX_CHUNK_CHARS,
    overlap_chars: int = 150,
) -> list[dict]:

    sentences = split_sentences(section["text"])

    chunks = []
    current = []

    for sentence in sentences:

        candidate = current + [sentence]
        candidate_text = " ".join(candidate)

        if current and len(candidate_text) > max_chars:

            chunks.append({
                "title": section["title"],
                "hierarchy": section["hierarchy"],
                "text": " ".join(current),
            })

            # Keep trailing sentences for overlap.
            overlap = []
            overlap_length = 0

            for previous in reversed(current):

                if overlap_length + len(previous) > overlap_chars:
                    break

                overlap.insert(0, previous)
                overlap_length += len(previous)

            current = overlap + [sentence]

        else:
            current = candidate

    if current:
        chunks.append({
            "title": section["title"],
            "hierarchy": section["hierarchy"],
            "text": " ".join(current),
        })

    return chunks

def shorten_statute_prefix(title: str) -> str:
    match = re.search(r"\(([^()]*)\)\s*(§\s*\S+.*)$", title)

    if not match:
        return title

    abbreviation = match.group(1).split("-")[-1].strip()
    rest = match.group(2)

    return f"{abbreviation} {rest}"

def extract_legal_sections(text: str) -> list[dict]:
    parts = re.split(r"(?=^\(\d+\))", text, flags=re.MULTILINE)

    parts = [part.strip() for part in parts if part.strip()]

    if not parts:
        return []

    title = parts[0]

    # Remove markdown heading marker.
    if title.startswith("#"):
        title = title.lstrip("#").strip()

    title = shorten_statute_prefix(title)

    sections = []

    for part in parts[1:]:
        match = re.match(r"^\((\d+)\)", part)

        if not match:
            continue

        paragraph_number = match.group(1)

        sections.append({
            "title": f"{title} – Absatz {paragraph_number}",
            "hierarchy": [
                title,
                f"Absatz {paragraph_number}",
            ],
            "text": clean_text(part),
        })

    return sections


def parse_heading(line: str):
    clean_line = line.strip()

    if not clean_line.startswith("#"):
        return None

    level = len(clean_line) - len(clean_line.lstrip("#"))
    title = clean_line.lstrip("#").strip()

    if not title:
        return None

    return level, title


def build_hierarchy(
    heading_stack: list[tuple[int, str]],
    level: int,
    title: str
):
    while heading_stack and heading_stack[-1][0] >= level:
        heading_stack.pop()

    heading_stack.append((level, title))

    return [title for _, title in heading_stack]

def clean_text(text: str) -> str:
    lines = []

    for line in text.splitlines():
        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)


def extract_sections(text: str) -> list[dict]:

    sections = []

    heading_stack = []

    current_title = None
    current_hierarchy = []
    current_lines = []

    for line in text.splitlines():

        heading = parse_heading(line)

        if heading is not None:

            level, title = heading

            # Save previous section
            if current_lines:
                sections.append({
                    "title": current_title or "(untitled)",
                    "hierarchy": current_hierarchy or ["(untitled)"],
                    "text": clean_text("\n".join(current_lines)),
                })

            current_title = title
            current_lines = []

            current_hierarchy = build_hierarchy(
                heading_stack,
                level,
                title
            )

        else:
            stripped = line.strip()
            if stripped and not re.fullmatch(r"#+", stripped):
                current_lines.append(line)

    # Save final section
    if current_lines:
        sections.append({
            "title": current_title or "(untitled)",
            "hierarchy": current_hierarchy or ["(untitled)"],
            "text": clean_text("\n".join(current_lines)),
        })

    return sections


def build_chunk_text(section: dict) -> str:

    hierarchy = " > ".join(section["hierarchy"])

    return (
        f"{hierarchy}\n\n"
        f"{section['text']}"
    ).strip()

def inspect_small_sections(sections: list[dict]):

    for i, section in enumerate(sections):

        size = len(section["text"])

        if size < MIN_CHUNK_CHARS:

            print("=" * 70)
            print(f"INDEX: {i}")
            print(f"SIZE: {size}")
            print(f"TITLE: {section['title']}")

            print("\nTEXT:")
            print(section["text"])

            if i + 1 < len(sections):
                next_section = sections[i + 1]

                print(
                    f"\nNEXT: {next_section['title']} "
                    f"({len(next_section['text'])} chars)"
                )

            if i > 0:
                previous_section = sections[i - 1]

                print(
                    f"PREVIOUS: {previous_section['title']} "
                    f"({len(previous_section['text'])} chars)"
                )


def main():

    source_inventory = load_source_inventory()
    fetch_metadata = load_fetch_metadata()

    all_records = []

    for path in sorted(PARSED_DIR.glob("*.txt")):

        if path.stem in EXCLUDED_SOURCE_STEMS:
            print("\n" + "=" * 80)
            print(f"File: {path.name} — SKIPPED (excluded per ADR 0006)")
            print("=" * 80)
            continue

        print("\n" + "=" * 80)
        print(f"FILE: {path.name}")
        print("=" * 80)

        text = path.read_text(encoding="utf-8")

        if path.stem in LEGAL_SOURCE_STEMS:
            sections = extract_legal_sections(text)
        else:
            sections = extract_sections(text)

        print("RAW SECTIONS:", len(sections))

        if path.stem not in LEGAL_SOURCE_STEMS:
            sections = merge_small_sections(sections)

        print("AFTER MERGE:", len(sections))

        final_chunks = []

        for section in sections:
            embedded_text = build_chunk_text(section)

            if len(embedded_text) > MAX_CHUNK_CHARS and path.stem not in LEGAL_SOURCE_STEMS:
                hierarchy_line = " > ".join(section["hierarchy"])
                effective_max = MAX_CHUNK_CHARS - len(hierarchy_line) - 2

                chunks = split_large_section(section, max_chars=effective_max)
                final_chunks.extend(chunks)
            else:
                final_chunks.append(section)

        print("FINAL CHUNKS:", len(final_chunks))

        source_meta = source_inventory.get(path.stem, {})
        fetch_meta = fetch_metadata.get(path.stem, {})

        if not source_meta:
            print(f"  WARNING: no inventory entry for source {path.stem}")

        for i, chunk in enumerate(final_chunks):
            record = build_chunk_record(chunk, i, path.stem, source_meta, fetch_meta)
            all_records.append(record)

            print(f"  CHUNK {i}: {record['char_count']} chars | {record['title']}")

    with open(CHUNKS_OUTPUT_PATH, "w", encoding="utf-8") as file:
        for record in all_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(all_records)} chunks to {CHUNKS_OUTPUT_PATH}")

    print("\n" + "=" * 80)
    print("CHUNKS PER SOURCE")
    print("=" * 80)

    counts_by_source = {}
    for record in all_records:
        counts_by_source[record["source_id"]] = counts_by_source.get(record["source_id"], 0) + 1

    for source_id in sorted(counts_by_source):
        print(f"  source {source_id}: {counts_by_source[source_id]} chunks")

    print("\n" + "=" * 80)
    print("SIZE DISTRIBUTION (char_count = full embedded text, hierarchy included)")
    print("=" * 80)

    sizes = sorted(record["char_count"] for record in all_records)

    print(f"  count:  {len(sizes)}")
    print(f"  min:    {sizes[0]}")
    print(f"  max:    {sizes[-1]}")
    print(f"  mean:   {statistics.mean(sizes):.0f}")
    print(f"  median: {statistics.median(sizes):.0f}")

    buckets = {"<200": 0, "200-500": 0, "500-1000": 0, "1000-1500": 0, "1500+": 0}

    for size in sizes:
        if size < 200:
            buckets["<200"] += 1
        elif size < 500:
            buckets["200-500"] += 1
        elif size < 1000:
            buckets["500-1000"] += 1
        elif size < 1500:
            buckets["1000-1500"] += 1
        else:
            buckets["1500+"] += 1

    for label, count in buckets.items():
        print(f"  {label}: {count}")

    print("\n" + "=" * 80)
    print("CHUNKS EXCEEDING MAX_CHUNK_CHARS")
    print("=" * 80)

    oversized = [r for r in all_records if r["char_count"] > MAX_CHUNK_CHARS]

    if not oversized:
        print("  none")
    else:
        for record in oversized:
            print(f"  {record['chunk_id']}: {record['char_count']} chars | {record['title']}")


if __name__ == "__main__":
    main()