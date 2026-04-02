# Feature Specification: Style de communication concis pour l'assistant IA

**Feature Branch**: `014-concise-chat-style`
**Created**: 2026-04-02
**Status**: Draft
**Input**: User description: "Instruction style concis pour le prompt systeme : pas de redondance texte/visuels, reponses directes, max 2-3 phrases par bloc visuel, pas de reformulations inutiles"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reponses concises apres un bloc visuel (Priority: P1)

Un dirigeant de PME demande son score ESG. L'assistant affiche un radar chart avec les scores E-S-G puis accompagne le visuel de 1-2 phrases d'insight actionnable, sans repeter les chiffres visibles sur le graphique.

**Why this priority**: C'est le cas le plus frequent -- chaque module (ESG, carbone, financement, credit) produit des blocs visuels. La redondance texte/visuel alourdit chaque interaction.

**Independent Test**: Envoyer un message declenchant un scoring ESG et verifier que la reponse ne repete pas les scores numeriques deja presents dans le bloc visuel.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec un profil entreprise complet, **When** il demande son evaluation ESG, **Then** la reponse contient un radar chart suivi de max 2-3 phrases focalisees sur l'insight principal et l'action recommandee, sans enumerer les scores par pilier.
2. **Given** un bilan carbone calcule avec un doughnut chart, **When** les resultats sont affiches, **Then** le texte d'accompagnement ne repete pas la repartition en pourcentages visible sur le graphique mais indique l'action de reduction prioritaire.
3. **Given** un tableau de recommandations ESG deja affiche, **When** l'assistant commente les resultats, **Then** il ne reformule pas le contenu du tableau ligne par ligne.

---

### User Story 2 - Pas de formules de politesse ni de recapitulatif (Priority: P1)

Un utilisateur met a jour son profil entreprise. L'assistant confirme en une seule phrase ("Profil mis a jour.") sans recapituler les informations que l'utilisateur vient de fournir.

**Why this priority**: Les reformulations inutiles et les formules de politesse allongent chaque echange et frustrent un dirigeant occupe.

**Independent Test**: Envoyer un message de mise a jour de profil et verifier que la confirmation fait moins de 2 phrases sans recapitulatif des donnees saisies.

**Acceptance Scenarios**:

1. **Given** un utilisateur qui fournit ses informations d'entreprise (secteur, ville, effectifs), **When** le profil est sauvegarde, **Then** la reponse est une confirmation courte (1 phrase) sans repeter les informations fournies.
2. **Given** un utilisateur qui demande de l'aide, **When** l'assistant repond, **Then** la reponse commence directement par l'information utile sans preambule type "Je suis ravi de vous aider...".
3. **Given** un utilisateur qui decrit son activite, **When** l'assistant enchaine, **Then** il ne commence pas par "Vous m'avez indique que..." ou toute reformulation de ce que l'utilisateur vient de dire.

---

### User Story 3 - Chaque mot apporte une information nouvelle (Priority: P2)

Un utilisateur parcourt plusieurs modules (ESG, carbone, financement). A chaque etape, les reponses de l'assistant sont denses en information : chaque phrase apporte soit une donnee nouvelle, soit une action concrete.

**Why this priority**: Ameliore l'experience globale sur l'ensemble de la plateforme mais depend de la bonne implementation des stories P1.

**Independent Test**: Parcourir un flux complet ESG puis carbone puis financement et verifier qu'aucune reponse ne contient de texte purement decoratif ou redondant.

**Acceptance Scenarios**:

1. **Given** une conversation multi-modules, **When** l'assistant produit des reponses successives, **Then** aucune phrase n'est purement decorative (pas de "Comme vous pouvez le voir...", "Voici les resultats detailles...").
2. **Given** un bloc visuel de type timeline ou progress, **When** l'assistant commente, **Then** il se limite a l'action prioritaire ou au prochain jalon, pas a une description exhaustive de chaque etape.

---

### Edge Cases

