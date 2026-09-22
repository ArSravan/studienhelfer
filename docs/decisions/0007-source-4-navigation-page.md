# ADR 0007: Source 4 (Bauen und Wohnen Overview Page) Kept Despite Being a Navigation Page

- Status: Accepted
- Date: 2026-09-15
- Decision: Keep source 4 (`data/parsed/4.txt`) in the ingestion pipeline as-is, rather than dropping it or deep-crawling the individual service pages it links to.

## Context

Source 4 is listed in `docs/m2-source-inventory.yaml` as:

```yaml
- id: 4
  title: "City Registration / Anmeldung"
  url: "https://serviceportal.hannover-stadt.de/buergerservice/lebenslagen/bauen-und-wohnen-900000157-0.html"
  topic:
    - city_registration
    - anmeldung
  authority_level: "primary"
```

The fetched page, however, is not an article about Anmeldung. It is the "Bauen und Wohnen" (Building and Housing) landing page of the Hannover service portal — a flat directory of roughly 50 short teaser blurbs, one per linked service, each 1-3 sentences long and frequently cut off with "...". Examples of unrelated topics on the same page include Abfallgebühr (waste fees), Baumschutzsatzung (tree protection), Denkmalschutz (monument protection), and Rundfunkbeitrag (broadcasting fee).

Only a small slice of the page — the `Anmeldung`, `Ummeldung`, and `Abmeldung` entries — is actually relevant to the target topics `city_registration` / `anmeldung`. The real, detailed procedural content for each service lives one click away, on pages that were never fetched.

ADR 0005 already anticipates this kind of source pairing: for Anmeldung specifically, it argues that the Hannover-local procedural source and the federal statute (source 13, §17 BMG) should be retrievable together — one for "how you do it locally," one for "what the law requires." Source 4 is the local-procedure half of that pair, even though its content is shallow.

## Decision

- Source 4 remains in the corpus for v1. It is not dropped, and its linked sub-pages are not crawled in this milestone.
- `merge_small_sections` (`src/app/ingestion/chunk.py`) was fixed so that when several of these short teaser sections are merged together to reach the minimum chunk size, the resulting chunk's `title` and `hierarchy` honestly list every original topic (joined with `|`) instead of silently taking on one neighbor's label. This was necessary specifically because source 4 is almost entirely short sections that require merging.
- The statutory registration deadline itself continues to rely on source 13 (§17 BMG), not on source 4's teaser text.

## Consequences

**Positive**
- Keeps a pointer to the Hannover-specific Anmeldung/Ummeldung/Abmeldung service names and URLs without additional crawling work.
- Because of the ADR-0006-style merge fix, chunks built from source 4 no longer assert false titles or false hierarchy relationships, even though the underlying page structure (many tiny unrelated sections) made that risk higher here than in other sources.

**Negative**
- The majority of source 4's ~20,000 characters (an estimated ~90%) is off-topic for the six target subjects and will be embedded anyway, which could dilute retrieval if not offset by metadata filtering.
- The Anmeldung-relevant content from source 4 is shallow — 1-3 sentences, often truncated with "..." — compared to what the actual linked service page would contain.

## Next Steps

- If evaluation shows source 4's shallow teaser text is insufficient to answer real Anmeldung questions, revisit fetching the individual linked service pages (e.g. "Anmeldung einer Wohnung: Zuzug nach Hannover") instead of relying on the landing-page teaser.
- Use the `topic` metadata field (per ADR 0005) during retrieval to bias away from source 4 chunks whose merged title doesn't include `anmeldung`/`ummeldung`/`abmeldung`, so off-topic municipal-service chunks don't compete for relevance on unrelated queries.
