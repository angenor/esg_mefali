# Inventaire des composants Frontend

56 composants Vue 3 dans `frontend/app/components/`, regroupés en 11 sous-dossiers par feature. Tous compatibles **dark mode** obligatoire et écrits en `<script setup lang="ts">`.

## 1. Vue d'ensemble

| Dossier | # | Catégorie | Réutilisable |
|---|---:|---|---|
| `ui/` | 2 | UI génériques | ✓ |
| `layout/` | 3 | Layout app | ✗ (singletons) |
| `chat/` | 13 | Feature Chat IA + widgets | partiel (widgets) |
| `richblocks/` | 8 | Blocs visuels injectables | ✓ |
| `esg/` | 6 | Feature ESG | ✗ |
| `credit/` | 7 | Feature Crédit | ✗ |
| `dashboard/` | 4 | Feature Dashboard | ✗ |
| `action-plan/` | 6 | Feature Plan d'action | ✗ |
| `documents/` | 4 | Feature Documents | ✗ |
| `profile/` | 3 | Feature Profil | ✗ |
| **Total** | **56** | | |

## 2. `components/ui/` — UI génériques

| Composant | Rôle | Props clés | Slots |
|---|---|---|---|
| `FullscreenModal.vue` | Modal plein écran (preview docs, formulaires longs) | `isOpen`, `title`, `@close` | `default`, `footer` |
| `ToastNotification.vue` | Toast temporaire (success/error/info) | `message`, `type`, `duration` | — |

> **Dette technique** : seulement 2 composants UI génériques. La règle projet (`CLAUDE.md`) impose d'extraire tout pattern répété 2+ fois dans `components/ui/`. Candidats évidents à factoriser : boutons, badges, inputs, cards, tabs, gauges génériques.

## 3. `components/layout/` — Layout applicatif

| Composant | Rôle |
|---|---|
| `AppHeader.vue` | Barre supérieure : logo, titre, avatar user, toggle dark mode, toggle chat panel |
| `AppSidebar.vue` | Navigation gauche : liens modules, état actif, collapse mobile |
| `ChatPanel.vue` | Panneau chat IA toujours visible à droite (ouverture via store `ui.chatPanelOpen`) |

Utilisés uniquement dans `layouts/default.vue`.

## 4. `components/chat/` — Chat IA (13 composants)

| Composant | Rôle |
|---|---|
| `ChatInput.vue` | Input texte + upload file + gestion envoi (verrouillé si question interactive `pending`) |
| `ChatMessage.vue` | Rendu d'un message (user/assistant), parsing markdown + richblocks, intègre les widgets interactifs |
| `MessageParser.vue` | Parse le contenu assistant en segments (texte vs richblocks) |
| `ConversationList.vue` | Liste conversations (sidebar chat drawer) |
| `WelcomeMessage.vue` | Message de bienvenue onboarding |
| `ProfileNotification.vue` | Notification in-chat des mises à jour de profil (event SSE `profile_update`) |
| `ToolCallIndicator.vue` | Indicateur visuel contextualisé en français pour chaque tool call en cours |
| `InteractiveQuestionHost.vue` | Hôte d'un widget interactif (feature 018), dispatch selon type |
| `SingleChoiceWidget.vue` | Widget QCU (radiogroup, ARIA `role="radiogroup"` + `aria-checked`) |
| `MultipleChoiceWidget.vue` | Widget QCM (checkbox, ARIA `role="checkbox"` + `aria-checked`) |
| `JustificationField.vue` | Champ justification (max 400 caractères, `aria-describedby`) |
| `AnswerElsewhereButton.vue` | Bouton « Répondre autrement » — expire la question et débloque l'input texte |
| `InteractiveQuestionInputBar.vue` | Barre d'actions associée au widget (soumettre / abandonner) |

**Principe feature 018** : un seul widget `pending` par conversation. Les précédents sont marqués `expired` automatiquement côté backend.

## 5. `components/richblocks/` — Blocs visuels inline (8)

Blocs rendus dans les réponses LLM via `useMessageParser`. Types enregistrés dans `types/richblocks.ts` (`RichBlockType`, `ParsedSegment`).

| Composant | Rôle | Données |
|---|---|---|
| `ChartBlock.vue` | Graphique Chart.js (bar, line, pie, doughnut, radar) | `ChartBlockData` |
| `MermaidBlock.vue` | Diagramme Mermaid (timeline, flow, gantt) | `{ code: string }` |
| `TableBlock.vue` | Tableau structuré avec entêtes + lignes | `TableBlockData` |
| `GaugeBlock.vue` | Jauge circulaire (score, progression) | `GaugeBlockData` |
| `ProgressBlock.vue` | Barre de progression | `ProgressBlockData` |
| `TimelineBlock.vue` | Timeline chronologique verticale (normalisée via `utils/normalizeTimeline.ts`) | `TimelineBlockData` |
| `BlockError.vue` | Placeholder d'erreur de parsing/rendu | `{ message: string }` |
| `BlockPlaceholder.vue` | Skeleton pendant le chargement d'un bloc | — |

