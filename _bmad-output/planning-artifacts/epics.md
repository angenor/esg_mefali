---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: 'complete'
completedAt: '2026-04-12'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/product-brief-esg-mefali-copilot.md
  - CLAUDE.md
featureId: '019-floating-copilot-guided-nav'
project_name: 'esg_mefali'
user_name: 'Angenor'
date: '2026-04-12'
---

# ESG Mefali — Feature 019 : Epic Breakdown

## Overview

Ce document fournit le decoupage complet en epics et stories pour la feature 019-floating-copilot-guided-nav du projet esg_mefali. Il decompose les exigences du PRD (35 FRs, 24 NFRs) et les decisions architecturales (7 ADRs) en stories implementables.

## Requirements Inventory

### Functional Requirements

FR1: L'utilisateur peut ouvrir et fermer le widget de chat via un bouton flottant en bas a droite de l'ecran
FR2: L'utilisateur peut envoyer des messages texte et recevoir des reponses streamees de l'assistant IA depuis le widget flottant
FR3: L'utilisateur peut uploader des documents (PDF, DOCX, XLSX, images) depuis le widget flottant
FR4: L'utilisateur peut redimensionner le widget de chat
FR5: L'utilisateur peut basculer entre ses conversations passees depuis le widget flottant
FR6: L'utilisateur peut creer une nouvelle conversation depuis le widget flottant
FR7: L'utilisateur peut voir le contenu de la page derriere le widget (fond semi-transparent)
FR8: Le systeme affiche un fallback opaque sur les navigateurs ne supportant pas la transparence
FR9: L'utilisateur peut interagir avec les widgets interactifs (QCU/QCM, feature 018) depuis le widget flottant
FR10: L'utilisateur peut voir les indicateurs de tool calls, les rich blocks (chart, table, gauge, mermaid, timeline) et les notifications de profil dans le widget flottant
FR11: Le systeme transmet au LLM l'identifiant de la page courante de l'utilisateur
FR12: L'assistant IA peut adapter ses reponses en fonction de la page sur laquelle se trouve l'utilisateur
FR13: L'assistant IA peut proposer un guidage visuel quand le contexte le justifie (fin de module, donnees disponibles a visualiser)
FR14: Quand l'assistant propose un guidage, l'utilisateur peut accepter (« Oui, montre-moi ») ou refuser (« Non merci ») via un widget interactif
FR15: L'utilisateur peut demander explicitement un guidage en langage naturel (ex: « montre-moi mes resultats ESG »)
FR16: Quand l'utilisateur demande explicitement un guidage, le systeme le declenche sans afficher le widget de consentement
FR17: Le systeme adapte la frequence des propositions de guidage (reduction apres refus repetes) et reduit la duree du decompteur apres plusieurs acceptations
FR18: Le systeme peut executer un parcours guide pre-defini qui met en surbrillance des elements de l'interface avec des explications textuelles en francais
FR19: Le widget de chat se retracte automatiquement pendant un parcours guide
FR20: Le widget de chat reapparait automatiquement a la fin d'un parcours guide
FR21: Quand un parcours necessite un changement de page, le systeme affiche un decompteur sur le popover pointant le lien a cliquer
FR22: Si l'utilisateur ne clique pas avant l'expiration du decompteur, le systeme navigue automatiquement vers la page cible
FR23: Apres un changement de page, le parcours guide reprend automatiquement une fois la page chargee
FR24: Le systeme peut pointer des elements dynamiques (elements de liste, resultats specifiques) via des marqueurs de donnees
FR25: L'utilisateur peut interrompre un parcours guide a tout moment (fermeture du popover, clic hors zone)
FR26: Le systeme maintient un registre extensible de parcours guides pre-definis (pages cibles, elements a pointer, textes explicatifs). Les textes peuvent etre personnalises par le LLM selon le contexte utilisateur
FR27: L'assistant IA peut declencher un parcours specifique via son identifiant
FR28: De nouveaux parcours peuvent etre ajoutes au registre sans modifier le code du systeme de guidage
FR29: Le systeme detecte si l'utilisateur est sur un ecran desktop (>= 1024px) ou mobile
FR30: Sur mobile, le widget flottant et le systeme de guidage sont desactives — l'interface existante est preservee sans regression
FR31: Si un element cible d'un parcours guide n'est pas trouve dans le DOM, le systeme abandonne l'etape apres plusieurs tentatives et informe l'utilisateur via le chat
FR32: Si le token JWT expire pendant un guidage multi-pages, le systeme le renouvelle automatiquement via le refresh token sans interrompre le parcours
FR33: Si la connexion SSE est perdue, le parcours guide en cours continue (entierement frontend) et le widget affiche un indicateur de reconnexion
FR34: La connexion SSE est maintenue lors des navigations entre pages (pas de reconnexion)
FR35: Le systeme supporte le dark mode sur tous les nouveaux composants (widget, popovers, bouton flottant)

### NonFunctional Requirements

