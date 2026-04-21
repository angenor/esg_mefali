# CODEMAPS — Documentation transversale ESG Mefali

Hub des codemaps techniques transverses. Chaque page documente un pattern
backend réutilisable (abstraction, gate, migration, extension schéma) avec
§1 Vue d'ensemble (Mermaid) + §§ suivantes selon le pattern.

## Pages

- [data-model-extension.md](./data-model-extension.md) — Extension du schéma BDD (Story 10.1 chaîne migrations 020–027).
- [feature-flags.md](./feature-flags.md) — Feature flag `ENABLE_PROJECT_MODEL` + pattern « ajouter un flag » (Story 10.9).
- [security-rls.md](./security-rls.md) — Row Level Security PostgreSQL sur 4 tables sensibles (Story 10.5).
- [storage.md](./storage.md) — Abstraction `StorageProvider` local + S3 EU-West-3 (Story 10.6).
