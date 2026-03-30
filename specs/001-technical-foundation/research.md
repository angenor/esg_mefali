# Research: Foundation Technique ESG Mefali

**Date**: 2026-03-30 | **Branch**: `001-technical-foundation`

## R-001 : LangGraph + FastAPI Streaming

**Decision** : Utiliser LangGraph avec `langgraph-checkpoint-postgres` pour la persistance et `StreamingResponse` FastAPI pour le SSE.

**Rationale** : LangGraph fournit un framework d'orchestration de graphes d'agents avec support natif du streaming. Le `PostgresSaver` (ou `AsyncPostgresSaver`) de `langgraph-checkpoint-postgres` persiste automatiquement l'etat des conversations dans PostgreSQL, ce qui evite de gerer manuellement la serialization.

**Pattern cle** :
- Le graphe et le checkpointer sont initialises dans le `lifespan` FastAPI (critique pour garder les connexions PostgreSQL ouvertes)
- Le graphe est compile avec `graph.compile(checkpointer=checkpointer)`
- Chaque invocation utilise un `thread_id` (= conversation_id) dans la config
- Le streaming se fait via `graph.astream_events(version="v2")` qui yield des evenements types (`on_chat_model_stream` pour les tokens)
- FastAPI wrappe ces evenements dans un `StreamingResponse(media_type="text/event-stream")`
- Le checkpointer utilise `AsyncPostgresSaver.from_conn_string()` (gere autocommit et row_factory automatiquement)

**Alternatives considerees** :
- Appel direct Claude API + gestion manuelle de l'historique : trop rigide pour l'ajout futur de noeuds/modules
- LangChain seul (sans LangGraph) : pas de gestion de graphe, plus difficile a etendre

## R-002 : LLM via OpenRouter

**Decision** : Utiliser `ChatOpenAI` de `langchain-openai` avec `base_url` pointant vers OpenRouter (et non `ChatAnthropic`).

**Rationale** : `ChatAnthropic` ne supporte pas nativement OpenRouter — il route les requetes incorrectement vers `/v1/v1/messages`. `ChatOpenAI` avec la base URL OpenRouter fonctionne correctement et permet de changer de modele facilement.

**Pattern cle** :
```python
# Configuration dans app/graph/nodes.py
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
    streaming=True,
)
```

**Dependance** : `langchain-openai` (au lieu de `langchain-anthropic`)

**Alternatives considerees** :
- `ChatAnthropic` avec base_url OpenRouter : bug connu, routing incorrect des URLs
- Appel direct API Anthropic (sans OpenRouter) : moins flexible pour changer de modele

## R-003 : Authentification JWT FastAPI

**Decision** : Implementer JWT custom avec `python-jose` + `passlib[bcrypt]`, sans framework auth externe.

**Rationale** : Pour la v1, l'auth est simple (email/password + JWT). Les frameworks comme `fastapi-users` ajoutent de la complexite non necessaire. L'implementation custom est plus legere et conforme au principe VII (Simplicite).

**Pattern cle** :
- `passlib` pour le hashing bcrypt
- `python-jose` pour la creation/verification des JWT
- Dependance FastAPI `get_current_user` qui decode le token et charge l'utilisateur
- Access token (1h) dans le header Authorization: Bearer
- Refresh token (30j) retourne dans le body (stocke en localStorage cote client)

**Alternatives considerees** :
- `fastapi-users` : trop opinionne, ajoute des modeles/routes qu'on ne controle pas
- `authlib` : plus adapte pour OAuth2, surdimensionne ici

## R-004 : Nuxt 4 + TypeScript Strict

**Decision** : Initialiser avec `npx nuxi@latest init` (Nuxt 4 stable) avec `strict: true` dans tsconfig.

**Rationale** : Nuxt 4 est la version courante stable. TypeScript strict detecte plus d'erreurs a la compilation.

**Pattern cle** :
- `nuxt.config.ts` avec `typescript: { strict: true }`
- Modules : `@pinia/nuxt`, `@nuxtjs/tailwindcss`
- Plugins client-only : `*.client.ts` pour GSAP, Chart.js, Mermaid

**Alternatives considerees** :
- Nuxt 3 : version precedente, moins de features

## R-005 : TailwindCSS 4 dans Nuxt 4

**Decision** : Utiliser `@nuxtjs/tailwindcss` module pour l'integration. Configurer le design system dans `tailwind.config.ts`.

**Rationale** : Le module officiel gere l'integration automatique. TailwindCSS 4 avec le nouveau moteur CSS est plus rapide.

**Pattern cle** :
- Couleurs de marque dans `theme.extend.colors`
- Design system : vert (#10B981), bleu (#3B82F6), violet (#8B5CF6), orange (#F59E0B), rouge (#EF4444), fond (#F9FAFB), texte (#111827)

## R-006 : PostgreSQL + pgvector via Docker

**Decision** : Utiliser l'image `pgvector/pgvector:pg16` pour Docker Compose.

**Rationale** : Image officielle pgvector basee sur PostgreSQL 16, extension pgvector pre-installee. Suffit de faire `CREATE EXTENSION IF NOT EXISTS vector` dans une migration Alembic.

**Alternatives considerees** :
- PostgreSQL standard + installation manuelle pgvector : plus complexe, fragile

## R-007 : SSE Frontend (EventSource / fetch)

**Decision** : Utiliser `fetch` + `ReadableStream` cote frontend plutot que `EventSource`.

**Rationale** : `EventSource` ne supporte pas les headers custom (Authorization Bearer). `fetch` avec `getReader()` sur le body stream permet d'envoyer le JWT et de lire le flux SSE.

**Pattern cle** :
```typescript
// Dans composables/useChat.ts
const response = await fetch('/api/chat/stream', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ message, conversation_id }),
})
const reader = response.body!.getReader()
const decoder = new TextDecoder()
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  const chunk = decoder.decode(value)
  // Parser les evenements SSE et mettre a jour le message
}
```

**Alternatives considerees** :
- `EventSource` : ne supporte pas les headers custom, obligerait a passer le token en query param (mauvaise pratique securite)
- WebSocket : surdimensionne pour du streaming unidirectionnel