La normalisation `TimelineBlock` (feature 013) tolère plusieurs formats : `phases` / `items` / `steps` → `events`, alias `period→date`, `name→title`, `state→status`, defaut `status=todo`.

## 6. `components/esg/` — Feature ESG (6)

| Composant | Rôle |
|---|---|
| `ScoreCircle.vue` | Score global ESG en cercle (0-100, couleur selon seuil) |
| `CriteriaProgress.vue` | Barres de progression par critère et par pilier |
| `ScoreHistory.vue` | Historique des évaluations (Chart.js line) |
| `Recommendations.vue` | Liste des recommandations LLM |
| `ReportButton.vue` | Bouton de génération rapport PDF |
| `StrengthsBadges.vue` | Badges des forces / faiblesses ESG |

## 7. `components/credit/` — Feature Crédit (7)

| Composant | Rôle |
|---|---|
| `ScoreGauge.vue` | Jauge principale du score crédit |
| `SubScoreGauges.vue` | 4 sous-scores (solvabilité, impact, qualité données, comportement) |
| `FactorsRadar.vue` | Chart.js radar des facteurs |
| `ScoreHistory.vue` | Historique du score |
| `DataCoverage.vue` | Taux de couverture des data points |
| `CertificateButton.vue` | Téléchargement certificat PDF |
| `Recommendations.vue` | Actions d'amélioration |

## 8. `components/dashboard/` — Dashboard (4)

| Composant | Rôle |
|---|---|
| `ScoreCard.vue` | Carte score synthétique (ESG / carbon / credit) |
| `FinancingCard.vue` | Carte financements avec parcours intermédiaire |
| `NextActions.vue` | Prochaines étapes (3-5 items prioritaires) |
| `ActivityFeed.vue` | Flux d'activité chronologique |

## 9. `components/action-plan/` — Plan d'action (6)

| Composant | Rôle |
|---|---|
| `ActionCard.vue` | Carte item d'action (titre, catégorie, priorité, deadline, status) |
| `ProgressBar.vue` | Barre de progression globale et par catégorie |
| `Timeline.vue` | Timeline verticale chronologique |
| `CategoryFilter.vue` | Filtres par catégorie (environment / social / governance / financing / carbon / intermediary_contact) |
| `BadgeGrid.vue` | Grille des badges débloqués (5 types) |
| `ReminderForm.vue` | Formulaire de création de rappel |

## 10. `components/documents/` — Documents (4)

| Composant | Rôle |
|---|---|
| `DocumentList.vue` | Liste des documents uploadés |
| `DocumentDetail.vue` | Détail + analyse LLM + chunks |
| `DocumentUpload.vue` | Upload par drag & drop (wrapper du FormData) |
| `DocumentPreview.vue` | Aperçu PDF dans `FullscreenModal` |

## 11. `components/profile/` — Profil (3)

| Composant | Rôle |
|---|---|
| `ProfileForm.vue` | Formulaire d'édition complet |
| `ProfileField.vue` | Champ individuel éditable inline |
| `ProfileProgress.vue` | Taux de complétude par section |

## 12. Conventions communes

- **Props typées** : tous les composants exportent une `interface Props` TypeScript
- **Émissions typées** : `defineEmits<{ ... }>()`
- **Dark mode** : variantes `dark:` systématiques — testées manuellement
- **Accessibilité** : labels ARIA sur les widgets interactifs (`radiogroup`, `checkbox`, `aria-checked`, `aria-describedby`)
- **Auto-import** : `pathPrefix: false` dans `nuxt.config.ts` permet d'utiliser `<ScoreCircle />` sans préfixe de dossier

## 13. Dépendances inter-composants (liens clés)

```
pages/chat.vue
 ├─ layout/ChatPanel
 │   ├─ chat/ConversationList
 │   ├─ chat/ChatMessage ──► richblocks/* (parse segments)
 │   │   ├─ chat/InteractiveQuestionHost
 │   │   │   ├─ chat/SingleChoiceWidget
 │   │   │   ├─ chat/MultipleChoiceWidget
 │   │   │   └─ chat/JustificationField
 │   │   └─ chat/ToolCallIndicator
 │   └─ chat/ChatInput
 │       └─ chat/InteractiveQuestionInputBar
 └─ chat/ProfileNotification

pages/dashboard.vue
 ├─ dashboard/ScoreCard × 3
 ├─ dashboard/FinancingCard
 ├─ dashboard/NextActions
 └─ dashboard/ActivityFeed

pages/esg/results.vue
 ├─ esg/ScoreCircle
 ├─ esg/CriteriaProgress
 ├─ esg/ScoreHistory
 ├─ esg/Recommendations
 ├─ esg/StrengthsBadges
 └─ esg/ReportButton

pages/credit-score/index.vue
 ├─ credit/ScoreGauge
 ├─ credit/SubScoreGauges
 ├─ credit/FactorsRadar
 ├─ credit/ScoreHistory
 ├─ credit/DataCoverage
 ├─ credit/CertificateButton
 └─ credit/Recommendations
```
