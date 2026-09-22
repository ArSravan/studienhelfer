# ADR 0006: Source 6 (Immatrikulationsordnung PDF) Excluded from Ingestion

- Status: Accepted
- Date: 2026-09-15
- Decision: Exclude source 6 (`data/raw/6.pdf`) from the chunking/embedding pipeline until it has been reprocessed with OCR.

## Context

Source 6 is the Immatrikulationsordnung (enrollment regulations) of Leibniz Universität Hannover, provided as `data/raw/6.pdf`.

Text extraction was attempted with both `pdfplumber` and `PyMuPDF` (see `docs/decisions/ingestion_notes.md`). Both produced text with character-level corruption rather than clean, readable German.

This is confirmed in the current `data/parsed/6.txt`. Line 18 contains:

```
§ 12 AustauschstudiumXQG+RFKVFKXOSDUWQHUVFKDIWHQ
```

Decoding `XQG+RFKVFKXOSDUWQHUVFKDIWHQ` with a Caesar shift of 3 yields `UND OCHSCHULPARTNERSCHAFTEN`, i.e. the original heading was almost certainly `... und Hochschulpartnerschaften`. This confirms the corruption is a systematic character-mapping fault in the PDF's embedded font encoding (a broken glyph-to-Unicode mapping), not random noise — and it is scattered through the document, not confined to one spot.

This kind of corruption changes actual letters. It cannot be repaired by downstream text cleaning (whitespace normalization, line joining, etc.), because the cleaning step has no way to know a letter is wrong.

## Decision

- `data/parsed/6.txt` is not run through the chunking pipeline (`extract_sections` / `merge_small_sections` / `split_large_section`) in its current form.
- Source 6 will be reprocessed using OCR (rendering the PDF pages to images and running OCR, instead of extracting the embedded text layer) before it is added to the ingested corpus.
- Until OCR reprocessing is complete and validated, statutory content from the Immatrikulationsordnung is not available to the RAG system. A user question that depends on this document should surface as unanswered rather than be answered from corrupted text.

## Consequences

**Positive**
- Prevents corrupted, misleading legal text from being embedded and later cited to a user making a visa/enrollment decision.
- Keeps the corruption visible and tracked instead of silently degrading answer quality.

**Negative**
- The Immatrikulationsordnung is not covered by the corpus until OCR work is done.
- Requires a separate OCR extraction path before source 6 becomes usable.

## Next Steps

- Run `data/raw/6.pdf` through an OCR-based extraction path.
- Re-validate the resulting text for corruption (e.g. spot-check headings and legal cross-references) before re-enabling it in the ingestion pipeline.
- Update `docs/m2-source-inventory.yaml` to reflect the OCR requirement for source 6.
