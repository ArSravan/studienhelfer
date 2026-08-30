# ADR 0005: Source Selection and Authority Metadata

- Status: Accepted
- Date: 2026-08-30
- Decision: Adopt a three-tier authority model and keep publisher, authority level, jurisdiction, and language as separate metadata fields.

## Context

The M2 source inventory showed that reliable information for international students in Hannover is distributed across different authorities, jurisdictions, languages, and document types.

The same topic can also be covered by sources with different levels of authority.

For example, student working rights are explained by government information portals, but the actual legal rule is contained in §16b AufenthG. Similarly, the Hannover service portal provides local information about Anmeldung, while the statutory registration requirement is defined by §17 BMG.

A semantic search system alone cannot reliably distinguish these sources.

Therefore, source metadata must be part of the retrieval design.

## Decision

Each source will contain the following independent metadata fields:

```
publisher: string
authority_level: statute | primary | secondary
jurisdiction:
  - federal
  - hannover
  - university
  - germany
language:
  - english
  - german
format: html | pdf
``` 

The three authority levels are deliberately constrained to an enum:

```
statute
primary
secondary
```

This prevents inconsistent values from entering the database.

## Three-Tier Authority Model
1. **Statute**

statute means that the source contains the legal text itself.

Examples include German legislation published through gesetze-im-internet.de, such as:

- §16b AufenthG — residence for study
- §17 BMG — registration requirement

A statutory source represents the legal rule itself.

This is categorically different from an organisation explaining the same rule.

For example:

```
§16b AufenthG permits the relevant student employment activity.
```

is a claim based on the statutory text.

Whereas:

```
Make it in Germany explains that international students can work under the applicable student rules.
```

is an explanatory claim.

Both may be relevant, but they do not have the same authority level.

2. **Primary**

primary means that the source comes from an official authority responsible for administering, governing, or providing the relevant process.

Examples include:

- Federal Foreign Office visa information
- Landeshauptstadt Hannover residence-permit procedures
- Landeshauptstadt Hannover registration procedures
- Leibniz Universität Hannover enrollment procedures
- Federal Ministry of Health information

A primary source is authoritative for the process or information it officially provides, but it is not necessarily the underlying law.

3. **Secondary**

secondary means that the source explains, summarises, or contextualises information from authoritative sources.

Examples include:

- DAAD explanatory information
- Make it in Germany explanatory pages

Secondary sources can still be highly useful and reliable. However, they should not be treated as equivalent to statutory text or an authority's official procedure.

## Publisher and Authority Level Are Independent

The publisher and authority level must be stored separately.

publisher answers:

```
Who published this source?
```

authority_level answers:

```
What kind of authority does this document represent?
```

For example, Make it in Germany is a German government information portal, but its student working-hours page is an explanatory source.

Therefore:

```
publisher: "Federal Republic of Germany / Make it in Germany"
authority_level: "secondary"
```

is correct.

The following representation should be avoided:

```
authority: "Federal Government (SECONDARY)"
```

because it combines two independent concepts.

A government organisation can publish secondary information, while a non-government organisation could reproduce or reference primary legal material.

## Jurisdiction Model

Jurisdiction is stored separately from authority level.

The current inventory uses the following jurisdiction values:

```
federal
hannover
university
germany
```

These represent different scopes of applicability.

## Federal

Federal legislation and federal government information.

Examples:

- Aufenthaltsgesetz
- Bundesmeldegesetz
- Federal Foreign Office visa information

## Hannover

Information specific to the City of Hannover.

Examples:

- Residence-permit procedures
- Anmeldung procedures

## University

Information governed by Leibniz Universität Hannover.

Examples:

- Enrollment
- Semester registration
- University regulations

## Germany

Information intended to apply generally across Germany without being tied to a particular city or university.

For example, DAAD's general information about health insurance can be classified as Germany-wide.

## Why Jurisdiction Matters for Retrieval

A question can be semantically similar to information from several locations while only one location is actually relevant.

For example:

```
"How do I apply for a student residence permit in Hannover?"
```

A residence-permit page from another German city may contain highly similar words and procedures.

However, it may describe a different administrative process.

Therefore, jurisdiction should be used as metadata during retrieval.

Conceptually:

