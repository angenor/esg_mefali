# Quickstart: 002-chat-rich-visuals

**Date**: 2026-03-30

## Prerequis

- Node.js 20+, npm
- Python 3.12+, pip
- PostgreSQL 16+ (ou Docker)
- Variables d'environnement configurees (.env)

## Lancement rapide

```bash
# 1. Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 2. Frontend
cd frontend
npm install
npm run dev
```

Acceder a http://localhost:3000/chat

## Nouvelles dependances a installer

### Frontend
```bash
cd frontend
npm install marked dompurify
npm install -D @types/dompurify
```

### Backend
Aucune nouvelle dependance requise.

## Structure des fichiers a creer

```
frontend/app/
├── pages/chat.vue
├── components/
│   ├── chat/
│   │   ├── MessageParser.vue
│   │   └── WelcomeMessage.vue
│   ├── richblocks/
│   │   ├── ChartBlock.vue
│   │   ├── MermaidBlock.vue
│   │   ├── TableBlock.vue
│   │   ├── GaugeBlock.vue
│   │   ├── ProgressBlock.vue
│   │   ├── TimelineBlock.vue
│   │   ├── BlockError.vue
│   │   └── BlockPlaceholder.vue
│   └── ui/
│       └── FullscreenModal.vue
├── composables/
│   └── useMessageParser.ts
└── types/
    └── richblocks.ts
```

## Tests

```bash
# Frontend unit tests
cd frontend && npm run test

# Frontend E2E
cd frontend && npm run test:e2e

# Backend
cd backend && source venv/bin/activate && pytest
```

## Verification rapide

1. Se connecter / creer un compte
2. Naviguer vers /chat
3. Creer une nouvelle conversation
4. Envoyer : "Montre-moi un exemple de radar chart ESG"
5. Verifier : un graphique radar interactif s'affiche dans la reponse
6. Cliquer "Agrandir" → modale plein ecran
7. Cliquer "Telecharger" → PNG sauvegarde
