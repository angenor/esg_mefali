# CODEMAPS — Documentation transversale ESG Mefali

Hub des codemaps techniques transverses. Chaque page documente un pattern
backend réutilisable (abstraction, gate, migration, extension schéma) avec
§1 Vue d'ensemble (Mermaid) + §§ suivantes selon le pattern.

## Pages

- [audit-trail.md](./audit-trail.md) — D6 audit immuable catalogue, endpoint consultation + export CSV (Story 10.12).
- [data-model-extension.md](./data-model-extension.md) — Extension du schéma BDD (Story 10.1 chaîne migrations 020–027).
- [feature-flags.md](./feature-flags.md) — Feature flag `ENABLE_PROJECT_MODEL` + pattern « ajouter un flag » (Story 10.9).
- [methodology.md](./methodology.md) — Patterns transverses dev-story BMAD (scan NFR66, dep dry-run, calibration sizing, corpus validation) — Story 10.13 post-review.
- [outbox.md](./outbox.md) — Micro-Outbox `domain_events` + worker APScheduler SKIP LOCKED (Story 10.10).
- [rag.md](./rag.md) — Abstraction `EmbeddingProvider` + switch OpenAI ↔ Voyage + migration dim 1536→1024 parallel (Story 10.13).
- [security-rls.md](./security-rls.md) — Row Level Security PostgreSQL sur 4 tables sensibles (Story 10.5).
- [source-tracking.md](./source-tracking.md) — NFR-SOURCE-TRACKING + CI nightly FR63 (Story 10.11).
- [storage.md](./storage.md) — Abstraction `StorageProvider` local + S3 EU-West-3 (Story 10.6).
- [storybook.md](./storybook.md) — Storybook partiel + 6 composants à gravité (Story 10.14).
- [ui-primitives.md](./ui-primitives.md) — Primitives UI Phase 0 Button/Input/Badge/Drawer/Combobox/DatePicker/Icon (Stories 10.15-10.21).