NFR1: Le widget s'ouvre completement (animation comprise) en < 300ms
NFR2: Le premier parcours guide demarre en < 500ms (import dynamique + initialisation)
NFR3: Chaque etape Driver.js s'affiche en < 200ms apres la precedente
NFR4: Driver.js est charge en lazy — 0 Ko ajoute au bundle initial
NFR5: Le widget monte en permanence consomme < 5 MB de memoire supplementaire
NFR6: Le backdrop-filter blur n'entraine pas de chute de FPS < 30 pendant le scroll
NFR7: Aucune reconnexion SSE lors des navigations entre pages. Latence de reprise du stream < 100ms apres changement de route
NFR8: Les donnees financieres (montants FCFA, scores) sont illisibles a travers le blur du widget (blur >= 12px)
NFR9: Le refresh token est utilise automatiquement pendant un guidage multi-pages — aucune interruption visible
NFR10: Aucune donnee sensible (scores, montants, IDs utilisateur) ne transite dans les identifiants de parcours envoyes par le tool LangChain
NFR11: Les donnees affichees sur les pages cibles d'un guidage passent par les composables authentifies existants — pas de canal de donnees parallele
NFR12: Ratio de contraste >= 4.5:1 sur tous les textes du widget, y compris avec le glassmorphism actif. Contraste verifie aussi sur le fallback opaque
NFR13: Le widget est atteignable via Tab. Les popovers Driver.js se ferment via Escape. Le focus est piege dans le widget quand il est ouvert
NFR14: Quand prefers-reduced-motion est actif, les animations GSAP du widget et les transitions Driver.js sont desactivees
NFR15: Les messages du chat dans le widget sont annonces via aria-live. Le bouton flottant a un label accessible (« Ouvrir l'assistant IA »)
NFR16: Le guidage multi-pages attend le chargement de page jusqu'a 5s avant reprise. Au-dela de 10s, le guidage s'interrompt avec message d'erreur dans le chat
NFR17: Le parcours Driver.js en cours continue (entierement frontend). Le widget affiche un indicateur de reconnexion SSE
NFR18: Si un element cible n'est pas trouve, le systeme retente 3x avec 500ms d'intervalle. Apres echec, l'etape est abandonnee et un message explicatif apparait dans le chat
NFR19: Les 935 tests backend existants passent sans modification. Les tests frontend existants passent sans modification
NFR20: Les widgets QCU/QCM fonctionnent identiquement dans le widget flottant et dans l'ancien ChatPanel. Le widget de consentement utilise le composant SingleChoiceWidget existant
NFR21: Le nouveau tool trigger_guided_tour suit le pattern existant des tools LangChain (log dans tool_call_logs, retry 1x, SSE events tool_call_start/end)
NFR22: La conscience contextuelle (page courante) ne conflit pas avec le mecanisme active_module existant dans ConversationState
NFR23: Tous les nouveaux composants respectent le theme du store ui et utilisent les variables de couleur definies dans main.css
NFR24: Code en anglais, commentaires en francais, UI en francais avec accents, composants PascalCase sans prefixe de dossier

### Additional Requirements

- ADR1 : Pattern singleton via module-level state pour useChat.ts — etat reactif declare au niveau module (hors de la fonction composable) pour persister cross-routes
- ADR2 : Connexion SSE par message (POST-based), reader stocke dans une ref module-level, AbortController pour annulation propre
- ADR3 : Composable useGuidedTour comme orchestrateur avec machine a etats (idle → loading → ready → navigating → waiting_dom → highlighting → complete | interrupted)
- ADR4 : Nouveau marker SSE __sse_guided_tour__ + event SSE dedie guided_tour + tool LangChain trigger_guided_tour
- ADR5 : Double systeme — attributs data-guide-target sur les composants + registre de parcours dans lib/guided-tours/registry.ts
- ADR6 : Machine a etats dans le store ui + sequence GSAP → Driver.js avec promesses pour orchestration retraction/reapparition
- ADR7 : Import dynamique Driver.js avec pre-chargement opportuniste via requestIdleCallback + CSS dans main.css
- Sequence d'implementation : D1 → D2 → Widget → D7 → D5 → D3 → D6 → D4 (respecter le graphe de dependances)
- Nouveau dossier components/copilot/ — les 13 composants chat existants restent inchanges et sont reutilises par composition
- Suppression de la page /chat et de ChatPanel.vue — remplacement par FloatingChatWidget dans layouts/default.vue
- Backend : empreinte minimale — 2 nouveaux fichiers (guided_tour_tools.py + guided_tour.py), modification de nodes.py, state.py, chat.py
- Convention data-guide-target : [module]-[element] en kebab-case
- Convention tour_id : show_[module]_[page] en snake_case
- 6 parcours guides pre-definis : show_esg_results, show_carbon_results, show_financing_catalog, show_credit_score, show_action_plan, show_dashboard_overview
- Messages d'erreur UX en francais avec accents et ton empathique
- Ajout data-guide-target sur ~15 composants existants (esg, carbon, financing, credit, action-plan, dashboard, sidebar)

### UX Design Requirements

Pas de document UX Design distinct. Les exigences UX sont integrees dans le PRD (glassmorphism, fallback opaque, retraction, decompteur, detection mobile) et dans l'Architecture (dark mode overrides Driver.js, popover custom, countdown badge).

### FR Coverage Map

| FR | Epic | Description |
|---|---|---|
| FR1-FR10 | Epic 1 | Widget flottant (ouverture, streaming, upload, resize, historique, glassmorphism, fallback, widgets 018, rich blocks) |
| FR11-FR13 | Epic 3 | Conscience contextuelle (page courante → LLM, adaptation reponses, proposition guidage) |
| FR14-FR17 | Epic 6 | Consentement et declenchement (widget binaire, demande explicite, sans consentement, frequence adaptative) |
| FR18 | Epic 5 | Parcours guide pre-defini avec surbrillance et textes FR |
| FR19-FR20 | Epic 5 | Retraction/reapparition widget pendant guidage |
| FR21-FR23 | Epic 5 | Decompteur multi-pages + navigation auto + reprise apres chargement |
| FR24 | Epic 4 | Marqueurs data-guide-target pour elements dynamiques |
| FR25 | Epic 5 | Interruption du parcours par l'utilisateur |
| FR26, FR28 | Epic 4 | Registre extensible de parcours + ajout sans modification du moteur |
| FR27 | Epic 6 | Declenchement par identifiant via le LLM |
| FR29-FR30 | Epic 1 | Detection mobile + desactivation widget |
| FR31-FR33 | Epic 7 | Resilience (DOM retry, JWT refresh, coupure SSE) |
| FR34 | Epic 1 | SSE cross-routes sans reconnexion |
| FR35 | Epic 1 | Dark mode complet |

## Epic List

### Epic 1 : Chat persistant et widget flottant
L'utilisateur accede au chat IA depuis n'importe quelle page via un widget flottant elegant, sans jamais perdre le contexte de conversation lors de la navigation.
**FRs couvertes :** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR29, FR30, FR34, FR35
**Phases archi :** 1 (module-level state), 2 (SSE cross-routes), 3 (widget flottant)

### Epic 2 : Migration et suppression de la page /chat
L'interface est unifiee — plus de duplication entre la page /chat et le widget flottant. La navigation est coherente et sans confusion.
**FRs couvertes :** Transversale (prerequis : Epic 1 livre le remplacement)

### Epic 3 : Conscience contextuelle du LLM
L'assistant sait sur quelle page se trouve l'utilisateur et adapte ses reponses en consequence — il ne propose plus des actions hors-contexte.
**FRs couvertes :** FR11, FR12, FR13

### Epic 4 : Infrastructure de guidage visuel
Le systeme est pret a montrer visuellement les elements de l'interface a l'utilisateur — les composants existants sont marques et le catalogue de parcours est en place.
**FRs couvertes :** FR24, FR26, FR28
**Phases archi :** 4 (lazy loading Driver.js), 5 (registre parcours + data-guide-target)

### Epic 5 : Parcours guides et navigation multi-pages
L'utilisateur peut suivre des parcours guides visuels complets — le systeme pointe les elements importants, navigue entre les pages avec decompteur, et le widget se retracte/reapparait fluidement.
**FRs couvertes :** FR18, FR19, FR20, FR21, FR22, FR23, FR25
**Phases archi :** 6 (composable useGuidedTour), 7 (orchestration GSAP + Driver.js)

### Epic 6 : Declenchement intelligent par le LLM et consentement
L'assistant propose des guidages au bon moment (fin de module, demande explicite) et respecte le choix de l'utilisateur via un consentement clair. La frequence s'adapte au comportement.
**FRs couvertes :** FR13, FR14, FR15, FR16, FR17, FR27
**Phase archi :** 8 (tool LangChain backend)

### Epic 7 : Resilience et edge cases
L'experience reste fluide meme en conditions degradees — connexion lente, elements manquants, token expire, coupure reseau.
**FRs couvertes :** FR31, FR32, FR33

### Epic 8 : Tests d'integration end-to-end
Confiance et qualite — les 5 parcours utilisateur du PRD (Fatou, Moussa, Aminata, Ibrahim, Aissatou) sont valides de bout en bout.
**FRs couvertes :** Transversale (validation de toutes les FRs)

---

## Epic 1 : Chat persistant et widget flottant

L'utilisateur accede au chat IA depuis n'importe quelle page via un widget flottant elegant, sans jamais perdre le contexte de conversation lors de la navigation.

### Story 1.1 : Refactoring useChat en module-level state

En tant qu'utilisateur,
je veux que ma conversation et le streaming SSE persistent quand je navigue entre les pages,
afin de ne jamais perdre le fil de mon echange avec l'assistant IA.

**Acceptance Criteria:**

**Given** le composable useChat.ts avec son etat reactif actuel dans la fonction composable
**When** un developpeur refactore l'etat (messages, conversations, currentConversationId, isStreaming, sseReader) au niveau module (hors de la fonction useChat())
**Then** toutes les refs sont declarees au niveau module et useChat() retourne toujours les memes references partagees
**And** un AbortController est stocke en ref module-level pour annulation propre du stream

**Given** l'utilisateur est sur la page /dashboard et un streaming SSE est en cours
**When** l'utilisateur navigue vers la page /esg
**Then** le streaming SSE continue sans interruption (pas de reconnexion)
**And** les messages deja recus restent affiches
**And** les nouveaux tokens arrivent normalement (latence de reprise < 100ms — NFR7)

**Given** l'utilisateur navigue entre 3 pages differentes pendant une conversation
**When** il revient sur la premiere page
**Then** l'historique complet de la conversation est intact

**Given** le refactoring est termine
**When** on execute la suite de tests existante
**Then** zero regression — tous les tests frontend et backend passent (NFR19)

**Exigences techniques :**
- ADR1 : pattern singleton module-level state
- ADR2 : reader SSE en ref module-level, AbortController
- Aucune modification des 13 composants chat existants
- Tests unitaires Vitest pour la persistance cross-routes (couverture >= 80%)
- Dark mode : N/A (pas de composant visuel)

---

### Story 1.2 : Composable useDeviceDetection

En tant qu'utilisateur sur mobile,
je veux que la plateforme detecte automatiquement mon type d'ecran,
afin de ne pas voir un widget flottant inadapte a mon appareil.

**Acceptance Criteria:**

**Given** un ecran de largeur >= 1024px
**When** le composable useDeviceDetection est appele
**Then** isDesktop retourne true et isMobile retourne false

**Given** un ecran de largeur < 1024px
**When** le composable useDeviceDetection est appele
**Then** isDesktop retourne false et isMobile retourne true

**Given** l'utilisateur est sur un ecran desktop (>= 1024px)
**When** il redimensionne la fenetre en dessous de 1024px
**Then** isDesktop passe a false en temps reel (listener matchMedia)

**Given** l'utilisateur est sur mobile
**When** il charge n'importe quelle page
**Then** aucun composant copilot (widget, bouton flottant) n'est rendu dans le DOM

**Exigences techniques :**
- Composable dans composables/useDeviceDetection.ts
- Basé sur window.matchMedia('(min-width: 1024px)') avec addEventListener('change')
- Cleanup du listener dans onUnmounted
- Tests unitaires Vitest (couverture >= 80%)

---

### Story 1.3 : Bouton flottant et conteneur du widget

En tant qu'utilisateur sur desktop,
je veux voir un bouton flottant en bas a droite et pouvoir ouvrir un widget de chat elegant,
afin d'acceder a l'assistant IA sans quitter la page que je consulte.

**Acceptance Criteria:**

**Given** l'utilisateur est sur n'importe quelle page desktop
**When** la page se charge
**Then** un bouton flottant (FAB) est visible en bas a droite avec le label accessible « Ouvrir l'assistant IA »

**Given** le bouton flottant est visible
**When** l'utilisateur clique dessus
**Then** le widget FloatingChatWidget s'ouvre avec une animation GSAP (duree < 300ms — NFR1)
**And** le fond du widget est glassmorphism (backdrop-filter: blur >= 12px — NFR8)
**And** le contenu de la page est visible mais les donnees financieres sont illisibles a travers le blur

**Given** le navigateur ne supporte pas backdrop-filter
**When** le widget s'ouvre
**Then** un fond opaque est affiche via @supports (FR8)
**And** le contraste des textes respecte WCAG AA >= 4.5:1 (NFR12)

**Given** le widget est ouvert
**When** l'utilisateur clique sur le bouton de fermeture ou sur le FAB
**Then** le widget se ferme avec animation GSAP

**Given** le dark mode est actif
**When** le widget est affiche
**Then** tous les elements utilisent les variantes dark: de Tailwind (bg-dark-card, text-surface-dark-text, border-dark-border, etc.)

**Given** prefers-reduced-motion est actif
**When** le widget s'ouvre ou se ferme
**Then** les animations GSAP sont desactivees (duree 0ms, transition instantanee)

**Given** le FPS de la page avec le widget ouvert et le scroll actif
**When** on mesure la performance
**Then** le FPS reste >= 30 (NFR6)

**Exigences techniques :**
- Composants dans components/copilot/ : FloatingChatButton.vue, FloatingChatWidget.vue
- Monte dans layouts/default.vue, conditionne par useDeviceDetection().isDesktop
- Extension du store ui.ts : chatWidgetOpen (boolean)
- Animation GSAP via le plugin gsap.client.ts existant
- Dark mode complet obligatoire
- Tests unitaires Vitest (couverture >= 80%)

---

### Story 1.4 : En-tete du widget et historique des conversations

En tant qu'utilisateur,
je veux gerer mes conversations depuis le widget flottant (voir l'historique, creer une nouvelle conversation),
afin de retrouver mes echanges passes et organiser mes demandes.

**Acceptance Criteria:**

**Given** le widget est ouvert
**When** l'en-tete s'affiche
**Then** il contient un titre, un bouton fermer, un bouton reduire, et un bouton d'acces a l'historique

**Given** le widget affiche la conversation courante
**When** l'utilisateur clique sur le bouton historique
**Then** la liste des conversations passees s'affiche (compose ConversationList.vue existant)
**And** l'utilisateur peut cliquer sur une conversation pour y basculer (FR5)

**Given** la liste des conversations est affichee
**When** l'utilisateur clique sur « Nouvelle conversation »
**Then** une nouvelle conversation est creee et devient la conversation active (FR6)

**Given** le dark mode est actif
**When** l'en-tete et la liste des conversations sont affiches
**Then** tous les elements respectent le theme dark

**Exigences techniques :**
- Composant components/copilot/ChatWidgetHeader.vue
- Reutilisation de components/chat/ConversationList.vue par composition (pas de modification)
- Tests unitaires Vitest (couverture >= 80%)

---

### Story 1.5 : Integration du chat complet dans le widget

En tant qu'utilisateur,
je veux retrouver toutes les fonctionnalites du chat (messages, streaming, upload, widgets interactifs, rich blocks) dans le widget flottant,
afin d'avoir une experience identique a l'ancien panneau lateral.

**Acceptance Criteria:**

**Given** le widget est ouvert
**When** l'utilisateur tape un message et l'envoie
**Then** le message est envoye via useChat().sendMessage() et la reponse streamee s'affiche en temps reel (FR2)

**Given** le widget est ouvert
**When** l'utilisateur uploade un document (PDF, DOCX, XLSX, image)
**Then** le fichier est traite et la reponse de l'assistant s'affiche dans le widget (FR3)

**Given** l'assistant envoie un widget interactif (QCU/QCM, feature 018)
**When** le widget s'affiche dans le chat
**Then** l'utilisateur peut interagir avec le widget identiquement a l'ancien ChatPanel (FR9, NFR20)

**Given** l'assistant envoie un rich block (chart, table, gauge, mermaid, timeline)
**When** le bloc s'affiche dans le widget
**Then** il est rendu correctement avec scroll horizontal si necessaire (FR10)

**Given** un tool call est en cours
**When** l'indicateur ToolCallIndicator s'affiche
**Then** il est visible et lisible dans le widget

**Given** le dark mode est actif
**When** tous les composants chat sont affiches dans le widget
**Then** le rendu dark mode est identique a l'ancien ChatPanel

**Exigences techniques :**
- Composition des 13 composants chat existants dans FloatingChatWidget.vue
- Aucune modification des composants dans components/chat/
- ChatInput, ChatMessage, MessageParser, ToolCallIndicator, ProfileNotification, WelcomeMessage, InteractiveQuestionHost, SingleChoiceWidget, MultipleChoiceWidget, JustificationField, AnswerElsewhereButton, InteractiveQuestionInputBar
- Tests unitaires Vitest (couverture >= 80%)

---

### Story 1.6 : Redimensionnement du widget

En tant qu'utilisateur,
je veux pouvoir redimensionner le widget de chat,
afin d'adapter sa taille au contenu que je consulte (tableaux, graphiques).

**Acceptance Criteria:**

**Given** le widget est ouvert
**When** l'utilisateur drag le bord ou le coin du widget
**Then** le widget se redimensionne en suivant le curseur
**And** la taille respecte les limites min (300x400) et max (largeur ecran - 100, hauteur ecran - 100)

**Given** l'utilisateur a redimensionne le widget
**When** il ferme et reouvre le widget
**Then** la taille personnalisee est restauree (persistance localStorage)

**Given** l'utilisateur a redimensionne le widget
**When** il navigue vers une autre page
**Then** la taille du widget est preservee

**Given** le widget est utilise avec prefers-reduced-motion actif
**When** l'utilisateur redimensionne
**Then** le redimensionnement fonctionne sans animation de transition

**Given** le widget est monte en permanence dans le layout
**When** on mesure la memoire consommee
**Then** l'overhead est < 5 MB (NFR5)

**Exigences techniques :**
- Logique de resize dans FloatingChatWidget.vue (pointer events)
- Persistance taille dans localStorage (cle esg_mefali_widget_size)
- Extension store ui.ts : chatWidgetSize ({ width, height })
- Tests unitaires Vitest (couverture >= 80%)

---

### Story 1.7 : Accessibilite et navigation clavier du widget

En tant qu'utilisateur naviguant au clavier ou utilisant un lecteur d'ecran,
je veux que le widget soit entierement accessible,
afin de pouvoir utiliser l'assistant IA sans souris.

**Acceptance Criteria:**

**Given** le widget est ferme
**When** l'utilisateur navigue via Tab
**Then** le bouton flottant est atteignable et porte le label aria « Ouvrir l'assistant IA » (NFR15)

**Given** le widget est ouvert
**When** l'utilisateur appuie sur Tab
**Then** le focus est piege dans le widget (focus trap) et cycle entre les elements interactifs (NFR13)

**Given** le widget est ouvert
**When** l'utilisateur appuie sur Escape
**Then** le widget se ferme et le focus retourne au bouton flottant

**Given** l'assistant envoie un nouveau message
**When** le message s'affiche dans le widget
**Then** il est annonce par le lecteur d'ecran via aria-live (NFR15)

**Given** le glassmorphism est actif
**When** on mesure le contraste des textes du widget
**Then** le ratio est >= 4.5:1 sur fond glassmorphism ET sur fond opaque fallback (NFR12)

**Exigences techniques :**
- Focus trap : implementation dans FloatingChatWidget.vue
- aria-live="polite" sur le conteneur de messages
- role="dialog" + aria-label sur le widget
- Tests unitaires Vitest pour le focus trap et les attributs ARIA (couverture >= 80%)

---

## Epic 2 : Migration et suppression de la page /chat

L'interface est unifiee — plus de duplication entre la page /chat et le widget flottant. La navigation est coherente et sans confusion.

### Story 2.1 : Suppression de la page /chat et de ChatPanel

En tant qu'utilisateur,
je veux une seule interface de chat (le widget flottant),
afin de ne pas etre perdu entre deux points d'acces differents a l'assistant.

**Acceptance Criteria:**

**Given** le fichier pages/chat.vue existe
**When** un developpeur le supprime
**Then** la route /chat n'est plus accessible (404 ou redirection)
**And** aucune regression dans le routing Nuxt des autres pages

**Given** le composant components/layout/ChatPanel.vue existe
**When** un developpeur le supprime
**Then** layouts/default.vue ne reference plus ChatPanel
**And** le FloatingChatWidget (Epic 1) est le seul point d'acces au chat dans le layout

**Given** la suppression est effectuee
**When** on execute la suite de tests existante
**Then** zero regression — tous les tests frontend passent (NFR19)
**And** les tests qui referençaient ChatPanel ou la page /chat sont mis a jour ou supprimes

**Exigences techniques :**
- Suppression : pages/chat.vue, components/layout/ChatPanel.vue
- Modification : layouts/default.vue (retrait de ChatPanel, conservation de FloatingChatWidget)
- Mise a jour des tests impactes
- Dark mode : N/A (suppression uniquement)
- Tests : verification zero regression (couverture >= 80%)

---

### Story 2.2 : Mise a jour de la navigation et des liens internes

En tant qu'utilisateur,
je veux que tous les liens et boutons qui menaient a /chat ouvrent desormais le widget flottant,
afin que la navigation reste coherente et intuitive.

**Acceptance Criteria:**

**Given** un lien vers /chat existe dans AppSidebar
**When** un developpeur met a jour la navigation
**Then** le lien est remplace par un bouton qui ouvre le widget flottant (uiStore.chatWidgetOpen = true)
**Or** le lien est supprime si redondant avec le bouton FAB

**Given** un lien vers /chat existe dans AppHeader ou tout autre composant
**When** un developpeur effectue une recherche globale de '/chat' et 'chat.vue'
**Then** toutes les references sont mises a jour ou supprimees

**Given** un utilisateur tape /chat dans la barre d'adresse
**When** la page se charge
**Then** il est redirige vers / (ou la derniere page visitee) et le widget flottant s'ouvre automatiquement

**Given** le dark mode est actif
**When** les elements de navigation mis a jour sont affiches
**Then** ils respectent le theme dark existant

**Exigences techniques :**
- Recherche globale : grep '/chat', 'to="/chat"', 'href="/chat"', 'navigateTo.*chat'
- Ajout d'un middleware ou redirect Nuxt pour /chat → / + ouverture widget
- Tests unitaires Vitest (couverture >= 80%)

---

## Epic 3 : Conscience contextuelle du LLM

L'assistant sait sur quelle page se trouve l'utilisateur et adapte ses reponses en consequence — il ne propose plus des actions hors-contexte.

### Story 3.1 : Transmission de la page courante au backend

En tant qu'utilisateur,
je veux que l'assistant sache sur quelle page je me trouve,
afin qu'il puisse me donner des reponses adaptees a mon contexte de navigation.

**Acceptance Criteria:**

**Given** l'utilisateur est sur la page /carbon/results
**When** le FloatingChatWidget est monte dans le layout
**Then** uiStore.currentPage est mis a jour avec '/carbon/results'

**Given** l'utilisateur navigue de /dashboard vers /esg
**When** la route change
**Then** uiStore.currentPage est mis a jour en temps reel avec '/esg'

**Given** l'utilisateur envoie un message depuis le widget
**When** useChat.sendMessage() construit le FormData
**Then** le champ 'current_page' est present avec la valeur de uiStore.currentPage

**Given** le backend recoit une requete POST /api/chat/messages avec current_page
**When** le message est traite
**Then** current_page est stocke dans ConversationState et accessible par tous les noeuds LangGraph

**Given** le champ current_page est ajoute a ConversationState
**When** on verifie le mecanisme active_module existant
**Then** les deux champs coexistent sans conflit (NFR22) — current_page est informatif, active_module est decisif pour le routage

**Given** le refactoring est termine
**When** on execute les 935+ tests backend
**Then** zero regression (NFR19)

**Exigences techniques :**
- Frontend : watch(route.path) dans le layout ou FloatingChatWidget → uiStore.currentPage
- Extension store ui.ts : currentPage (string)
- Modification useChat.ts : ajout current_page au FormData dans sendMessage()
- Backend : modification app/api/chat.py pour extraire current_page du FormData
- Backend : modification app/graph/state.py — ajout current_page: str | None dans ConversationState
- Tests unitaires pytest + Vitest (couverture >= 80%)
- Dark mode : N/A (pas de composant visuel)

---

### Story 3.2 : Injection de la page courante dans les prompts et adaptation des reponses

En tant qu'utilisateur,
je veux que l'assistant adapte ses reponses en fonction de la page que je consulte,
afin de recevoir des conseils pertinents et contextuels.

**Acceptance Criteria:**

**Given** current_page est '/carbon/results' dans ConversationState
**When** le LLM genere une reponse via chat_node
**Then** le prompt systeme contient l'information de la page courante
**And** le LLM peut adapter son discours (ex: « Je vois que vous consultez vos resultats carbone... »)

**Given** current_page est '/dashboard' et l'utilisateur vient de completer un module ESG
**When** le LLM genere une reponse
**Then** il peut proposer un guidage vers les resultats ESG (FR13 — la proposition textuelle, pas le declenchement technique qui est dans l'Epic 6)

**Given** current_page est null ou vide (premier message, erreur)
**When** le LLM genere une reponse
**Then** il repond normalement sans contexte de page (degradation gracieuse)

**Given** le mecanisme active_module est actif (ex: esg_scoring en cours)
**When** current_page change parce que l'utilisateur navigue
**Then** active_module n'est pas affecte — le routage LangGraph continue de suivre active_module

**Exigences techniques :**
- Nouveau fichier ou extension dans prompts/ : instruction PAGE_CONTEXT_INSTRUCTION
- Injection dans les prompts systeme des noeuds LangGraph concernes (chat_node au minimum, potentiellement les 7 noeuds qui triggereront le guidage dans l'Epic 6)
- Tests unitaires pytest : verification presence current_page dans le prompt, test degradation gracieuse (couverture >= 80%)
- Dark mode : N/A (backend uniquement)

---

## Epic 4 : Infrastructure de guidage visuel

Le systeme est pret a montrer visuellement les elements de l'interface a l'utilisateur — les composants existants sont marques et le catalogue de parcours est en place.

### Story 4.1 : Installation Driver.js, lazy loading et CSS dark mode

En tant que developpeur,
je veux que Driver.js soit disponible en import dynamique sans impacter le bundle initial,
afin que le premier parcours guide demarre en < 500ms sans penaliser le chargement des pages.

**Acceptance Criteria:**

**Given** Driver.js n'est pas encore installe dans le projet
**When** un developpeur ajoute la dependance et configure le lazy loading
**Then** Driver.js est installe dans package.json
**And** un module-level cache (driverModule) stocke l'import pour ne le charger qu'une seule fois

**Given** le FloatingChatWidget est monte
**When** onMounted est execute
**Then** prefetchDriverJs() est appele via requestIdleCallback pour pre-charger Driver.js en arriere-plan

**Given** le bundle initial est construit
**When** on analyse la taille du bundle (npm run build + analyse)
**Then** Driver.js n'apparait pas dans le chunk initial — 0 Ko ajoute (NFR4)

**Given** Driver.js est pre-charge en cache
**When** loadDriver() est appele pour la premiere fois
**Then** le module est retourne immediatement depuis le cache (< 500ms total — NFR2)

**Given** le CSS de Driver.js est necessaire
**When** main.css est charge
**Then** @import 'driver.js/dist/driver.css' est present (~2 Ko, acceptable)
**And** les overrides dark mode sont definis (.dark .driver-popover avec bg-dark-card, text-surface-dark-text, border-dark-border)

**Given** le dark mode est actif
**When** un popover Driver.js est affiche
**Then** il respecte le theme dark via les overrides CSS

**Exigences techniques :**
- npm install driver.js
- Fonctions prefetchDriverJs() et loadDriver() dans composables/useGuidedTour.ts (ou un fichier utilitaire dedie)
- CSS : @import dans app/assets/css/main.css + overrides .dark .driver-popover
- Tests unitaires Vitest : mock de l'import dynamique, verification du cache (couverture >= 80%)

---

### Story 4.2 : Types et registre de parcours guides

En tant que developpeur,
je veux un registre extensible de parcours guides avec des types TypeScript stricts,
afin d'ajouter de nouveaux parcours sans modifier le moteur de guidage.

**Acceptance Criteria:**

**Given** les types n'existent pas encore
**When** un developpeur cree types/guided-tour.ts
**Then** les interfaces suivantes sont definies : GuidedTourStep (route?, selector, popover, countdown?), GuidedTourDefinition (id, steps[], entryStep?), TourContext (Record<string, unknown>), TourState ('idle' | 'loading' | 'ready' | 'navigating' | 'waiting_dom' | 'highlighting' | 'complete' | 'interrupted')

**Given** le registre n'existe pas encore
**When** un developpeur cree lib/guided-tours/registry.ts
**Then** tourRegistry est un Record<string, GuidedTourDefinition> contenant 6 parcours pre-definis

**Given** les 6 parcours pre-definis
**When** on les inspecte
**Then** chacun a un id unique suivant la convention show_[module]_[page] en snake_case :
- show_esg_results (score, forces/faiblesses, recommandations)
- show_carbon_results (donut, benchmark, plan reduction)
- show_financing_catalog (catalogue fonds)
- show_credit_score (score credit vert)
- show_action_plan (timeline plan d'action)
- show_dashboard_overview (vue d'ensemble tableau de bord)

**Given** un parcours contient des placeholders dans ses textes (ex: '{{total_tco2}} tCO2e')
**When** un TourContext est fourni avec les valeurs correspondantes
**Then** les textes sont interpolables (la logique d'interpolation sera dans useGuidedTour, Epic 5)

**Given** un developpeur veut ajouter un 7eme parcours
**When** il ajoute une entree dans tourRegistry
**Then** le parcours est disponible sans modifier aucun autre fichier (FR28)

**Exigences techniques :**
- Fichiers : types/guided-tour.ts, lib/guided-tours/registry.ts
- Convention selectors : [data-guide-target="xxx"] uniquement, jamais de classes CSS ou IDs
- Convention entryStep : pour les parcours multi-pages, definit l'etape de navigation initiale (sidebar link + countdown)
- Textes en francais avec accents
- Tests unitaires Vitest : validation structure registre, presence des 6 parcours, unicite des ids (couverture >= 80%)

---

### Story 4.3 : Marquage data-guide-target sur les composants existants

En tant qu'utilisateur,
je veux que les elements importants de l'interface soient identifiables par le systeme de guidage,
afin que l'assistant puisse me les montrer visuellement.

**Acceptance Criteria:**

**Given** les composants existants n'ont pas d'attributs data-guide-target
**When** un developpeur ajoute les attributs selon la convention [module]-[element] en kebab-case
**Then** les elements suivants sont marques (liste non exhaustive, a completer selon les composants reels) :
- Sidebar : sidebar-esg-link, sidebar-carbon-link, sidebar-financing-link, sidebar-credit-link, sidebar-action-plan-link, sidebar-dashboard-link
- ESG : esg-score-circle, esg-strengths-badges, esg-recommendations
- Carbon : carbon-donut-chart, carbon-benchmark, carbon-reduction-plan
- Financing : financing-fund-list
- Credit : credit-score-gauge
- Action Plan : action-plan-timeline
- Dashboard : dashboard-esg-card, dashboard-carbon-card, dashboard-credit-card, dashboard-financing-card

**Given** un attribut data-guide-target est ajoute a un composant
**When** le composant est rendu dans le DOM
**Then** document.querySelector('[data-guide-target="xxx"]') retourne l'element

**Given** les attributs sont ajoutes
**When** on execute les tests frontend existants
**Then** zero regression — aucun test casse (ajout d'attribut HTML n'impacte pas le comportement)

**Given** les attributs sont ajoutes
**When** on compare avec les selectors definis dans tourRegistry (Story 4.2)
**Then** chaque selector du registre a un data-guide-target correspondant dans les composants

**Exigences techniques :**
- Modification de ~15 composants existants : ajout d'un attribut data-guide-target sur l'element pertinent
- Aucune modification de logique, style, ou comportement des composants
- Convention stricte : [module]-[element] en kebab-case
- Tests unitaires Vitest : verification presence des attributs dans le DOM rendu (couverture >= 80%)

---

## Epic 5 : Parcours guides et navigation multi-pages

L'utilisateur peut suivre des parcours guides visuels complets — le systeme pointe les elements importants, navigue entre les pages avec decompteur, et le widget se retracte/reapparait fluidement.

### Story 5.1 : Composable useGuidedTour — machine a etats et execution mono-page

En tant qu'utilisateur,
je veux que le systeme puisse mettre en surbrillance des elements de l'interface avec des explications,
afin de comprendre visuellement ou se trouvent les informations importantes.

**Acceptance Criteria:**

**Given** le composable useGuidedTour n'existe pas encore
**When** un developpeur le cree dans composables/useGuidedTour.ts
**Then** il expose : startTour(tourId, context?), cancelTour(), tourState (ref<TourState>)
**And** l'etat est declare au niveau module (persistance cross-routes, coherent avec ADR3)

**Given** startTour('show_carbon_results') est appele et l'utilisateur est deja sur /carbon/results
**When** le parcours demarre
**Then** Driver.js est charge via loadDriver() (cache si deja prefetche)
**And** le parcours est resolu depuis tourRegistry
**And** les placeholders du contexte sont interpoles dans les textes des popovers
**And** l'etat passe idle → loading → highlighting

**Given** le parcours est en cours sur la page courante
**When** Driver.js affiche les etapes sequentiellement
**Then** chaque popover s'affiche en < 200ms apres le precedent (NFR3)
**And** les textes sont en francais avec accents

**Given** un element cible n'est pas trouve dans le DOM
**When** waitForElement(selector) est appele
**Then** le systeme retente 3 fois avec 500ms d'intervalle
**And** si l'element est trouve, l'etape continue normalement
**And** si l'element n'est pas trouve apres 3 tentatives, l'etape est skippee et un message est ajoute via useChat().addSystemMessage() (« Je n'ai pas pu pointer cet element. Passons a la suite. »)

**Given** toutes les etapes du parcours sont terminees
**When** le parcours se finalise
**Then** driver.destroy() est appele
**And** l'etat passe a 'complete'

**Given** la methode addSystemMessage n'existe pas encore dans useChat
**When** un developpeur l'ajoute
**Then** elle insere un message local (non envoye au LLM) dans la liste des messages affiches

**Exigences techniques :**
- Fichier : composables/useGuidedTour.ts
- Machine a etats module-level : idle → loading → ready → highlighting → complete | interrupted
- Interpolation templates : regex /\{\{(\w+)\}\}/g replacee par context[key]
- Ajout methode addSystemMessage() dans useChat.ts
- Tests unitaires Vitest : machine a etats, interpolation, retry waitForElement, addSystemMessage (couverture >= 80%)

---

### Story 5.2 : Retraction et reapparition animee du widget pendant le guidage

En tant qu'utilisateur,
je veux que le widget de chat se retracte automatiquement pendant un parcours guide,
afin de ne pas masquer les elements que le systeme me montre.

**Acceptance Criteria:**

**Given** un parcours guide demarre via startTour()
**When** useGuidedTour met a jour uiStore
**Then** uiStore.guidedTourActive passe a true
**And** uiStore.chatWidgetMinimized passe a true

**Given** uiStore.chatWidgetMinimized passe a true
**When** FloatingChatWidget observe le changement
**Then** le widget se retracte en bouton FAB reduit avec animation GSAP (scale: 1→0.3, opacity: 1→0.8, duree: 250ms)
**And** l'animation GSAP se termine AVANT que Driver.js ne demarre (sequence par promesse)

**Given** le parcours guide se termine (complete ou interrupted)
**When** useGuidedTour met a jour uiStore
**Then** uiStore.chatWidgetMinimized passe a false
**And** uiStore.guidedTourActive passe a false

**Given** uiStore.chatWidgetMinimized passe a false
**When** FloatingChatWidget observe le changement
**Then** le widget reapparait avec animation GSAP (scale: 0.3→1, opacity: 0.8→1, duree: 250ms)

**Given** prefers-reduced-motion est actif
**When** le widget se retracte ou reapparait
**Then** les animations GSAP sont desactivees (duree 0ms, transition instantanee — NFR14)

**Given** le widget est retracte (minimized)
**When** l'utilisateur clique sur le bouton FAB reduit
**Then** rien ne se passe (le widget ne s'ouvre pas pendant un guidage actif)

**Exigences techniques :**
- Extension store ui.ts : chatWidgetMinimized (boolean), guidedTourActive (boolean)
- Watchers dans FloatingChatWidget.vue : watch(chatWidgetMinimized) → animation GSAP
- Sequence promesse : retract() retourne une Promise resolue dans onComplete GSAP
- Dans useGuidedTour : await retractWidget() avant de lancer Driver.js
- Verification uiStore.guidedTourActive avant ouverture widget
- Tests unitaires Vitest : retraction, reapparition, blocage ouverture pendant guidage (couverture >= 80%)

---

### Story 5.3 : Navigation multi-pages avec decompteur

En tant qu'utilisateur,
je veux que le parcours guide puisse me diriger vers une autre page avec un decompteur visuel,
afin d'etre accompagne meme quand les informations sont sur une page differente.

**Acceptance Criteria:**

**Given** le parcours a une etape dont step.route !== currentRoute (ex: entryStep avec targetRoute '/carbon/results')
**When** l'etape est atteinte
**Then** l'etat passe a 'navigating'
**And** Driver.js highlight le lien de navigation (ex: sidebar-carbon-link) avec un popover contenant un CountdownBadge

**Given** le popover avec decompteur est affiche
**When** le decompteur demarre (defaut 8 secondes, configurable par etape)
**Then** le badge affiche le compte a rebours visuellement (secondes restantes)
**And** le texte du popover invite a cliquer sur le lien

**Given** l'utilisateur clique sur le lien avant l'expiration du decompteur
**When** la navigation Nuxt s'execute (router.push)
**Then** le decompteur s'arrete
**And** l'etat passe a 'waiting_dom'

**Given** le decompteur expire sans clic de l'utilisateur
**When** le timer atteint 0
**Then** la navigation est declenchee automatiquement via router.push(step.targetRoute) (FR22)
**And** l'etat passe a 'waiting_dom'

**Given** la navigation est effectuee (clic ou auto)
**When** la page cible se charge
**Then** le systeme attend nextTick() + polling de l'element cible (waitForElement)
**And** si l'element est trouve en < 5s, l'etat passe a 'highlighting' et le parcours reprend (FR23)
**And** si l'element n'est pas trouve en 5s, retry silencieux
**And** si l'element n'est pas trouve en 10s, le parcours s'interrompt avec message d'erreur dans le chat (NFR16)

**Given** le dark mode est actif
**When** le CountdownBadge est affiche
**Then** il respecte le theme dark

**Exigences techniques :**
- Composant components/copilot/CountdownBadge.vue : badge avec timer visuel, props countdown (number), emit expired
- Extension useGuidedTour : logique navigation cross-pages, watch route.path pour detecter l'arrivee, timeout 5s/10s
- Dark mode complet sur CountdownBadge
- Tests unitaires Vitest : decompteur, navigation auto a expiration, attente DOM, timeout (couverture >= 80%)

---

### Story 5.4 : Interruption du parcours et popover custom

En tant qu'utilisateur,
je veux pouvoir interrompre un parcours guide a tout moment et voir des popovers bien designes,
afin de garder le controle de mon experience sans me sentir piege.

**Acceptance Criteria:**

**Given** un parcours guide est en cours
**When** l'utilisateur appuie sur Escape
**Then** le parcours s'interrompt immediatement
**And** driver.destroy() est appele
**And** le widget reapparait (uiStore.chatWidgetMinimized = false)
**And** l'etat passe a 'interrupted'
**And** aucun message n'est ajoute au chat (action volontaire de l'utilisateur — FR25)

**Given** un parcours guide est en cours
**When** l'utilisateur clique hors de la zone highlight/popover
**Then** le comportement est identique a Escape (interruption propre)

**Given** le popover custom GuidedTourPopover est affiche
**When** l'utilisateur le consulte
**Then** il affiche le titre et la description en francais avec accents
**And** il integre le CountdownBadge si l'etape a un countdown
**And** le design est coherent avec le style de la plateforme (arrondi, ombres, typographie)

**Given** le dark mode est actif
**When** les popovers sont affiches
**Then** ils utilisent les couleurs dark (bg-dark-card, text-surface-dark-text, border-dark-border)

**Given** prefers-reduced-motion est actif
**When** Driver.js affiche les popovers
**Then** animate: false est passe dans la configuration Driver.js (NFR14)

**Given** le parcours est interrompu ou termine
**When** le cleanup s'execute
**Then** aucun overlay, popover, ou classe CSS de Driver.js ne reste dans le DOM

**Exigences techniques :**
- Composant components/copilot/GuidedTourPopover.vue : template custom pour Driver.js popoverRender
- Integration dans useGuidedTour : callbacks Driver.js onDestroyStarted, onDestroyed, onHighlightStarted
- Configuration Driver.js : animate (conditionne par prefers-reduced-motion), allowClose: true
- Dark mode complet sur GuidedTourPopover
- Tests unitaires Vitest : interruption Escape, interruption clic hors zone, cleanup DOM, dark mode popover (couverture >= 80%)

---

## Epic 6 : Declenchement intelligent par le LLM et consentement

L'assistant propose des guidages au bon moment (fin de module, demande explicite) et respecte le choix de l'utilisateur via un consentement clair. La frequence s'adapte au comportement.

### Story 6.1 : Tool LangChain trigger_guided_tour et marker SSE

En tant qu'utilisateur,
je veux que l'assistant puisse declencher un parcours guide visuel depuis le chat,
afin d'etre accompagne visuellement sans manipulation manuelle.

**Acceptance Criteria:**

**Given** le tool trigger_guided_tour n'existe pas encore
**When** un developpeur le cree dans graph/tools/guided_tour_tools.py
**Then** le tool accepte tour_id (str) et context (dict | None)
**And** il retourne un marker SSE au format <!--SSE:{"__sse_guided_tour__":true,"tour_id":"...","context":{}}-->
**And** aucune donnee sensible (scores, montants, IDs utilisateur) ne transite dans le marker (NFR10)

**Given** le tool est appele par un noeud LangGraph
**When** stream_graph_events detecte le marker __sse_guided_tour__ dans le contenu
**Then** il emet un event SSE au format {"event": "guided_tour", "tour_id": "...", "context": {...}}

**Given** le frontend recoit un event SSE de type 'guided_tour'
**When** useChat parse l'event
**Then** useGuidedTour().startTour(tour_id, context) est appele automatiquement

**Given** le tool est appele avec un tour_id invalide (pas dans le registre)
**When** useGuidedTour recoit l'appel
**Then** le parcours est ignore silencieusement et un message d'erreur est ajoute dans le chat via addSystemMessage()

**Given** le tool est utilise en production
**When** on verifie les logs
**Then** l'appel est journalise dans tool_call_logs suivant le pattern existant (NFR21)
**And** les events SSE tool_call_start et tool_call_end sont emis

**Exigences techniques :**
- Backend : graph/tools/guided_tour_tools.py (nouveau fichier, pattern identique aux 12 fichiers existants)
- Backend : modification stream_graph_events dans api/chat.py — detection __sse_guided_tour__
- Frontend : modification useChat.ts — case 'guided_tour' dans le parser d'events SSE
- Convention marker : __sse_guided_tour__ (double underscore, snake_case)
- Tests unitaires pytest : tool output, marker detection, event emission (couverture >= 80%)
- Tests unitaires Vitest : parsing event, appel startTour (couverture >= 80%)

---

### Story 6.2 : Prompt GUIDED_TOUR_INSTRUCTION et injection dans les noeuds LangGraph

En tant qu'utilisateur,
je veux que l'assistant sache quels parcours guides sont disponibles et quand les proposer,
afin de recevoir des suggestions de guidage pertinentes au bon moment.

**Acceptance Criteria:**

**Given** le prompt GUIDED_TOUR_INSTRUCTION n'existe pas encore
**When** un developpeur le cree dans prompts/guided_tour.py
**Then** il contient la liste des 6 parcours disponibles avec leurs identifiants (show_esg_results, show_carbon_results, show_financing_catalog, show_credit_score, show_action_plan, show_dashboard_overview)
**And** il definit les regles de declenchement : proposer UNIQUEMENT apres completion d'un module ou sur demande explicite
**And** il precise d'utiliser ask_interactive_question pour le consentement (sauf demande explicite)

**Given** le prompt est cree
**When** les noeuds LangGraph sont configures
**Then** GUIDED_TOUR_INSTRUCTION est injecte dans les prompts systeme de 7 noeuds : chat_node, esg_scoring_node, carbon_node, financing_node, credit_node, action_plan_node
**And** les noeuds application_node, document_node, profiling_node, router_node ne recoivent PAS le prompt

**Given** esg_scoring_node termine une evaluation ESG
**When** le LLM genere sa reponse finale
**Then** il peut proposer textuellement un guidage et utiliser le tool trigger_guided_tour si l'utilisateur accepte

**Given** chat_node recoit « montre-moi mes resultats carbone »
**When** le LLM analyse la demande
**Then** il detecte l'intent de guidage et peut declencher trigger_guided_tour('show_carbon_results') directement

**Given** le prompt est injecte
**When** on execute les tests backend existants
**Then** zero regression (NFR19)

**Exigences techniques :**
- Nouveau fichier : prompts/guided_tour.py avec GUIDED_TOUR_INSTRUCTION
- Modification : injection dans les prompts systeme des 7 noeuds dans graph/nodes.py (ou fichiers de prompts individuels)
- Pattern identique a WIDGET_INSTRUCTION (feature 018) et STYLE_INSTRUCTION (feature 014)
- Tests unitaires pytest : presence du prompt dans les noeuds autorises, absence dans les noeuds non autorises (couverture >= 80%)

---

### Story 6.3 : Consentement via widget interactif et declenchement direct

En tant qu'utilisateur,
je veux choisir si j'accepte un guidage propose par l'assistant via un choix clair,
afin de garder le controle de mon experience sans etre force.

**Acceptance Criteria:**

**Given** le LLM decide de proposer un guidage apres completion d'un module
**When** il genere sa reponse
**Then** il appelle d'abord ask_interactive_question avec 2 options : « Oui, montre-moi » et « Non merci » (reutilisation SingleChoiceWidget, feature 018)

**Given** l'utilisateur clique sur « Oui, montre-moi »
**When** la reponse est renvoyee au LLM
**Then** le LLM appelle trigger_guided_tour avec le tour_id correspondant
**And** le parcours guide demarre (FR14)

**Given** l'utilisateur clique sur « Non merci »
**When** la reponse est renvoyee au LLM
**Then** le LLM ne declenche pas de guidage
**And** il continue la conversation normalement

**Given** l'utilisateur tape « montre-moi mes resultats ESG » (demande explicite)
**When** le LLM analyse le message
**Then** il detecte l'intent de guidage explicite
**And** il appelle trigger_guided_tour('show_esg_results') SANS afficher le widget de consentement (FR15, FR16)

**Given** l'utilisateur tape « guide-moi vers le plan d'action »
**When** le LLM analyse le message
**Then** il detecte l'intent et declenche trigger_guided_tour('show_action_plan') directement

**Exigences techniques :**
- Pas de nouveau composant — reutilisation de SingleChoiceWidget existant via ask_interactive_question
- La logique de detection d'intent explicite est dans les prompts (GUIDED_TOUR_INSTRUCTION)
- Tests unitaires pytest : flux consentement accepte, consentement refuse, declenchement direct (couverture >= 80%)

---

### Story 6.4 : Frequence adaptative des propositions de guidage

En tant qu'utilisateur,
je veux que l'assistant reduise ses propositions de guidage si je les refuse souvent,
afin de ne pas etre importune par des suggestions repetitives.

**Acceptance Criteria:**

**Given** l'utilisateur a refuse 0 guidages
**When** le LLM propose un guidage
**Then** la proposition est affichee normalement

**Given** l'utilisateur a refuse 3 guidages consecutifs
**When** le LLM envisage de proposer un guidage
**Then** le contexte transmis au LLM contient guidance_refusal_count >= 3
**And** le prompt GUIDED_TOUR_INSTRUCTION indique de reduire les propositions (ne proposer que sur demande explicite ou apres un nouveau module complete)

**Given** l'utilisateur a accepte plusieurs guidages
**When** un nouveau parcours avec decompteur demarre
**Then** la duree du decompteur est reduite (ex: 8s → 5s apres 3 acceptations — FR17)

**Given** l'utilisateur accepte un guidage apres une serie de refus
**When** le guidage est complete
**Then** le compteur de refus est reinitialise

**Given** l'utilisateur ferme et reouvre le navigateur
**When** le widget se recharge
**Then** les compteurs de refus et d'acceptation sont preserves (localStorage ou module-level state)

**Exigences techniques :**
- Module-level state dans useGuidedTour : guidanceRefusalCount, guidanceAcceptanceCount
- Persistance optionnelle dans localStorage (cle esg_mefali_guidance_stats)
- Transmission du compteur au LLM via le champ guidance_stats dans le FormData de sendMessage()
- Backend : ajout guidance_stats dans ConversationState, injection dans les prompts
- Logique de reduction du countdown dans useGuidedTour : countdown = max(3, defaultCountdown - acceptanceCount)
- Tests unitaires Vitest + pytest : compteurs, persistance, reduction countdown (couverture >= 80%)

---

## Epic 7 : Resilience et edge cases

L'experience reste fluide meme en conditions degradees — connexion lente, elements manquants, token expire, coupure reseau.

### Story 7.1 : Gestion des elements DOM absents et timeout de chargement

En tant qu'utilisateur avec une connexion lente,
je veux que le parcours guide gere gracieusement les situations ou un element n'est pas encore charge,
afin de ne pas rester bloque sur un ecran fige.

**Acceptance Criteria:**

**Given** un parcours guide pointe un element qui n'est pas dans le DOM (donnees async non chargees)
**When** waitForElement est appele
**Then** le systeme retente 3 fois avec 500ms d'intervalle (NFR18)
**And** si l'element apparait pendant les retries, l'etape s'execute normalement

**Given** l'element n'est pas trouve apres 3 retries
**When** le dernier retry echoue
**Then** l'etape est skippee
**And** un message empathique en francais est ajoute dans le chat : « Je n'ai pas pu pointer cet element. Passons a la suite. » (FR31)
**And** le parcours continue avec l'etape suivante

**Given** une navigation multi-pages est effectuee et la page cible met du temps a charger
**When** le temps de chargement depasse 5 secondes
**Then** un retry silencieux est tente

**Given** la page cible n'a toujours pas charge apres 10 secondes
**When** le timeout expire
**Then** le parcours s'interrompt
**And** le widget reapparait
**And** un message empathique est ajoute dans le chat : « La page met trop de temps a charger. Reessayez plus tard. » (NFR16)

**Given** Driver.js leve une exception inattendue pendant un parcours
**When** l'erreur est attrapee
**Then** driver.destroy() est appele, le widget reapparait, l'etat passe a 'interrupted'
**And** un message empathique est ajoute : « Le guidage a rencontre un probleme. Le chat est toujours disponible. »

**Exigences techniques :**
- Renforcement de useGuidedTour.ts : try/catch global autour de l'execution du parcours
- Messages d'erreur en francais avec accents, ton empathique (pas technique)
- Tous les messages via useChat().addSystemMessage() (message local, pas envoye au LLM)
- Tests unitaires Vitest : retry succes au 2eme essai, retry echec apres 3, timeout 5s, timeout 10s, crash Driver.js (couverture >= 80%)

---

### Story 7.2 : Renouvellement JWT transparent pendant le guidage

En tant qu'utilisateur qui suit un parcours guide sur plusieurs pages,
je veux que mon token d'authentification soit renouvele automatiquement,
afin de ne pas etre interrompu par une deconnexion.

**Acceptance Criteria:**

**Given** un parcours guide multi-pages est en cours
**When** le token JWT expire pendant la navigation entre deux pages
**Then** le mecanisme de refresh token dans apiFetch/useAuth intercepte le 401
**And** le refresh token est utilise pour obtenir un nouveau JWT
**And** la requete originale est rejouee automatiquement
**And** aucune interruption visible pour l'utilisateur (NFR9, FR32)

**Given** le refresh token lui-meme est expire
**When** le renouvellement echoue
**Then** l'utilisateur est redirige vers la page de login
**And** le parcours guide s'interrompt proprement (cleanup)

**Given** une page chargee pendant un guidage fait un appel API authentifie
**When** le JWT a ete renouvele en arriere-plan
**Then** l'appel API utilise le nouveau token sans intervention

**Given** le renouvellement JWT se produit
**When** un parcours Driver.js est en cours (etapes frontend-only)
**Then** le parcours n'est pas affecte (Driver.js ne fait pas d'appel API)

**Exigences techniques :**
- Verification du mecanisme existant dans useAuth/apiFetch : intercepteur 401 → refresh → retry
- Si le mecanisme n'existe pas completement, l'implementer dans le composable d'auth existant
- Le parcours Driver.js ne depend pas du JWT (frontend-only) — seules les pages chargees en ont besoin
- Tests unitaires Vitest : mock 401 → refresh → retry, refresh echoue → redirect login (couverture >= 80%)

---

### Story 7.3 : Resilience SSE et indicateur de reconnexion

En tant qu'utilisateur dont la connexion reseau est instable,
je veux que le parcours guide continue meme si la connexion au serveur est perdue,
afin de ne pas perdre ma progression de guidage.

**Acceptance Criteria:**

**Given** un parcours guide est en cours et la connexion SSE est perdue
**When** le reader SSE detecte une erreur ou une fermeture inattendue
**Then** le parcours Driver.js continue normalement (entierement frontend — FR33, NFR17)
**And** le widget affiche un indicateur visuel de reconnexion (icone ou badge « Reconnexion... »)

**Given** l'indicateur de reconnexion est affiche
**When** la connexion SSE est retablie (prochain sendMessage reussi)
**Then** l'indicateur disparait
**And** le chat reprend son fonctionnement normal

**Given** la connexion SSE est perdue et le parcours guide se termine
**When** le widget reapparait
**Then** l'indicateur de reconnexion est visible dans le widget
**And** l'utilisateur peut toujours consulter l'historique des messages charges

**Given** la connexion SSE est perdue et aucun parcours guide n'est en cours
**When** l'utilisateur ouvre le widget
**Then** l'indicateur de reconnexion est affiche
**And** l'envoi de messages est desactive avec un message explicatif

**Given** le dark mode est actif
**When** l'indicateur de reconnexion est affiche
**Then** il respecte le theme dark

**Exigences techniques :**
- Nouvelle ref module-level dans useChat.ts : isConnected (boolean) basee sur l'etat du dernier fetch
- Indicateur visuel dans FloatingChatWidget.vue : badge conditionnel sur !isConnected
- Desactivation de ChatInput quand !isConnected
- Dark mode complet sur l'indicateur
- Tests unitaires Vitest : perte connexion pendant guidage, reprise connexion, indicateur affiche/masque (couverture >= 80%)

---

## Epic 8 : Tests d'integration end-to-end

Confiance et qualite — les 5 parcours utilisateur du PRD (Fatou, Moussa, Aminata, Ibrahim, Aissatou) sont valides de bout en bout.

### Story 8.1 : Tests E2E — Parcours Fatou (guidage propose et accepte, multi-pages)

En tant que product owner,
je veux valider le parcours complet d'un utilisateur qui accepte un guidage propose apres completion d'un module,
afin de garantir que la chaine de bout en bout fonctionne sans regression.

**Acceptance Criteria:**

**Given** l'utilisateur Fatou est connectee sur /dashboard avec le widget flottant visible
**When** elle ouvre le widget et complete un module via le chat (ex: bilan carbone)
**Then** l'assistant propose un guidage via widget interactif (« Oui, montre-moi » / « Non merci »)

**Given** Fatou clique sur « Oui, montre-moi »
**When** le guidage demarre
**Then** le widget se retracte (animation ou instantane si reduced-motion)
**And** Driver.js highlight le lien sidebar correspondant avec un decompteur

**Given** Fatou clique sur le lien sidebar avant l'expiration du decompteur
**When** la page cible se charge (ex: /carbon/results)
**Then** le parcours Driver.js reprend automatiquement
**And** les popovers pointent successivement les elements marques (donut, benchmark, plan reduction)

**Given** le parcours se termine
**When** la derniere etape est affichee
**Then** driver.destroy() est appele, le widget reapparait
**And** un message de conclusion s'affiche dans le chat

**Exigences techniques :**
- Test Playwright dans tests/e2e/guided-tour-fatou.spec.ts
- Fixtures : utilisateur authentifie, profil entreprise existant, bilan carbone completable
- Assertions : widget visible, retraction, navigation, popovers Driver.js, reapparition widget
- Timeout genereux pour les connexions SSE et le chargement des pages

---

### Story 8.2 : Tests E2E — Parcours Moussa (guidage refuse, chat contextuel)

En tant que product owner,
je veux valider que le refus du guidage fonctionne sans friction et que le chat reste utilisable en superposition,
afin de garantir que les utilisateurs experimentes ne sont pas genes.

**Acceptance Criteria:**

**Given** l'utilisateur Moussa est connecte sur /financing avec le widget flottant ouvert
**When** il pose une question dans le chat (« Quels fonds sont compatibles avec mon profil ? »)
**Then** l'assistant repond avec un resume contextuel (adapte a la page /financing)

**Given** l'assistant propose un guidage
**When** Moussa clique sur « Non merci »
**Then** aucun parcours Driver.js ne demarre
**And** le chat continue normalement
**And** le widget reste ouvert et fonctionnel

**Given** le widget est ouvert en superposition sur /financing
**When** Moussa consulte la page derriere le widget
**Then** le contenu est visible a travers le glassmorphism (ou le fallback opaque)
**And** les donnees financieres ne sont pas lisibles a travers le blur

**Exigences techniques :**
- Test Playwright dans tests/e2e/guided-tour-moussa.spec.ts
- Assertions : reponse contextuelle, pas de Driver.js apres refus, glassmorphism/fallback visible
- Verification que le chat fonctionne apres refus (envoi de messages supplementaires)

---

### Story 8.3 : Tests E2E — Parcours Aminata (guidage demande explicitement)

En tant que product owner,
je veux valider qu'un utilisateur peut demander un guidage en langage naturel sans passer par le consentement,
afin de garantir que la detection d'intent fonctionne de bout en bout.

**Acceptance Criteria:**

**Given** l'utilisateur Aminata est connectee sur /dashboard avec le widget ouvert
**When** elle tape « montre-moi mes resultats ESG »
**Then** l'assistant detecte l'intent de guidage explicite
**And** trigger_guided_tour('show_esg_results') est appele SANS widget de consentement (FR16)

**Given** le guidage demarre
**When** le parcours s'execute
**Then** le widget se retracte, Driver.js guide vers /esg/results
**And** les popovers pointent les elements ESG (score, forces/faiblesses, recommandations)

**Given** le parcours est termine
**When** le widget reapparait
**Then** le chat est fonctionnel et Aminata peut continuer la conversation

**Exigences techniques :**
- Test Playwright dans tests/e2e/guided-tour-aminata.spec.ts
- Fixtures : utilisateur authentifie avec evaluation ESG completee (donnees en base)
- Assertions : pas de widget consentement, declenchement direct, parcours complet

---

### Story 8.4 : Tests E2E — Parcours Ibrahim (decompteur expire, navigation automatique)

En tant que product owner,
je veux valider que la navigation automatique fonctionne quand l'utilisateur ne clique pas avant l'expiration du decompteur,
afin de garantir l'accompagnement des utilisateurs peu technophiles.

**Acceptance Criteria:**

**Given** un guidage est accepte et l'entryStep affiche un decompteur sur le lien sidebar
**When** Ibrahim ne clique pas et le decompteur arrive a 0
**Then** la navigation vers la page cible se fait automatiquement via router.push (FR22)

**Given** la navigation automatique est effectuee
**When** la page cible se charge
**Then** Driver.js attend la stabilite DOM puis reprend le parcours (FR23)
**And** les popovers s'affichent correctement sur les elements cibles

**Given** le parcours se deroule entierement sans clic utilisateur sur les liens
**When** toutes les etapes sont terminees
**Then** le widget reapparait et le parcours est marque comme complete

**Exigences techniques :**
- Test Playwright dans tests/e2e/guided-tour-ibrahim.spec.ts
- Strategie : ne pas cliquer sur le lien sidebar, attendre l'expiration du decompteur
- Assertions : navigation automatique, reprise parcours post-navigation, parcours complete
- Timeout du test suffisant pour couvrir le decompteur (8s par defaut)

---

### Story 8.5 : Tests E2E — Parcours Aissatou (detection mobile, degradation gracieuse)

En tant que product owner,
je veux valider que sur mobile aucun element du copilot n'est rendu et que l'interface existante est intacte,
afin de garantir zero regression pour les utilisateurs mobiles.

**Acceptance Criteria:**

**Given** le viewport est configure a < 1024px (ex: 375x812, iPhone)
**When** n'importe quelle page se charge
**Then** aucun bouton FAB n'est visible dans le DOM
**And** aucun FloatingChatWidget n'est rendu
**And** aucun overlay Driver.js n'est present

**Given** le viewport mobile est actif
**When** l'utilisateur navigue entre les pages
**Then** la navigation classique fonctionne normalement (sidebar mobile, menu hamburger)
**And** les pages de contenu s'affichent correctement

**Given** le viewport est redimensionne de desktop (>= 1024px) a mobile (< 1024px)
**When** le changement est detecte
**Then** le widget flottant disparait s'il etait visible
**And** aucun parcours guide en cours n'est casse (interruption propre)

**Exigences techniques :**
- Test Playwright dans tests/e2e/guided-tour-aissatou.spec.ts
- Configuration viewport mobile : page.setViewportSize({ width: 375, height: 812 })
- Assertions : absence totale de composants copilot dans le DOM
- Test de resize dynamique desktop → mobile

---

### Story 8.6 : Tests de non-regression globaux

En tant que product owner,
je veux la certitude que la feature 019 n'a casse aucune fonctionnalite existante,
afin de deployer en confiance.

**Acceptance Criteria:**

**Given** la feature 019 est completement implementee
**When** on execute la suite complete de tests backend (pytest)
**Then** les 935+ tests existants passent sans modification (NFR19)
**And** aucun test n'a ete supprime ou marque skip sans justification

**Given** la feature 019 est completement implementee
**When** on execute la suite de tests frontend (Vitest)
**Then** tous les tests existants passent sans modification

**Given** la feature 018 (widgets interactifs) est utilisee dans le widget flottant
**When** on teste les widgets QCU/QCM dans le FloatingChatWidget
**Then** le comportement est identique a l'ancien ChatPanel (NFR20)

**Given** la feature 012 (tool calling) est active
**When** un tool call est execute pendant une conversation dans le widget
**Then** les events SSE tool_call_start/end sont recus et affiches normalement

**Given** la feature 013 (active_module) est active
**When** un module est en cours (ex: esg_scoring) et current_page est transmis
**Then** les deux mecanismes coexistent sans conflit (NFR22)

**Given** la couverture de tests est mesuree
**When** on calcule le ratio pour les nouveaux fichiers de la feature 019
**Then** la couverture est >= 80% sur chaque nouveau fichier (frontend et backend)

**Exigences techniques :**
- Execution : pytest (backend complet), vitest run (frontend complet)
- Verification couverture : vitest --coverage, pytest --cov
- Pas de nouveau test dans cette story — verification que l'existant passe
- Documentation des resultats : nombre de tests, couverture par fichier
