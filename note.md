test cette feature avec `agent-browser --headed`

`claude --dangerously-skip-permissions`

Email: `amadou@ecosolaire.sn`
Mot de passe: `TestPass123!`



Champ	Valeur
URL	http://localhost:3000
Email	mamadou.kone@ecoplast-ci.com
Mot de passe	EcoPlast2025!

merge la branche actuelle dans main, j'ai déjà commité

Après cette correction, relancer les 45 tests avec la cible : 42/45 minimum (93%).
Les 3 seuls échecs tolérés : 2.1 (upload OCR), 3.4 (interruption/reprise si non implémenté), un edge case.




Très bien ! Voici les alternatives à Entrée express que je vous recommande, classées de la plus adaptée à votre profil à la moins adaptée :

---

**1. Programme Mobilité francophone (ma recommandation n°1)**

C'est la voie la plus simple et la plus adaptée à votre situation. Ce programme permet aux employeurs canadiens (hors Québec) de vous embaucher **sans avoir besoin d'une Évaluation de l'impact sur le marché du travail (EIMT)**, ce qui simplifie énormément le processus. Le statut est actuellement **Ouvert**, les frais sont de seulement **155 $**, et c'est un permis de travail temporaire qui peut ensuite mener à la résidence permanente.

Pourquoi c'est idéal pour vous : vous êtes francophone natif, ingénieur logiciel (secteur STIM très demandé), et vous travaillez déjà pour une organisation canadienne (l'OIF basée au Québec). Il vous suffit de trouver un employeur canadien **hors Québec** prêt à vous embaucher. Votre expérience avec l'OIF et vos missions internationales (COP) sont un excellent atout.

**2. Programme pilote d'immigration dans les communautés francophones**

Ce programme offre directement la **résidence permanente** à des travailleurs francophones qualifiés dans des communautés rurales francophones hors Québec. Il vous faut une offre d'emploi d'un employeur désigné dans une communauté participante. C'est une voie vers la résidence permanente plus directe qu'Entrée express.

**3. Questionnaire d'orientation du gouvernement**

Il y a aussi sur la page un lien très utile : « Répondez à quelques questions et découvrez les autres programmes d'immigration du Canada ». Ce questionnaire officiel analyse votre situation et vous propose les programmes les plus adaptés parmi tous ceux disponibles (pas seulement ceux pour francophones).

---

**Mon conseil concret :** Commencez par le **Programme Mobilité francophone**. Avec votre profil d'ingénieur logiciel francophone, concentrez-vous sur la recherche d'un employeur au Canada (hors Québec) — en Ontario, au Nouveau-Brunswick, au Manitoba, ou en Alberta par exemple. Les entreprises tech canadiennes recrutent activement et l'avantage de ce programme est que l'employeur n'a pas besoin de passer par l'EIMT, ce qui le rend plus attractif pour eux aussi.

Souhaitez-vous que j'ouvre la page d'admissibilité du Programme Mobilité francophone ou le questionnaire d'orientation ?





  Cause racine

  Le hook est défini quelque part sous ~/.claude/plugins/.../gateguard-fact-force.js avec les flags      
  standard,strict. Le mode strict force l'énoncé des 4 faits systématiquement, y compris sur des fichiers
   markdown inertes où les questions « fichiers importeurs » ou « fonctions affectées » ne s'appliquent  
  pas (réponses N/A), ce qui amplifie le bruit.                                                        

  Options pour la suite

  - Option A — Garder tel quel : utile pour des projets critiques (PII, prod), le prix à payer est la
  verbosité.
  - Option B — Abaisser à standard seul : supprime le mode strict, le hook ne s'active que sur des cibles
   à risque (fichiers avec secrets, données prod, etc.).                                                 
  - Option C — Désactiver sur les markdowns de _bmad-output/ : ajouter un filtre d'exclusion pour les
  fichiers de tracking BMAD qui sont purement documentaires.                                             
  - Option D — Désactiver complètement : retirer le hook si tu ne travailles pas sur du sensible. 

________________________________________________________________________
/bmad-brainstorming TITRE : Exploration des 6 évolutions ESG Mefali avant PRD d'extension

