---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
completedAt: '2026-04-12'
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-esg-mefali-copilot.md
  - CLAUDE.md
  - docs/architecture-frontend.md
  - docs/architecture-backend.md
  - docs/integration-architecture.md
  - docs/project-overview.md
workflowType: 'prd'
classification:
  projectType: web_app
  domain: fintech
  complexity: high
  projectContext: brownfield
featureId: '019-floating-copilot-guided-nav'
documentCounts:
  briefCount: 1
  researchCount: 0
  brainstormingCount: 0
  projectDocsCount: 5
---

# Product Requirements Document — ESG Mefali Copilot

**Auteur :** Angenor
**Date :** 2026-04-12
**Feature ID :** 019-floating-copilot-guided-nav

## Executive Summary

ESG Mefali est une plateforme conversationnelle IA qui démocratise l'accès à la finance durable pour les PME africaines francophones (zone UEMOA/CEDEAO). La plateforme intègre 8 modules métier — évaluation ESG, calculateur carbone, matching financement vert, scoring crédit alternatif, plan d'action — orchestrés par un graphe LangGraph à 10 noeuds avec ~100 tools LangChain et streaming SSE.

**Le problème :** Aujourd'hui, l'assistant IA vit dans une page `/chat` isolée ou un panneau latéral déconnecté du contenu des pages. Il répond aux questions mais ne montre jamais où se trouvent les réponses dans l'interface. Pour un public incluant le secteur informel et des utilisateurs peu technophiles, naviguer entre 18 pages et 11 entrées de menu constitue un obstacle silencieux à l'adoption. Les utilisateurs complètent les modules conversationnels mais n'exploitent pas les pages de résultats — là où réside la valeur tangible.

**La feature 019** transforme l'assistant en copilot contextuel omniprésent à travers deux axes :
1. **Widget de chat flottant** — glassmorphism avec fallback opaque, redimensionnable, historique des conversations, rétraction pendant le guidage. Remplace la page `/chat` et le panneau latéral.
2. **Navigation guidée visuelle** — parcours Driver.js pré-définis déclenchés par le LLM via un tool LangChain. Consentement binaire via widgets interactifs (feature 018). Décompteur sur les popovers Driver.js avec navigation automatique multi-pages.

### Ce qui rend cette approche spéciale

L'architecture hybride : le frontend détient les parcours guidés (sélecteurs CSS, étapes, `data-guide-target` pour les éléments dynamiques), le LLM déclenche le bon parcours au bon moment via un identifiant. Résultat : l'effet « copilot intelligent qui tient la main » pour une fraction du coût en tokens des solutions full-LLM. Le LLM sait *quand* guider, le frontend sait *comment* guider.

## Success Criteria

### Succès utilisateur

