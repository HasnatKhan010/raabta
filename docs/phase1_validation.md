# Phase 1 corpus validation

Validation date: 2026-08-16. These are measured corpus-construction statistics, not retrieval results.

## Source subset

- Source: `wikimedia/wikipedia`, configuration `20231101.ur`
- Revision: `3e1f92c331f318af862b87e2319ed5dc26d80f5d`
- Source card records: 200,154
- Deterministically retained articles: 4,000
- Minimum article length: 80 whitespace tokens
- Subset SHA-256: `cf8abe3bc85140e7d8fe202d0406085214942d736bd16f3eeb92a5b95022906c`
- Article token length: minimum 80, median 186, mean 463.00, maximum 45,533

The maximum is a genuine long-form article, not an empty/duplicate-record error. All 4,000 article IDs are unique and all records retain title, URL, raw text, clean text, and a project domain label.

## Project-domain distribution

| Project label | Articles |
|---|---:|
| Geography | 938 |
| General | 900 |
| History | 757 |
| Pakistan | 748 |
| Culture | 460 |
| Science | 197 |

These are deterministic keyword-based project labels, not official Wikipedia categories. Their purpose is auditing and breakdown analysis; they must not be cited as Wikipedia metadata.

## Chunking comparison

| Chunk / overlap | Passages | Mean tokens | Median | SHA-256 |
|---|---:|---:|---:|---|
| 120 / 24 | 20,106 | 111.34 | 120 | `67ddd9fdeef1f7bbf48026ca8cffcbf52a13aeba163b3fb8250b5a2eb03d1463` |
| 150 / 30 | 16,352 | 135.92 | 150 | `47648cf679facb9a576841542289767f854c1a27aca6cb8e14e3f3eb1a2e5671` |
| 180 / 36 | 13,908 | 158.81 | 180 | `0fd6fbda4747e7c46d2cc1f2e1c2215024c928aadb6006847128467cba60e4f8` |

Every variant represents all 4,000 articles, has unique passage IDs, and has token counts consistent with stored text. The 150/30 setting is the assignment default. Selection between development settings uses development retrieval results and does not inspect locked-test performance.

## Acceptance check

The literal Urdu query `اسلام آباد` retrieved a passage from article ID `521248`, *اخبار اردو (جریدہ)*, with the original Urdu Wikipedia URL retained. Literal matching is only a Phase 1 evidence-survival check; it is not reported as a retrieval baseline.

## Roman-Urdu supporting slice

- Source revision: `b9ef670661582b5f17eff68b4e65fbe25f3cb0b9`
- Automatically verified license metadata: Apache-2.0
- Bounded development rows: 30,000
- Unique aligned pairs: 29,577
- Duplicate aligned pairs retained and recorded: 423
- Unique Roman-Urdu strings: 29,539
- Unique Urdu strings: 29,560
- Median length: 14 Roman-Urdu tokens and 14 Urdu tokens
- Local slice SHA-256: `8bcf7a0166ce35d2b516784ac5bd5f09b086e3e003dc5238b4c44a4ddfbeabcf`

This slice follows the pinned training-shard order and is not claimed to be a statistically representative random sample. It supports spelling/transliteration analysis only and is not retrieval relevance supervision.