- Que se passe-t-il quand le bloc visuel seul est insuffisant (ex: gauge sans contexte) ? L'assistant doit fournir le contexte manquant en 1-2 phrases.
- Comment gerer une erreur de generation de visuel ? L'assistant doit fournir l'information en texte concis comme fallback.
- Que se passe-t-il si l'utilisateur pose une question ouverte sans bloc visuel ? Le style concis s'applique : reponse directe, pas de preambule.
- Que se passe-t-il lors des premiers echanges d'onboarding (utilisateur sans profil) ? L'assistant adopte un ton plus guide et pedagogique jusqu'a la fin du profilage initial, puis bascule en style concis.
- Que se passe-t-il si l'utilisateur utilise des emojis ? L'assistant peut en utiliser en retour, mais uniquement dans ce cas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le prompt systeme de base DOIT contenir une instruction de style imposant la concision apres chaque bloc visuel (max 2-3 phrases d'accompagnement).
- **FR-002**: Le prompt systeme DOIT interdire la repetition en texte d'informations deja presentes dans un bloc visuel (chart, gauge, table, progress, timeline, mermaid).
- **FR-003**: Le prompt systeme DOIT interdire les formules de politesse a rallonge et les preambules decoratifs.
- **FR-004**: Le prompt systeme DOIT interdire les recapitulatifs de ce que l'utilisateur vient de dire.
- **FR-005**: Le prompt systeme DOIT imposer des confirmations d'action en une seule phrase (ex: "Profil mis a jour.").
- **FR-006**: Le prompt systeme DOIT interdire les emojis sauf si l'utilisateur en utilise.
- **FR-007**: L'instruction de style DOIT etre injectee dans le prompt systeme de TOUS les noeuds du graphe (chat, esg_scoring, carbon, financing, credit, application, action_plan) pour garantir une coherence de ton.
- **FR-008**: L'instruction de style DOIT inclure des exemples BON/MAUVAIS pour guider le LLM de maniere concrete.
- **FR-009**: Le prompt DOIT contenir la regle "chaque mot doit apporter une information nouvelle ou une action concrete".
- **FR-010**: Le style concis NE DOIT PAS s'appliquer pendant la phase d'onboarding (utilisateur sans profil / premiere visite). Pendant cette phase, l'assistant adopte un ton plus guide et pedagogique. Le style concis s'active apres la fin du profilage initial.

### Key Entities

- **STYLE_INSTRUCTION**: Bloc de texte ajoute au prompt systeme, contenant les regles de concision, les interdictions, et les exemples BON/MAUVAIS.
- **Prompt systeme**: Prompt assemble dynamiquement pour chaque noeud du graphe LangGraph, incluant le BASE_PROMPT, les instructions visuelles, et maintenant le STYLE_INSTRUCTION.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les reponses accompagnant un bloc visuel ne depassent pas 3 phrases (hors blocs de code/JSON).
- **SC-002**: Aucune reponse ne contient de recapitulatif des informations que l'utilisateur vient de fournir dans le meme tour de conversation.
- **SC-003**: Les confirmations d'action (sauvegarde, mise a jour) tiennent en 1 phrase maximum.
- **SC-004**: Aucune reponse ne commence par une formule de politesse decorative (type "Je suis ravi...", "Excellent ! Voici...").
- **SC-005**: Le temps de lecture moyen d'une reponse de l'assistant diminue -- les reponses sont plus courtes a contenu egal.

## Clarifications

### Session 2026-04-02

- Q: Faut-il une exception au style concis pour les premiers echanges d'onboarding ou les questions pedagogiques ? → A: Exception onboarding — premieres interactions plus guidees, style concis applique apres le profilage initial.

## Assumptions

- L'instruction de style sera ajoutee au prompt systeme et non geree par un mecanisme externe (fine-tuning, guardrails, etc.).
- Le LLM (Claude via OpenRouter) respecte suffisamment les instructions de prompt pour que les regles de style soient appliquees sans post-processing.
- L'instruction sera placee apres les instructions de visualisation dans le prompt systeme, comme indique par l'utilisateur.
- Les prompts specialises de chaque module (ESG, carbone, etc.) heritent du BASE_PROMPT ou l'instruction sera injectee via les fonctions `build_*_prompt()` respectives.
- Si certains prompts specialises construisent leur prompt independamment du BASE_PROMPT, l'instruction devra etre injectee individuellement.