CONTEXTE PROJET :
ESG Mefali — conseiller et agent ESG IA pour PME africaines francophones UEMOA/CEDEAO.
Plateforme existante : 8 modules métier (ESG, carbone, crédit vert, 
financement, dossiers, plan d'action, dashboard, rapports), ~935 tests, 
LangGraph + tool calling, RAG pgvector, widgets interactifs, guided tours.

AUDIT 18-SPECS TERMINÉ (voir _bmad-output/implementation-artifacts/spec-audits/index.md) :
- 14 P1 identifiés (1 résolu — rate limiting) + 28 P2 + 56 P3
- 5 références architecturales reconnues (specs 010, 011, 013, 014, 017)
- Signaux PRD consolidés dans la section « Signaux pour le prochain PRD »

ÉVOLUTIONS À EXPLORER :
1. FINANCEMENT DE PROJET (vs entreprise) — un entrepreneur peut demander un 
   financement pour UN projet spécifique, pas juste l'entreprise.
2. PROFIL DYNAMIQUE (entreprise + projets) — un même projet peut avoir N 
   dossiers différents selon le fonds ciblé et le profils peut etre ajusté selon le font.
3. DOSSIER PROJET OU ENTREPRISE — ESG Mefali doit pouvoir monter un dossier 
   pour financer un projet particulier sans exclure la possibilité de monter les dossiers de financement d'entreprise.
4. CRITÈRES ESG RELATIFS — les critères ESG seraient relatifs (au secteur ? 
   à la taille ? au projet ? le fond ciblé ? à creuser).
5. ÉTUDE D'IMPACT — Mefali doit pouvoir faire une étude d'impact du projet 
   d'une entreprise OU de l'entreprise.
6. DASHBOARD PLUS EXPRESSIF ET GRAPHIQUE — enrichissement visuel.

OBJECTIFS DU BRAINSTORMING (par ordre) :
a) Révéler les implications cachées de chaque évolution (ex : passer d'un 
   profil entreprise unique à N projets change le modèle data + routing 
   LangGraph + scoring ESG).
b) Identifier les DÉPENDANCES entre évolutions (ex : "critères ESG relatifs" 
   est sans doute prérequis à "étude d'impact").
c) Prioriser : lesquelles sont "phase 1" et lesquelles peuvent attendre.
d) Révéler les personas impactés (entrepreneur solo vs multi-projets ? 
   consultant qui suit plusieurs PME ?).

CONTRAINTES ET SIGNAUX PRD À INTÉGRER (cf. spec-audits/index.md) :

1. DÉCISION DATA-DRIVEN vs HARD-CODED (priorité absolue) :
   - 4 specs ont révélé un hard-coding massif (SECTOR_WEIGHTS, 
     SECTOR_BENCHMARKS, 12 fonds + 14 intermédiaires dans seed.py 889 lignes, 
     facteurs d'émission, UEMOA/BCEAO)
   - Les 6 évolutions nécessitent toutes une migration vers BDD avec 
     interface admin — sinon refactor impossible
   - Table `fund` + `intermediary` + `esg_sector_config` + 
     `carbon_emission_factor` + `regulation_reference` à prévoir

2. SATURATION DU PATTERN « PROMPTS DIRECTIFS » :
   - 4 spec-correctifs consécutives (013, 015, 016, 017) ont juste ajouté 
     plus de REGLE ABSOLUE dans les prompts
   - Le pattern ne scale plus → réfléchir à un enforcement applicatif 
     (state machines, guards pré-tool, agents dédiés)
   - Nouvelles évolutions = nouvelles instructions transverses = saturation 
     accélérée si pas de refactor

3. FRAMEWORK D'INJECTION D'INSTRUCTIONS :
   - 3 instructions transverses déjà dupliquées 
     (STYLE + WIDGET + GUIDED_TOUR)
   - Projet dynamique + étude d'impact généreront vraisemblablement 
     2-3 nouvelles instructions → refactor préventif recommandé

4. RICH BLOCKS EXTENSIBLES :
   - Dashboard graphique nécessitera probablement des nouveaux types de 
     blocs visuels — registre extensible attendu
   - Spec 018 a contourné en créant un système parallèle 
     (interactive_questions) plutôt qu'étendre

5. SNAPSHOT DES DONNÉES SOURCE :
   - Specs 008 + 010 n'ont pas de snapshot → historiques trompeurs
   - Profil dynamique et étude d'impact : obligation de snapshot propre

6. RAG TRANSVERSAL :
   - Promesse FR-005 spec 009 non tenue, 1/8 modules consomme le RAG
   - Étude d'impact et dossier projet bénéficieraient directement du RAG

RÉFÉRENCES ARCHITECTURALES À S'INSPIRER :
- Spec 010 (Green Credit Scoring) — pattern scoring/évaluation
- Spec 011 (Dashboard Action Plan) — pattern intégration multi-modules + 
  snapshot
- Spec 013 (Fix routing) — pattern spec-correctif
- Spec 014 (Concise Chat Style) — pattern micro-spec transverse
- Spec 017 (Fix failing tests) — pattern spec-nettoyage

PUBLIC CIBLE RAPPEL :
- PME africaines francophones UEMOA/CEDEAO
- Secteurs dominants : agroalimentaire (60-70%), commerce, artisanat, 
  construction (source BCEAO) — actuellement SOUS-PONDÉRÉS dans le scoring ESG
- Accès internet variable, data cost-sensitive, mobile-first
- Bailleurs cibles : GCF, FEM, BOAD, BAD, SUNREF, FNDE

LIVRABLE ATTENDU :
Un document de brainstorming qui, pour chaque évolution :
- Implications architecturales identifiées
- Dépendances avec les autres évolutions
- Personas impactés
- Prérequis (dettes P1 à fixer avant)
- Priorité suggérée (P0/P1/P2)
- Questions ouvertes à clarifier
