---
title: "Product Brief: ESG Mefali Copilot — Assistant Flottant & Navigation Guidée"
status: "final"
created: "2026-04-12"
updated: "2026-04-12"
review_passes: ["skeptic", "opportunity", "adoption-friction"]
feature_id: "019-floating-copilot-guided-nav"
inputs:
  - CLAUDE.md
  - docs/index.md
  - docs/project-overview.md
  - docs/architecture-frontend.md
  - docs/component-inventory-frontend.md
  - brain dump utilisateur (discovery session)
---

# Product Brief : ESG Mefali Copilot — Assistant Flottant & Navigation Guidée

## Résumé exécutif

ESG Mefali accompagne les PME africaines francophones dans leur transition vers la finance durable. La plateforme offre déjà 8 modules métier (ESG, carbone, financement, crédit, plan d'action...) pilotés par un assistant IA conversationnel. Mais aujourd'hui, cet assistant vit dans une page dédiée `/chat` ou un panneau latéral — il **répond** aux questions sans jamais **montrer** où se trouvent les réponses dans l'interface.

Cette feature transforme l'assistant en **copilot contextuel omniprésent** : un widget de chat flottant glassmorphism accessible depuis toutes les pages, couplé à un système de navigation guidée visuelle (Driver.js) qui permet au LLM de littéralement pointer du doigt les éléments de l'interface à l'utilisateur. L'entrepreneur ne cherche plus, il est accompagné. Le LLM ne décrit plus, il montre.

C'est un changement de paradigme : passer d'un assistant qui **informe** à un compagnon qui **guide**.

## Le problème

Un dirigeant de PME au Sénégal termine son bilan carbone via le chat. L'assistant lui dit : « Votre empreinte est de 47 tCO2e. Consultez vos résultats détaillés sur la page Empreinte Carbone. » L'entrepreneur regarde l'écran. Il voit 11 liens dans la barre latérale. Il ne sait pas lequel mène aux résultats. Il hésite, clique au mauvais endroit, se décourage.

Aujourd'hui :

- **Le chat est déconnecté des pages** — l'assistant ne sait pas ce que l'utilisateur regarde et ne peut pas lui montrer où aller.
- **La navigation repose entièrement sur l'utilisateur** — 18 pages, 11 entrées de menu, des sous-sections dans chaque module. Pour un public peu technophile, dont une partie vient du secteur informel, c'est un obstacle silencieux.
- **Le panneau de chat latéral disparaît** quand on navigue vers `/chat` — et la page `/chat` coupe l'utilisateur du reste de la plateforme.

Le coût du statu quo : des utilisateurs qui complètent les modules conversationnels mais n'exploitent jamais les pages de résultats, les rapports PDF, le plan d'action — la valeur tangible de la plateforme.

## La solution

### 1. Widget de chat flottant omniprésent

Le panneau latéral et la page `/chat` sont remplacés par un **widget flottant en bas à droite**, toujours accessible. Le widget :

- S'ouvre et se ferme avec une animation fluide (GSAP)
- Affiche un fond **glassmorphism léger** (backdrop-filter blur) — l'utilisateur perçoit la page derrière, gardant le contexte visuel. **Fallback opaque** via `@supports` pour les navigateurs ou appareils ne supportant pas `backdrop-filter`
- Est **redimensionnable** avec une taille par défaut suffisante pour afficher des tableaux sans coupure
- Donne accès à l'**historique des conversations** (bascule entre conversations passées)
- Réutilise les composants existants du chat (ChatMessage, ChatInput, widgets interactifs, rich blocks)
- Se **rétracte automatiquement** pendant les séquences de guidage pour ne pas masquer ce que le LLM veut montrer

### 2. Navigation guidée par le LLM (Driver.js)

Quand le contexte le justifie, l'assistant propose une visite guidée. L'utilisateur choisit via un **widget interactif** (réutilisation de la feature 018) parmi 2 options claires :

- **Oui, montre-moi** — le LLM pilote Driver.js pour pointer les éléments pertinents
- **Non merci** — aucune action

Ce choix binaire réduit la friction cognitive, notamment pour les utilisateurs peu technophiles qui n'ont jamais vu de navigation guidée.

L'utilisateur peut aussi **demander explicitement** un guidage (« Montre-moi mes résultats ESG »).

**Mécanique multi-pages :**

Quand le guidage nécessite de changer de page, Driver.js affiche un **indicateur visuel avec décompteur** directement sur le widget/popover de l'étape en cours (pas dans le chat). Le décompteur pointe le lien ou bouton à cliquer. Si l'utilisateur ne clique pas avant la fin du décompte, la navigation se fait automatiquement. Le processus Driver.js reprend sur la page de destination.

### 3. Architecture hybride (économie de tokens)

- Les **parcours guidés sont pré-définis** côté frontend (pages cibles, sélecteurs CSS, étapes, textes explicatifs). Les pages et composants sont connus d'avance.
- Le LLM **déclenche** un parcours via un tool LangChain dédié — il envoie un identifiant de parcours, pas des instructions Driver.js.
- Les éléments dynamiques (ex: un plan d'action spécifique dans une liste) sont marqués via **`data-guide-target`** pour être trouvables automatiquement par Driver.js.
- Le LLM produit un **résumé concis dans le chat** puis renvoie vers la page détaillée — économie de tokens et de bande passante.

## Ce qui rend cette approche différente

| Alternative | Limite |
|---|---|
| Onboarding classique (tooltips statiques) | Se déclenche une seule fois, n'est pas contextuel, ne s'adapte pas au parcours de l'utilisateur |
| Liens cliquables dans les réponses chat | L'utilisateur doit encore trouver l'élément sur la page cible — le dernier kilomètre manque |
| Panneau latéral enrichi (actuel) | Reste déconnecté de la page, espace contraint, coupe le flux de travail |
| Copilot full LLM (type Pillar) | Coûteux en tokens — le LLM doit connaître le DOM, générer des sélecteurs. Non viable économiquement à l'échelle |

**L'approche ESG Mefali** combine le meilleur : la contextualité de l'IA (savoir *quand* guider) avec la précision et l'économie du pré-défini (savoir *comment* guider). Le résultat est un copilot qui semble intelligent et réactif, pour une fraction du coût en tokens.

## Qui est concerné

**Tous les profils d'utilisateurs**, sans distinction :
- Le dirigeant peu technophile qui découvre la plateforme
- Le responsable RSE qui connaît les concepts mais pas l'interface
- Le gestionnaire qui cherche des financements verts

Le dénominateur commun : des personnes qui ont besoin d'être accompagnées, pas juste informées. Le secteur informel africain implique des utilisateurs pour qui chaque friction dans l'interface est un risque d'abandon.

**Plateforme cible :** Desktop uniquement pour la V1. Détection automatique mobile/desktop — sur mobile, le comportement actuel est préservé (pas de widget flottant ni de guidage Driver.js).

## Critères de succès

| Signal | Mesure |
|---|---|
| L'utilisateur se sent accompagné | Feedback qualitatif positif (entretiens, NPS, formulaire in-app) |
| Les pages de résultats sont consultées | Augmentation du taux de visite des pages `/esg/results`, `/carbon/results`, `/action-plan` après complétion d'un module via le chat |
| Le guidage est accepté | Ratio d'acceptation « Oui, montre-moi » vs « Non merci » > 50% |
| L'engagement persiste | Les utilisateurs qui acceptent le guidage reviennent plus souvent dans les 7 jours |

## Périmètre V1

### Inclus

- Widget de chat flottant (glassmorphism, redimensionnable, historique conversations)
- Suppression sèche de la page `/chat` (projet pas encore en production), réutilisation des composants existants dans le widget flottant
- Rétraction automatique du widget pendant le guidage
- Système extensible de parcours guidés pré-définis (Driver.js)
- Marquage `data-guide-target` des éléments dynamiques
- Décompteur + navigation automatique pour les parcours multi-pages
- Tool LangChain `trigger_guided_tour` pour le déclenchement par le LLM
- Widget interactif (018) pour le consentement utilisateur (choix binaire : « Oui, montre-moi » / « Non merci »)
- Détection mobile/desktop (pas de widget flottant sur mobile)
- Conscience contextuelle : le LLM sait sur quelle page se trouve l'utilisateur

### Exclus (V1)

- Support mobile du widget flottant et du guidage
- Drag & drop du widget (position fixe bas-droite)
- Création de parcours guidés par l'utilisateur
- Analytics détaillées des parcours (au-delà du feedback qualitatif)

## Vision

Si cette feature réussit, ESG Mefali ne sera plus perçu comme « un outil avec un chatbot ». Il sera perçu comme **un conseiller qui connaît son bureau** — qui sait où sont les dossiers, qui les ouvre devant vous, qui pointe la ligne du tableau qui compte.

À terme, le système de parcours guidés devient un **langage d'interaction** entre le LLM et l'interface : chaque nouveau module, chaque nouvelle page, chaque nouveau composant peut être « enseigné » au copilot en ajoutant simplement un parcours et des `data-guide-target`. L'extensibilité est native.

Le copilot contextuel devient l'avantage concurrentiel majeur d'ESG Mefali face aux outils ESG traditionnels (formulaires, rapports statiques, portails institutionnels) qui dominent le marché africain francophone.
