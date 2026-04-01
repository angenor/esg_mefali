# Research: Tableau de bord principal et plan d'action

**Feature**: 011-dashboard-action-plan
**Date**: 2026-04-01

## R1: Agrégation cross-modules pour le dashboard

**Decision**: Le service dashboard effectue des requêtes directes vers les services existants (ESG, carbone, crédit, financement, applications) via imports Python. Pas d'API interne HTTP entre modules.

**Rationale**: Le backend est un monolithe modulaire FastAPI. Les services sont des fonctions async qui acceptent une session DB. L'appel direct est plus simple, plus rapide et cohérent avec le pattern existant (ex: le noeud financing_node appelle déjà le service financing).

**Alternatives considered**:
- API HTTP interne entre modules : surcharge réseau inutile dans un monolithe
- Vue SQL matérialisée : trop rigide, les données changent souvent
- Cache Redis : prématuré (principe VII YAGNI), à ajouter si besoin de performance

## R2: Génération du plan d'action via LLM

**Decision**: Un nouveau noeud LangGraph `action_plan_node` appelle Claude via le prompt `action_plan.py` avec le contexte complet de l'utilisateur (profil, score ESG, bilan carbone, fonds recommandés, intermédiaires). Claude retourne un JSON structuré d'actions que le service parse et persiste en base.

**Rationale**: Pattern identique aux noeuds existants (esg_scoring_node, carbon_node, financing_node). Le LLM génère des actions contextualisées avec les coordonnées réelles des intermédiaires injectées dans le prompt. Le JSON structuré permet la persistance et le suivi.

**Alternatives considered**:
- Génération purement algorithmique (règles métier) : manque de personnalisation et de langage naturel
- Génération LLM sans structuration JSON : impossible à persister et suivre
- Appel API séparé hors LangGraph : incohérent avec l'architecture conversation-driven

## R3: Système de badges

**Decision**: Table `badges` avec conditions évaluées à la volée lors des événements déclencheurs (création bilan carbone, mise à jour score ESG, complétion action intermédiaire). Vérification dans le service action_plan lors de chaque mutation pertinente.

**Rationale**: Simplicité (principe VII). 5 badges avec des conditions simples ne justifient pas un moteur de règles. Les conditions sont vérifiées au moment des événements, pas en polling.

**Alternatives considered**:
- Moteur de règles dédié : surdimensionné pour 5 badges
- Cron de vérification périodique : latence inutile, les événements déclencheurs sont connus
- Système de points/XP : explicitement hors périmètre (assumption spec)

## R4: Rappels in-app

**Decision**: Les rappels sont stockés en base avec `scheduled_at` et `sent=false`. Le frontend effectue un polling léger sur `GET /api/reminders/upcoming` toutes les 60 secondes quand l'utilisateur est connecté. Les rappels échus sont affichés en toast et marqués `sent=true`.

**Rationale**: Approche la plus simple cohérente avec le principe YAGNI. Le SSE existe déjà pour le chat mais les rappels sont basse fréquence (quelques par jour max). Le polling à 60s est négligeable en charge.

**Alternatives considered**:
- WebSocket/SSE dédié aux rappels : complexité non justifiée pour la fréquence
- Cron backend + push notification : nécessite infrastructure push, hors périmètre
- Intégration dans le flux SSE du chat existant : couplage excessif entre modules

## R5: Blocs visuels dans le chat pour le plan d'action

**Decision**: Réutiliser le système de blocs riches existant (`richblocks/` components : TimelineBlock, TableBlock, MermaidBlock, GaugeBlock, ChartBlock). Le noeud `action_plan_node` inclut les blocs markdown dans la réponse LLM (```timeline, ```table, ```mermaid, ```gauge, ```chart) qui sont parsés par `MessageParser.vue`.

**Rationale**: Infrastructure déjà en place et testée. Les composants richblocks existent dans `frontend/app/components/richblocks/`. Le `MessageParser.vue` sait déjà parser ces blocs. Aucun développement frontend supplémentaire nécessaire pour le rendu des blocs.

**Alternatives considered**:
- Nouveau système de rendu : duplication inutile
- Rendu côté backend (PDF/image) : perte d'interactivité

## R6: Activité récente - types d'événements

**Decision**: Créer un type `ActivityEvent` avec les champs : type (enum), title, description, timestamp, related_entity_type, related_entity_id. Les événements sont collectés à la volée depuis les tables existantes (pas de table dédiée events).

**Rationale**: Les 3 sources d'événements (actions, système, modules) sont déjà en base avec des timestamps. Une requête UNION triée par date sur les 10 derniers éléments est simple et performante. Pas besoin d'event sourcing pour 10 éléments.

**Alternatives considered**:
- Table events dédiée (event sourcing) : surdimensionné, nécessite des triggers partout
- Log file parsing : fragile et non structuré