| Critère | Mesure | Cible |
|---|---|---|
| **Sentiment d'accompagnement** | Feedback qualitatif (entretiens utilisateurs, formulaire in-app) | Score satisfaction ≥ 4/5 sur la question « Je me suis senti guidé » |
| **Découverte des résultats** | Taux de visite `/esg/results`, `/carbon/results`, `/action-plan` dans les 5 min après complétion d'un module via le chat | > 60% (vs baseline actuelle à mesurer) |
| **Acceptation du guidage** | Ratio « Oui, montre-moi » vs « Non merci » sur les propositions de guidage | > 50% |
| **Complétion du guidage** | Parcours guidés commencés vs terminés (l'utilisateur suit toutes les étapes) | > 70% |
| **Rétention post-guidage** | Utilisateurs ayant accepté un guidage qui reviennent dans les 7 jours | Supérieur aux utilisateurs n'ayant pas eu de guidage |

### Succès business

| Critère | Mesure | Cible |
|---|---|---|
| **Taux de complétion multi-modules** | Nombre d'utilisateurs ayant complété ≥ 3 modules (ESG + carbone + financement ou crédit) | Augmentation de 20% vs période précédente |
| **Génération de rapports PDF** | Nombre de rapports générés après un guidage vers la page de résultats | Augmentation mesurable |
| **Économie de tokens** | Tokens LLM consommés par session utilisateur (résumé chat + renvoi vs explications détaillées) | Réduction de 15-25% par session |

### Succès technique

| Critère | Mesure | Cible |
|---|---|---|
| **Performance widget** | Temps d'ouverture du widget flottant (animation comprise) | < 300ms |
| **Connexion SSE cross-routes** | Pas de perte de connexion SSE lors de la navigation entre pages pendant un guidage | 0 déconnexion |
| **Fallback glassmorphism** | Le widget est fonctionnel et lisible sur navigateurs sans support `backdrop-filter` | 100% des navigateurs desktop modernes |
| **Couverture tests** | Tests unitaires + intégration pour les nouveaux composants et le tool LangChain | ≥ 80% |
| **Dark mode** | Tous les nouveaux composants compatibles dark mode | 100% |

### Résultats mesurables

- Baseline à capturer avant déploiement : taux de visite actuel des pages résultats après complétion d'un module
- Le widget flottant doit supporter l'ensemble des fonctionnalités existantes du chat (SSE streaming, rich blocks, widgets interactifs 018, upload documents, tool call indicators)
- Zéro régression sur les 935 tests backend existants

## User Journeys

### Parcours 1 : Fatou — « Montre-moi mes résultats » (guidage proposé par le LLM)

**Persona :** Fatou Diallo, 42 ans, gérante d'une PME de transformation agroalimentaire à Dakar (15 employés). Premier contact avec la plateforme il y a 3 jours. Elle a complété son profil entreprise et vient de finir son bilan carbone via le chat.

**Scène d'ouverture :** Fatou est sur la page `/dashboard`. Le widget de chat flottant en bas à droite affiche un badge indiquant un nouveau message. Elle clique pour l'ouvrir. L'assistant lui dit : « Votre empreinte carbone est de 47 tCO2e, principalement liée au transport (62%). Je peux vous montrer vos résultats détaillés avec le plan de réduction — voulez-vous ? »

**Action montante :** Un widget interactif apparaît avec deux boutons : « Oui, montre-moi » / « Non merci ». Fatou clique « Oui, montre-moi ». Le widget de chat se rétracte en un bouton. Un popover Driver.js apparaît sur le lien « Empreinte Carbone » dans la sidebar, avec un décompteur de 8 secondes : « Cliquez ici pour accéder à vos résultats carbone ». Fatou clique. La page `/carbon/results` se charge.

**Climax :** Driver.js pointe successivement : le graphique donut (répartition par catégorie), le benchmark sectoriel (« Vous êtes 15% en dessous de la moyenne agroalimentaire »), puis le plan de réduction avec les 3 premières actions recommandées. À chaque étape, un texte explicatif en français lui dit quoi regarder et pourquoi c'est important.

**Résolution :** Fatou comprend que son principal levier est le transport. Le guidage se termine, le widget de chat réapparaît. L'assistant lui dit : « Vous pouvez maintenant lancer votre évaluation ESG pour compléter votre profil de durabilité. » Elle se sent guidée, pas perdue.

### Parcours 2 : Moussa — « Je connais la plateforme » (guidage refusé)

**Persona :** Moussa Keita, 35 ans, responsable qualité dans une entreprise de recyclage à Abidjan. Utilisateur régulier depuis 2 semaines, a déjà complété l'ESG et le carbone.

**Scène d'ouverture :** Moussa est sur `/financing` et parcourt les fonds disponibles. Il ouvre le widget de chat pour demander : « Quels fonds sont compatibles avec mon profil ? » L'assistant fait le matching et répond avec un résumé de 3 fonds compatibles. Puis propose : « Je peux vous guider vers le fonds GCF qui matche le mieux — voulez-vous ? »

**Action montante :** Moussa clique « Non merci » — il sait déjà naviguer. Il clique lui-même sur le fonds GCF dans la liste de `/financing`. Le chat reste disponible en superposition, il peut poser des questions contextuelles sur le fonds tout en lisant la page de détail.

**Résolution :** Moussa utilise le widget comme assistant contextuel sans jamais quitter sa page. Le glassmorphism lui permet de voir le contenu de la page derrière le chat. Il obtient une réponse sur les critères d'éligibilité sans naviguer. L'expérience est fluide, sans interruption.

### Parcours 3 : Aminata — « Comment on fait ? » (guidage demandé explicitement)

**Persona :** Aminata Traoré, 28 ans, comptable dans une PME de panneaux solaires à Bamako. Première semaine sur la plateforme, envoyée par son directeur pour « préparer le dossier ESG ».

**Scène d'ouverture :** Aminata est sur le `/dashboard`, un peu intimidée par les 4 cartes vides (aucun module complété). Elle ouvre le widget de chat et tape : « Je ne sais pas par où commencer, tu peux me montrer ? »

**Action montante :** L'assistant détecte la demande explicite de guidage. Il répond : « Bien sûr ! On va commencer par votre évaluation ESG. Je vais vous poser quelques questions directement ici. » L'assistant lance le questionnaire ESG guidé dans le chat (routage vers `esg_scoring_node`). Aminata répond aux questions, critère par critère, dans le widget flottant.

**Climax :** L'évaluation terminée, l'assistant lui dit : « Votre score ESG est de 58/100. Je peux vous montrer le détail par pilier et les recommandations — voulez-vous ? » Aminata clique « Oui, montre-moi ». Le chat se rétracte. Driver.js la guide vers `/esg/results` et pointe le score global, puis les forces/faiblesses, puis les recommandations.

**Résolution :** Aminata a fait toute l'évaluation sans quitter le chat, puis a découvert la page de résultats grâce au guidage. Le parcours naturel : **conversation d'abord, visualisation ensuite**.

### Parcours 4 : Ibrahim — Edge case : navigation multi-pages avec décompteur expiré

**Persona :** Ibrahim Ouédraogo, 50 ans, dirigeant d'une coopérative agricole à Ouagadougou. Faible aisance numérique, connexion intermittente.

**Scène d'ouverture :** Ibrahim est dans le chat (widget flottant) et vient de terminer son évaluation ESG. L'assistant propose de lui montrer ses résultats. Ibrahim clique « Oui, montre-moi ».

**Action montante :** Le chat se rétracte. Driver.js pointe le lien « Évaluation ESG » dans la sidebar. Le décompteur démarre (8 secondes). Ibrahim lit le texte du popover, hésite, ne clique pas. Le décompteur arrive à zéro — la navigation vers `/esg/results` se fait automatiquement.

**Climax :** La page charge. Driver.js attend que le DOM soit stable puis pointe le score ESG global (cercle). Ibrahim voit son score 62/100 mis en surbrillance. Le parcours continue automatiquement — pas besoin de cliquer sur des boutons « Suivant ».

**Résolution :** Ibrahim a suivi le guidage sans jamais cliquer un lien lui-même. Le système a compensé son hésitation. Il voit ses résultats, comprend son score. L'accompagnement a fonctionné pour le cas le plus exigeant.

### Parcours 5 : Aïssatou — Détection mobile, dégradation gracieuse

**Persona :** Aïssatou Bah, 38 ans, commerçante à Conakry, accède à la plateforme depuis son téléphone Android.

**Scène :** Aïssatou se connecte depuis son smartphone. La plateforme détecte un écran mobile. Pas de widget de chat flottant, pas de guidage Driver.js. Elle voit l'interface standard mobile existante. Si elle accède au chat, c'est via le menu de navigation classique. L'expérience est identique à avant la feature 019 — zéro régression, zéro confusion.

### Résumé des capacités révélées par les parcours

| Parcours | Capacités requises |
|---|---|
| **Fatou** (guidage proposé) | Widget flottant, rétraction, consentement via widget 018, parcours multi-pages avec décompteur, réapparition du chat post-guidage |
| **Moussa** (guidage refusé) | Chat contextuel superposé, glassmorphism lisible, refus sans friction, conversations multiples |
| **Aminata** (guidage explicite) | Détection d'intent « montre-moi », déclenchement sans consentement quand demandé, enchaînement guidage → module conversationnel |
| **Ibrahim** (décompteur expiré) | Navigation automatique au timeout, attente DOM stable avant reprise, progression sans clic utilisateur |
| **Aïssatou** (mobile) | Détection mobile, désactivation complète du widget + guidage, zéro régression |

## Domain-Specific Requirements

### Conformité & Données sensibles

- **Glassmorphism et données financières** — Le fond transparent du widget laisse entrevoir la page derrière. Sur les pages affichant des données sensibles (score crédit `/credit-score`, montants FCFA `/financing`), le niveau de flou (`blur`) doit rendre les chiffres **illisibles** à travers le widget. Le fallback opaque résout ce problème nativement.
- **Guidage Driver.js et scores** — Les popovers Driver.js qui pointent des éléments contenant des scores ESG/crédit/carbone doivent respecter l'auth existante : si le token JWT expire pendant un guidage multi-pages, le système le renouvelle automatiquement via le refresh token sans interrompre le parcours (cf. FR32).
- **Pas de données sensibles dans les identifiants de parcours** — Le tool LangChain `trigger_guided_tour` transmet un identifiant de parcours (ex: `show_carbon_results`), jamais de données financières. Les données sont chargées par la page cible via les composables existants authentifiés.

### Contraintes techniques spécifiques au contexte Afrique de l'Ouest

- **Bande passante limitée** — Le widget flottant ne doit pas multiplier les appels API. La connexion SSE existante est réutilisée, pas dupliquée. Driver.js est chargé en lazy (import dynamique) — pas inclus dans le bundle initial.
- **Latence réseau** — Le décompteur multi-pages doit tolérer un temps de chargement de page ≤ 5 secondes avant de reprendre le guidage (attente DOM stable). Si le chargement dépasse 10 secondes, le guidage s'interrompt avec un message d'erreur dans le chat.
- **Coupures réseau** — Si la connexion SSE est perdue pendant un guidage, le parcours Driver.js en cours continue (il est entièrement côté frontend). Le widget de chat affiche un indicateur de reconnexion.

### Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Données financières visibles à travers le glassmorphism | Confidentialité | Blur ≥ 12px + fallback opaque via `@supports` |
| Token JWT expire pendant guidage multi-pages | Interruption potentielle | Renouvellement automatique via refresh token (cf. FR32, NFR9) |
| Driver.js pointe un élément non chargé (lazy loading, données async) | Popover perdu, UX cassée | `onHighlightStarted` vérifie existence du DOM element, retry 3× avec 500ms delay, abandon avec message chat si échec |
| L'utilisateur ferme le navigateur pendant un guidage | Perte de progression du parcours | État du parcours non persisté — pas critique, le LLM peut reproposer |

## Innovation & Patterns Nouveaux

### Zones d'innovation détectées

**1. Architecture hybride LLM-trigger / Frontend-guide**

Le pattern dominant dans les copilots SaaS 2025-2026 est soit full-LLM (le modèle génère les instructions de navigation — coûteux, fragile) soit full-statique (onboarding classique — figé, non contextuel). ESG Mefali introduit un **pattern intermédiaire** :

- Le LLM détecte le *moment opportun* (fin d'un module, question de l'utilisateur, données disponibles)
- Le frontend exécute un *parcours pré-compilé* (sélecteurs CSS, étapes, textes)
- La communication se fait via un identifiant opaque — zéro connaissance du DOM côté LLM

Ce pattern est reproductible dans tout SaaS avec un assistant IA.

**2. `data-guide-target` dynamique**

Les éléments rendus dynamiquement (liste de plans d'action, résultats spécifiques) sont marqués via des attributs de données. Driver.js les trouve via un sélecteur CSS standard. C'est la résolution du problème « comment pointer un élément qui n'existe pas encore au moment de la définition du parcours ».

**3. Rétraction contextuelle du chat**

Le widget de chat se minimise automatiquement quand il gêne — pendant un guidage Driver.js — puis réapparaît. Ce comportement adaptatif est rare dans les widgets de chat existants (Intercom, Crisp, Drift restent ouverts ou fermés).

### Contexte marché

- **Pillar (open source)** — Le plus proche concurrent en pattern. Mais full-LLM : le modèle exécute des actions dans le navigateur. Coûteux en tokens, fragile aux changements DOM.
- **OpenCopilot** — Transforme les intentions en appels API. Pas de guidage visuel.
- **Tendance 2026** — Les copilots contextuels sont un prérequis SaaS. Mais aucun ne cible spécifiquement les marchés à faible littératie numérique avec un guidage visuel adapté.

### Approche de validation

| Hypothèse | Comment la valider |
|---|---|
| Les utilisateurs acceptent le guidage (> 50%) | Ratio acceptation/refus sur le widget de consentement |
| Le guidage augmente l'usage des pages de résultats | Comparaison avant/après sur le taux de visite post-module |
| L'architecture hybride réduit les coûts tokens | Mesure tokens/session avant et après |
| Le décompteur ne désoriente pas les utilisateurs | Entretiens qualitatifs ciblés sur Ibrahim-type (faible littératie) |

### Mitigation des risques d'innovation

| Risque | Fallback |
|---|---|
| Les utilisateurs refusent systématiquement le guidage | Réduire la fréquence des propositions, ne proposer qu'après les 3 premiers modules |
| Le pattern hybride est trop rigide (parcours pré-définis insuffisants) | Ajouter un mode « highlight seul » — le LLM pointe un seul élément sans parcours complet, via `driver.highlight()` |
| Driver.js entre en conflit avec GSAP ou Chart.js | Tester les overlays sur chaque type de page (graphiques, mermaid, tableaux) — fallback : désactiver le highlight sur les éléments canvas |

## Exigences spécifiques Web App

### Vue d'ensemble technique

SPA Nuxt 4 existante (compatibilityVersion 4, structure `app/`). La feature 019 introduit 2 patterns nouveaux dans cette stack : un composant `position: fixed` avec glassmorphism (widget flottant) et une intégration de librairie tierce (Driver.js) avec contrôle programmatique cross-routes.

### Navigateurs cibles

| Navigateur | Version min | Support `backdrop-filter` | Notes |
|---|---|---|---|
| Chrome | 90+ | Oui | Cible principale desktop Afrique |
| Firefox | 103+ | Oui | |
| Safari | 15.4+ | Oui (préfixe `-webkit-`) | |
| Edge | 90+ | Oui | |
| Navigateurs sans support | — | Non | Fallback opaque via `@supports` |

Pas de support IE11. Pas de support mobile V1. Les métriques de performance et d'accessibilité sont détaillées dans la section [Non-Functional Requirements](#non-functional-requirements).

### Responsive et détection mobile

- **Breakpoint de désactivation :** `< 1024px` (correspond au breakpoint `lg` Tailwind existant, celui où `AppSidebar` apparaît)
- **Comportement mobile :** Le bouton flottant et le widget ne sont pas rendus. L'accès au chat se fait via la navigation classique (identique au comportement pré-019)
- **Détection :** Composable `useDeviceDetection` basé sur `window.matchMedia('(min-width: 1024px)')` avec listener pour les changements de taille

### Considérations d'implémentation

- **Persistance du widget cross-routes** — Le widget est monté dans `layouts/default.vue` (comme l'actuel `ChatPanel`), pas dans les pages. Il persiste entre les navigations Nuxt.
- **État du widget** — Géré par le store `ui` Pinia : `chatWidgetOpen`, `chatWidgetSize`, `chatWidgetMinimized` (rétraction pendant guidage)
- **Connexion SSE cross-routes** — `useChat` est déjà un composable partagé. La connexion SSE est initiée une fois et maintenue tant que le composable est monté dans le layout.
- **Driver.js et navigation Nuxt** — Après un `router.push()` pendant un guidage multi-pages, il faut attendre `nextTick()` + un délai pour la stabilité DOM avant de reprendre le parcours Driver.js.

## Project Scoping & Développement phasé

### Stratégie MVP

**Approche :** MVP de type *experience-first* — L'objectif n'est pas de livrer le maximum de fonctionnalités, mais de valider que le sentiment d'accompagnement est réel. Si les utilisateurs disent « c'est comme si quelqu'un me tenait la main », le MVP a réussi.

**Ressources nécessaires :** 1 développeur fullstack (Nuxt 4 + FastAPI/LangGraph). Le projet est un monorepo avec conventions bien établies et ~935 tests comme filet de sécurité.

### Parcours utilisateur MVP (Phase 1)

| Parcours | Inclus MVP ? | Justification |
|---|---|---|
| **Fatou** (guidage proposé, multi-pages) | Oui | Scénario fondamental — valide toute la chaîne |
| **Moussa** (guidage refusé, chat contextuel) | Oui | Valide le widget flottant sans guidage |
| **Aminata** (guidage demandé explicitement) | Oui | Valide la détection d'intent « montre-moi » |
| **Ibrahim** (décompteur expiré, navigation auto) | Oui | Valide le cas extrême (faible littératie) |
| **Aïssatou** (mobile, dégradation) | Oui | Zéro régression = non négociable |

**Tous les parcours sont MVP** — chacun valide un aspect critique de la feature. Aucun n'est optionnel.

### Capacités Must-Have (Phase 1)

| # | Capacité | Sans ça, le produit... |
|---|---|---|
| 1 | Widget flottant avec ouverture/fermeture animée | ...n'existe pas |
| 2 | Glassmorphism + fallback opaque | ...est visuellement cassé |
| 3 | Redimensionnement du widget | ...coupe les tableaux et rich blocks |
| 4 | Historique conversations dans le widget | ...perd du contexte |
| 5 | Suppression `/chat` + réutilisation composants | ...a 2 interfaces chat redondantes |
| 6 | Conscience contextuelle (page courante → LLM) | ...propose des guidages incohérents |
| 7 | Rétraction pendant guidage | ...masque ce qu'il montre |
| 8 | Registre de parcours extensible + Driver.js | ...ne peut pas guider |
| 9 | Décompteur + navigation auto multi-pages | ...bloque les utilisateurs peu technophiles |
| 10 | Tool LangChain `trigger_guided_tour` | ...ne peut pas déclencher de guidage |
| 11 | Consentement via widget 018 (binaire) | ...guide sans permission |
| 12 | Détection mobile (≥ 1024px) | ...casse sur mobile |
| 13 | Dark mode complet | ...viole la convention projet |
| 14 | `data-guide-target` sur éléments dynamiques | ...ne peut pas pointer les éléments de listes |

### Phase 2 — Growth (post-MVP)

- Parcours guidés contextuels selon le profil entreprise (secteur, maturité ESG)
- Suggestions proactives basées sur le comportement (pages jamais visitées, modules non complétés)
- Alertes hors-session (email/push) déclenchées par le copilot
- Analytics détaillées des parcours guidés (heatmap d'acceptation, points d'abandon)
- Mode « highlight seul » — `driver.highlight()` pour pointer un seul élément sans parcours complet

### Phase 3 — Expansion (vision)

- Support mobile du widget flottant (responsive bottom sheet)
- Mode accompagnateur pour conseillers terrain (CCI, agents BDS)
- Profil ESG public partageable
- API whitelabel du copilot pour intégrateurs

### Stratégie de mitigation des risques

**Risque technique majeur :** La persistance du widget et de la connexion SSE cross-routes.
- *Mitigation :* Le widget est monté dans le layout (pas dans les pages). `useChat` est déjà partagé. Valider avec un spike technique avant l'implémentation complète.

**Risque marché :** Les utilisateurs refusent le guidage (pop-up fatigue).
- *Mitigation :* Ne proposer le guidage qu'aux moments à haute valeur (fin de module, première utilisation). Fréquence adaptative : si l'utilisateur refuse 3 fois, réduire les propositions.

**Risque ressource :** Feature ambitieuse pour 1 développeur.
- *Contingence :* Livrer en 2 incréments — d'abord le widget flottant seul (sans guidage Driver.js), puis le système de guidage. Le widget seul a déjà de la valeur (chat omniprésent + glassmorphism).

## Functional Requirements

### Widget de chat flottant

- **FR1 :** L'utilisateur peut ouvrir et fermer le widget de chat via un bouton flottant en bas à droite de l'écran
- **FR2 :** L'utilisateur peut envoyer des messages texte et recevoir des réponses streamées de l'assistant IA depuis le widget flottant
- **FR3 :** L'utilisateur peut uploader des documents (PDF, DOCX, XLSX, images) depuis le widget flottant
- **FR4 :** L'utilisateur peut redimensionner le widget de chat
- **FR5 :** L'utilisateur peut basculer entre ses conversations passées depuis le widget flottant
- **FR6 :** L'utilisateur peut créer une nouvelle conversation depuis le widget flottant
- **FR7 :** L'utilisateur peut voir le contenu de la page derrière le widget (fond semi-transparent)
- **FR8 :** Le système affiche un fallback opaque sur les navigateurs ne supportant pas la transparence
- **FR9 :** L'utilisateur peut interagir avec les widgets interactifs (QCU/QCM, feature 018) depuis le widget flottant
- **FR10 :** L'utilisateur peut voir les indicateurs de tool calls, les rich blocks (chart, table, gauge, mermaid, timeline) et les notifications de profil dans le widget flottant

### Conscience contextuelle

- **FR11 :** Le système transmet au LLM l'identifiant de la page courante de l'utilisateur
- **FR12 :** L'assistant IA peut adapter ses réponses en fonction de la page sur laquelle se trouve l'utilisateur
- **FR13 :** L'assistant IA peut proposer un guidage visuel quand le contexte le justifie (fin de module, données disponibles à visualiser)

### Consentement et déclenchement du guidage

- **FR14 :** Quand l'assistant propose un guidage, l'utilisateur peut accepter (« Oui, montre-moi ») ou refuser (« Non merci ») via un widget interactif
- **FR15 :** L'utilisateur peut demander explicitement un guidage en langage naturel (ex: « montre-moi mes résultats ESG »)
- **FR16 :** Quand l'utilisateur demande explicitement un guidage, le système le déclenche sans afficher le widget de consentement
- **FR17 :** Le système adapte la fréquence des propositions de guidage (réduction après refus répétés) et réduit la durée du décompteur après plusieurs acceptations (l'utilisateur s'habitue)

### Navigation guidée Driver.js

- **FR18 :** Le système peut exécuter un parcours guidé pré-défini qui met en surbrillance des éléments de l'interface avec des explications textuelles en français
- **FR19 :** Le widget de chat se rétracte automatiquement pendant un parcours guidé
- **FR20 :** Le widget de chat réapparaît automatiquement à la fin d'un parcours guidé
- **FR21 :** Quand un parcours nécessite un changement de page, le système affiche un décompteur sur le popover pointant le lien à cliquer
- **FR22 :** Si l'utilisateur ne clique pas avant l'expiration du décompteur, le système navigue automatiquement vers la page cible
- **FR23 :** Après un changement de page, le parcours guidé reprend automatiquement une fois la page chargée
- **FR24 :** Le système peut pointer des éléments dynamiques (éléments de liste, résultats spécifiques) via des marqueurs de données
- **FR25 :** L'utilisateur peut interrompre un parcours guidé à tout moment (fermeture du popover, clic hors zone)

### Registre de parcours

- **FR26 :** Le système maintient un registre extensible de parcours guidés pré-définis (pages cibles, éléments à pointer, textes explicatifs). Les textes explicatifs peuvent être personnalisés par le LLM selon le contexte utilisateur (profil, secteur, données)
- **FR27 :** L'assistant IA peut déclencher un parcours spécifique via son identifiant
- **FR28 :** De nouveaux parcours peuvent être ajoutés au registre sans modifier le code du système de guidage

### Détection mobile

- **FR29 :** Le système détecte si l'utilisateur est sur un écran desktop (≥ 1024px) ou mobile
- **FR30 :** Sur mobile, le widget flottant et le système de guidage sont désactivés — l'interface existante est préservée sans régression

### Résilience et edge cases

- **FR31 :** Si un élément cible d'un parcours guidé n'est pas trouvé dans le DOM, le système abandonne l'étape après plusieurs tentatives et informe l'utilisateur via le chat
- **FR32 :** Si le token JWT expire pendant un guidage multi-pages, le système le renouvelle automatiquement via le refresh token sans interrompre le parcours
- **FR33 :** Si la connexion SSE est perdue, le parcours guidé en cours continue (entièrement frontend) et le widget affiche un indicateur de reconnexion
- **FR34 :** La connexion SSE est maintenue lors des navigations entre pages (pas de reconnexion)
- **FR35 :** Le système supporte le dark mode sur tous les nouveaux composants (widget, popovers, bouton flottant)

## Non-Functional Requirements

### Performance

| NFR | Critère mesurable |
|---|---|
| **NFR1 — Ouverture du widget** | Le widget s'ouvre complètement (animation comprise) en < 300ms |
| **NFR2 — Chargement Driver.js** | Le premier parcours guidé démarre en < 500ms (import dynamique + initialisation) |
| **NFR3 — Affichage popover** | Chaque étape Driver.js s'affiche en < 200ms après la précédente |
| **NFR4 — Impact bundle** | Driver.js est chargé en lazy — 0 Ko ajouté au bundle initial |
| **NFR5 — Mémoire** | Le widget monté en permanence consomme < 5 MB de mémoire supplémentaire |
| **NFR6 — Glassmorphism** | Le `backdrop-filter: blur` n'entraîne pas de chute de FPS < 30 pendant le scroll de la page derrière le widget |
| **NFR7 — SSE cross-routes** | Aucune reconnexion SSE lors des navigations entre pages. Latence de reprise du stream < 100ms après changement de route |

### Sécurité

| NFR | Critère mesurable |
|---|---|
| **NFR8 — Confidentialité glassmorphism** | Les données financières (montants FCFA, scores) sont illisibles à travers le blur du widget (blur ≥ 12px) |
| **NFR9 — Renouvellement JWT** | Le refresh token est utilisé automatiquement pendant un guidage multi-pages — aucune interruption visible pour l'utilisateur |
| **NFR10 — Identifiants de parcours** | Aucune donnée sensible (scores, montants, IDs utilisateur) ne transite dans les identifiants de parcours envoyés par le tool LangChain |
| **NFR11 — Auth sur données guidées** | Les données affichées sur les pages cibles d'un guidage passent par les composables authentifiés existants — pas de canal de données parallèle |

### Accessibilité

| NFR | Critère mesurable |
|---|---|
| **NFR12 — Contraste WCAG AA** | Ratio de contraste ≥ 4.5:1 sur tous les textes du widget, y compris avec le glassmorphism actif. Contraste vérifié aussi sur le fallback opaque |
| **NFR13 — Navigation clavier** | Le widget est atteignable via Tab. Les popovers Driver.js se ferment via Escape. Le focus est piégé dans le widget quand il est ouvert |
| **NFR14 — Réduction de mouvement** | Quand `prefers-reduced-motion` est actif, les animations GSAP du widget et les transitions Driver.js sont désactivées |
| **NFR15 — Screen readers** | Les messages du chat dans le widget sont annoncés via `aria-live`. Le bouton flottant a un label accessible (« Ouvrir l'assistant IA ») |

### Fiabilité & Résilience réseau

| NFR | Critère mesurable |
|---|---|
| **NFR16 — Tolérance latence** | Le guidage multi-pages attend le chargement de page jusqu'à 5s avant reprise. Au-delà de 10s, le guidage s'interrompt avec message d'erreur dans le chat |
| **NFR17 — Coupure réseau pendant guidage** | Le parcours Driver.js en cours continue (entièrement frontend). Le widget affiche un indicateur de reconnexion SSE |
| **NFR18 — Élément DOM absent** | Si un élément cible n'est pas trouvé, le système retente 3× avec 500ms d'intervalle. Après échec, l'étape est abandonnée et un message explicatif apparaît dans le chat |
| **NFR19 — Zéro régression** | Les 935 tests backend existants passent sans modification. Les 2 tests frontend existants passent sans modification |

### Intégration avec les features existantes

| NFR | Critère mesurable |
|---|---|
| **NFR20 — Feature 018 (widgets interactifs)** | Les widgets QCU/QCM fonctionnent identiquement dans le widget flottant et dans l'ancien ChatPanel. Le widget de consentement utilise le composant `SingleChoiceWidget` existant |
| **NFR21 — Feature 012 (tool calling)** | Le nouveau tool `trigger_guided_tour` suit le pattern existant des tools LangChain (log dans `tool_call_logs`, retry 1×, SSE events `tool_call_start/end`) |
| **NFR22 — Feature 013 (active_module)** | La conscience contextuelle (page courante) ne conflit pas avec le mécanisme `active_module` existant dans `ConversationState` |
| **NFR23 — Dark mode** | Tous les nouveaux composants respectent le thème du store `ui` et utilisent les variables de couleur définies dans `main.css` (`dark-card`, `dark-border`, `surface-dark-bg`, etc.) |
| **NFR24 — Conventions projet** | Code en anglais, commentaires en français, UI en français avec accents, composants dans `components/` avec PascalCase sans préfixe de dossier |