```
User Query
    |
    v
Identify jurisdiction
    |
    v
Metadata filtering
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

For a Hannover-specific question, the retrieval system should prefer:

```
jurisdiction IN ["federal", "hannover"]
```

rather than allowing every German local authority to compete based only on semantic similarity.

This means a Munich procedure should not become a candidate simply because it is semantically similar to the question.

## German Primary / English Secondary Asymmetry

The source inventory also showed an important language pattern.

Some of the strongest authoritative sources are available only in German.

For example:

- German statutes
- Hannover administrative procedures
- University regulations

At the same time, English-language information is often easier to find through explanatory sources such as DAAD and Make it in Germany.

Therefore, language must not be used as a proxy for authority.

The system should not assume:

```
English = better source
```

Instead:

```
language
authority_level
publisher
jurisdiction
```

are independent properties.

An English secondary source may be useful for explaining a rule to an international student, while a German statutory source may be the strongest evidence for the actual legal claim.

## Example: Student Working Hours

Student working hours provide the clearest example of the authority distinction.

The legal rule is contained in §16b AufenthG.

The Make it in Germany page explains the rule for students in a more accessible way.

Therefore:

```
- source: "§16b AufenthG"
  authority_level: "statute"
  language: "german"

- source: "Make it in Germany"
  authority_level: "secondary"
  language: "english"
```

Both sources are relevant.

However, the statutory source should carry greater evidentiary weight when the system makes a claim about what the law actually permits.

This is the motivating example for future authority-aware reranking.

## Example: Anmeldung

Anmeldung demonstrates why federal and local sources may need to be combined.

The Hannover service portal provides local procedural information.

The federal Bundesmeldegesetz provides the statutory registration requirement.

The RAG should therefore be able to retrieve both sources:

```
- topic:
    - anmeldung
  jurisdiction:
    - hannover
  authority_level: primary

- topic:
    - registration_deadline
  jurisdiction:
    - federal
  authority_level: statute
```

The generated answer can then distinguish between:

1. what German law requires, and
2. how the student completes the process in Hannover.

This is preferable to expecting a single document to contain every relevant fact.

## Source Freshness

The source inventory also demonstrated that official URLs can change.

An official Hannover page was found to redirect or change even though the underlying government service remained available.

Therefore, URL validity cannot be assumed permanently.

The ingestion pipeline should monitor:

- broken URLs
- HTTP errors
- redirects
- changed pages
- removed documents
- replaced PDFs
- updated documents

Source records should retain the original URL and sufficient metadata to support future validation.

## Data Format

The source inventory will be stored as YAML rather than prose.

The inventory is structured data that will eventually be consumed by the ingestion pipeline.

Example:

```
id: 9
title: "Student Working Hours — §16b AufenthG"
url: "https://www.gesetze-im-internet.de/aufenthg_2004/__16b.html"
topic:
  - working_hours
  - student_employment
publisher: "Bundesministerium der Justiz"
authority_level: "statute"
jurisdiction:
  - federal
format: "html"
language:
  - german
english_available: false
verified: true
```

The observations and reasoning from the inventory remain in documentation and ADRs rather than being embedded into the machine-readable source file.

## Qdrant Metadata

These source fields will become Qdrant payload metadata during ingestion.

Conceptually:

```
payload:
  source_id: 9
  topic:
    - working_hours
    - student_employment
  publisher: "Bundesministerium der Justiz"
  authority_level: "statute"
  jurisdiction:
    - federal
  format: "html"
  language:
    - german
  english_available: false
```

This allows retrieval to combine metadata filtering with semantic similarity.

The intended architecture is:

```
Metadata filtering
        +
Semantic similarity
        +
Authority-aware reranking
```

rather than relying exclusively on vector similarity.

## Consequences
### **Positive**

- Prevents geographically incorrect sources from competing equally with local sources.
- Distinguishes statutory text from official administrative guidance.
- Separates publisher identity from document authority.
- Prevents English-language sources from automatically outranking stronger German sources.
- Provides a clear schema for Qdrant payload metadata.
- Enables future authority-aware reranking.
- Makes source freshness monitoring possible.
- Allows local procedures and federal statutes to be retrieved together when required.

### **Negative**

- Every source requires additional metadata.
- Authority classification requires manual verification during the initial inventory.
- Some sources may combine explanatory and administrative content, requiring judgement.
- Retrieval becomes more complex than pure vector similarity.
- German-language primary and statutory sources may require additional processing or translation support.
- Decision Summary

The M2 source inventory establishes four independent concepts:

```
publisher
authority_level
jurisdiction
language
```

The authority model is:

```
statute
primary
secondary
```

The central design principle is:

- Publisher identifies who publishes the information. Authority level identifies what kind of authority the document represents. Jurisdiction identifies where or to whom it applies. Language identifies how the information is presented.

These properties will be preserved as source metadata and used by the retrieval pipeline.