# CODEMAPS — Documentation transversale ESG Mefali

Hub des codemaps techniques transverses. Chaque page documente un pattern
backend réutilisable (abstraction, gate, migration, extension schéma) avec
§1 Vue d'ensemble (Mermaid) + §§ suivantes selon le pattern.

## Pages

- [audit-trail.md](./audit-trail.md) — D6 audit immuable catalogue, endpoint consultation + export CSV (Story 10.12).
- [data-model-extension.md](./data-model-extension.md) — Extension du schéma BDD (Story 10.1 chaîne migrations 020–027).
- [feature-flags.md](./feature-flags.md) — Feature flag `ENABLE_PROJECT_MODEL` + pattern « ajouter un flag » (Story 10.9).
- [outbox.md](./outbox.md) — Micro-Outbox `domain_events` + worker APScheduler SKIP LOCKED (Story 10.10).
- [security-rls.md](./security-rls.md) — Row Level Security PostgreSQL sur 4 tables sensibles (Story 10.5).
- [source-tracking.md](./source-tracking.md) — NFR-SOURCE-TRACKING + CI nightly FR63 (Story 10.11).
- [storage.md](./storage.md) — Abstraction `StorageProvider` local + S3 EU-West-3 (Story 10.6).
