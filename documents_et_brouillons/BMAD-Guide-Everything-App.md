# Guide BMAD — Everything App (Super App Africaine)


## 0. Installation

```bash
mkdir everything-app && cd everything-app
git init
npx bmad-method install
```

Choix durant l'installation :
- Modules → **BMad Method** + **Test Architect**
- Outil IA → **Claude Code**
- Setup → **Express Setup**

### Vérification

```
bmad-help
```

Confirme que tout est bien installé et montre les prochaines étapes.

---

## Phase 1 — Analyse (Optionnelle mais recommandée pour ce projet)

Ces étapes explorent le problème et valident les idées avant de planifier.

| # | Commande | Agent | Description |
|---|----------|-------|-------------|
| 1 | `bmad-brainstorming` | Analyst | Brainstorming guidé. Tu as déjà un document, tu peux le fournir à l'agent pour qu'il l'enrichisse et le structure. |
| 2 | `bmad-market-research` | Analyst | Recherche de marché. Valider les hypothèses sur Glovo, Yango, Jumia Food en CI. |
| 3 | `bmad-technical-research` | Analyst | Recherche technique. Valider les choix Flutter + Actix/Rust + FastAPI, CinetPay, etc. |
| 4 | `bmad-domain-research` | Analyst | Recherche domaine. Explorer la logistique inter-villes, réglementations wallet/paiement en CI. |
| 5 | `bmad-create-product-brief` | Analyst | Créer le Product Brief — document de vision stratégique. Résume la vision, les utilisateurs cibles, le MVP. Produit → `product-brief.md` |

---

## Phase 2 — Planification (Obligatoire)

Définir ce qu'on construit et pour qui.

| # | Commande | Agent | Description |
|---|----------|-------|-------------|
| 6 | `bmad-create-prd` | PM | Créer le PRD (Product Requirements Document). Exigences fonctionnelles et non-fonctionnelles, personas, métriques, risques. Produit → `PRD.md` |
| 7 | `bmad-create-ux-design` | UX Designer | Concevoir l'expérience utilisateur. Wireframes, flows, composants UI pour les 4 apps. Produit → `ux-spec.md` |

---

## Phase 3 — Solutioning (Obligatoire pour BMad Method)

Décider comment construire et découper le travail.

| # | Commande | Agent | Description |
|---|----------|-------|-------------|
| 8 | `bmad-create-architecture` | Architect | Créer le document d'architecture. Décisions techniques (microservices Rust/Python, DB, API, infra), ADRs. Produit → `architecture.md` |
| 9 | `bmad-generate-project-context` | Analyst | Générer le fichier de contexte projet. Règles et conventions que tous les agents suivront. Produit → `project-context.md` |
| 10 | `bmad-create-epics-and-stories` | PM | Découper le PRD + Architecture en epics et stories. Crée des fichiers par epic avec les stories priorisées. Produit → dossier `epics/` |
| 11 | `bmad-check-implementation-readiness` | Architect | Vérification de cohérence avant de coder. Valide que PRD, Architecture et Stories sont alignés. Résultat → PASS / CONCERNS / FAIL |

---

## Phase 4 — Implémentation

Construire story par story.

### Initialisation (une seule fois)

| # | Commande | Agent | Description |
|---|----------|-------|-------------|
| 12 | `bmad-sprint-planning` | SM (Scrum Master) | Initialiser le suivi de sprint. Séquence les stories à implémenter. Produit → `sprint-status.yaml` |

### Cycle de développement (répéter pour chaque story)

| # | Commande | Agent | Description |
|---|----------|-------|-------------|
| 13 | `bmad-create-story` | SM | Préparer la prochaine story. Crée un fichier story détaillé avec tout le contexte nécessaire au Dev. Produit → `story-[slug].md` |
| 14 | `bmad-dev-story` | DEV | Implémenter la story. L'agent code en suivant l'architecture et le contexte projet. Produit → code + tests |
| 15 | `bmad-code-review` | DEV | Revue de code. Valide la qualité, les bonnes pratiques, la conformité à l'architecture. Résultat → Approved / Changes requested |

### Suivi & ajustements

| # | Commande | Agent | Description |
|---|----------|-------|-------------|
| 16 | `bmad-sprint-status` | SM | Voir l'état du sprint en cours. Quelles stories sont faites, en cours, à faire. |
| 17 | `bmad-correct-course` | SM | Gérer un changement de scope important en plein sprint. Met à jour le plan. |
| 18 | `bmad-retrospective` | SM | Rétrospective après la fin d'un epic. Leçons apprises, améliorations. |

---

## Commandes utiles à tout moment

| Commande | Description |
|----------|-------------|
| `bmad-help` | Guide intelligent. Demande-lui n'importe quoi : où tu en es, quoi faire ensuite, comment résoudre un problème. |
| `bmad-help <question>` | Pose une question contextuelle. Ex : `bmad-help I just finished the architecture, what's next?` |
| `bmad-pm` | Charger l'agent PM pour une conversation libre (hors workflow). |
| `bmad-architect` | Charger l'agent Architecte pour discuter de choix techniques. |
| `bmad-sm` | Charger le Scrum Master pour discuter du sprint. |
| `bmad-analyst` | Charger l'Analyste pour du brainstorming ou de la recherche. |
| `bmad-ux-designer` | Charger l'UX Designer pour discuter interfaces. |

---

## Résumé visuel du parcours

```
INSTALLATION
  npx bmad-method install → bmad-help

PHASE 1 — ANALYSE (optionnelle)
  bmad-brainstorming
  bmad-market-research / bmad-technical-research / bmad-domain-research
  bmad-create-product-brief → product-brief.md

PHASE 2 — PLANIFICATION
  bmad-create-prd → PRD.md
  bmad-create-ux-design → ux-spec.md

PHASE 3 — SOLUTIONING
  bmad-create-architecture → architecture.md
  bmad-generate-project-context → project-context.md
  bmad-create-epics-and-stories → epics/
  bmad-check-implementation-readiness → PASS/FAIL

PHASE 4 — IMPLÉMENTATION
  bmad-sprint-planning → sprint-status.yaml
  ┌─────────────────────────────────────┐
  │  BOUCLE (pour chaque story) :       │
  │  bmad-create-story → story file     │
  │  bmad-dev-story → code + tests      │
  │  bmad-code-review → validation      │
  └─────────────────────────────────────┘
  bmad-sprint-status (suivi)
  bmad-retrospective (fin d'epic)
```

---

## Rappels importants

1. **Nouveau chat à chaque workflow** — Ne pas enchaîner plusieurs workflows dans le même chat, ça évite les problèmes de contexte.
2. **bmad-help est ton meilleur ami** — En cas de doute, lance-le. Il inspecte ton projet et te dit exactement quoi faire.
3. **Les fichiers générés s'accumulent** — Chaque phase produit des documents qui servent de contexte à la phase suivante. Ne les supprime pas.
4. **Mise à jour BMAD** — Pour mettre à jour : `npx bmad-method install` (sans perdre tes customisations).

---

*Source : [docs.bmad-method.org](https://docs.bmad-method.org) — BMAD-METHOD v6*



Prochaines etapes :                                                                                     
  1. Relire la story dans 1-1-initialize-flutter-monorepo.md                                              
  2. Lancer /bmad-dev-story pour l'implementation                                                         
  3. Lancer /bmad-code-review quand termine                                                               
  4. Optionnel : /bmad-testarch-automate pour les tests guardrail                                         

