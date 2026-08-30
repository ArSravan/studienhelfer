# M2 Source Inventory
## Purpose

This document records the source-selection methodology and findings from Milestone 2.

The machine-readable source inventory is stored in:

```
docs/m2-source-inventory.yaml
```

The architectural decisions derived from the inventory are documented in:

```
docs/decisions/0005-source-selection.md
```

## Source Metadata

Each source is classified using the following fields:

- url — source URL
- topic — topics covered by the source
- publisher — organisation publishing or providing the source
- authority_level — authority represented by the document
- jurisdiction — geographical or institutional scope
- format — HTML or PDF
- language — source language
- english_available — whether an English version is available
- verified — whether the source was manually verified

## Authority Model

The source inventory uses three authority levels:

```
statute
primary
secondary
```

## Statute

The legal text itself.

Examples:

- §16b AufenthG
- §17 BMG

## Primary

An official authority administering or governing the relevant process.

Examples:

- Federal Foreign Office
- Landeshauptstadt Hannover
- Leibniz Universität Hannover
- Federal Ministry of Health

## Secondary

An organisation or portal explaining or summarising authoritative information.

Examples:

- DAAD
- Make it in Germany

Publisher and authority level are intentionally separate fields.

## Key Findings

1. Jurisdiction is essential

Relevant information is distributed across federal, Hannover-specific, and university sources.

Therefore, semantic similarity alone is insufficient for reliable retrieval.

2. Language does not determine authority

Some of the strongest sources are German-only.

English sources can be useful for accessibility, but an English source should not automatically outrank a German primary or statutory source.

3. Source format varies

The inventory contains both HTML pages and PDF documents.

The ingestion pipeline must therefore support both formats.

4. URLs can change

Official URLs can redirect, disappear, or be replaced.

The ingestion system should monitor URL validity, redirects, changed pages, removed documents, and updated documents.

5. Publisher and authority are independent

A government organisation can publish a secondary explanatory document.

For example, Make it in Germany is government-operated but its explanatory student-work page is classified as secondary.

6. Federal and local sources may need to be combined

Anmeldung demonstrates this clearly.

The Hannover service portal describes the local procedure, while §17 BMG provides the federal statutory registration requirement.

The RAG should be capable of retrieving both when answering a question.

## Retrieval Implication

The metadata collected during M2 will become Qdrant payload metadata.

The intended retrieval architecture is:

```
User Question
      |
      v
Metadata / jurisdiction filtering
      |
      v
Semantic retrieval
      |
      v
Authority-aware reranking
      |
      v
Answer generation
```

This allows the system to distinguish between:

- relevant information,
- locally applicable information,
- authoritative information,
- explanatory information.

## M2 Conclusion

The source inventory demonstrates that reliable RAG retrieval is not only a semantic-search problem.

The system must understand:

- where information comes from,
- which jurisdiction it applies to,
- what level of authority it represents,
- what language it is written in,
- what format it uses,
- and whether the source is still current.

These findings define the metadata model that will be used in later retrieval and reranking stages.