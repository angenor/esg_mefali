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
/bmad-brainstorming TITRE : Exploration de plusieurs évolutions ESG Mefali avant PRD d'extension

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

Dans mes recherche, par curiosité, j'ai demandé ceci à claude(peut-etre interressant à inclure):
````
c'est quoi le role d'un consultant ESG. Lorsqu'une entreprise a recour à un consultant ESG c'est pour que ce consultant l'aide à faire quoi, de facons exostif mais pour l'afrique de l'ouest, J'imagine que ce n'est pas forcement la meme chose qu'en europe
````
Voici sa reponse, tu pourra faire toi meme des recherche pour confirmer, rejerter ou en richir :
```
# Le rôle d'un consultant ESG en Afrique de l'Ouest

Tu as raison : **le métier existe, mais il ne ressemble pas du tout à son équivalent européen**. En Europe, le consultant ESG est avant tout tiré par la réglementation (CSRD, Taxonomie, CS3D). En Afrique de l'Ouest, il est surtout tiré par **les bailleurs de fonds, les investisseurs internationaux, les clients multinationaux et les grands donneurs d'ordre**. La pression réglementaire locale existe mais reste embryonnaire. Voici, de façon exhaustive, ce que fait réellement un consultant ESG dans la région (UEMOA/CEDEAO).

## 1. Le contexte qui change tout

Avant de parler missions, il faut comprendre l'écosystème, parce qu'il conditionne tout le métier :

- **Pas de CSRD, pas d'ESRS, pas de Taxonomie européenne contraignante.** La BCEAO n'a pas encore publié de directives complètes sur l'intégration des risques environnementaux et sociaux dans la gestion du portefeuille et la supervision bancaire, bien que des travaux soient en cours.
- **Les référentiels viennent d'ailleurs.** Les banques africaines qui gèrent les risques E&S le font principalement dans le cadre de leurs relations avec des partenaires financiers comme FMO, la Société Financière Internationale (IFC/SFI), Proparco, la Banque Africaine de Développement, etc.
- **Le tissu économique est spécifique.** Les PME représentent plus de 90 % des entreprises d'Afrique de l'Ouest et contribuent à 60–70 % de l'emploi, mais moins de 20 % ont accès à un crédit formel. Une grande partie de l'économie est informelle.
- **La finance durable est en structuration.** Les échanges lors des BRVM Awards 2026 à Dakar ont mis en évidence l'écart entre les référentiels ESG internationaux et les capacités opérationnelles des entreprises de l'UEMOA, notamment en matière de reporting, de gouvernance et de structuration de projets. Le financement durable suppose des outils techniques, des données fiables et des cadres réglementaires adaptés, qui restent inégalement disponibles dans la région.
- **Les standards ne sont pas calibrés pour l'Afrique.** La configuration actuelle des standards et normes de la finance durable est conçue par et pour les pays développés, et il n'est pas toujours aisé de les appliquer au contexte des marchés émergents comme l'Afrique. Une partie du travail du consultant consiste donc à "traduire" et adapter.

Conséquence : le consultant ESG ouest-africain est **beaucoup plus opérationnel et terrain** que son homologue parisien, et beaucoup moins "normatif/reporting pur".

## 2. Accompagnement à l'accès aux financements internationaux (LE cœur du métier)

C'est souvent la porte d'entrée. Une entreprise ivoirienne, sénégalaise ou béninoise qui cherche un prêt ou une prise de participation auprès de :

- **IFC (Société Financière Internationale)** → doit se conformer aux **IFC Performance Standards (PS1 à PS8)**
- **Proparco, FMO, BIO, DEG, CDC, BEI**
- **BAD (Banque Africaine de Développement), BOAD (Banque Ouest Africaine de Développement)** → Système de Sauvegardes Intégré
- **Fonds d'impact** (AfricInvest, Mediterrania Capital, Adenia, Partech Africa, Janngo Capital, etc.)

… doit impérativement présenter un **système de gestion environnementale et sociale (SGES / ESMS)** conforme. Le consultant :
- réalise le **diagnostic E&S** (due diligence)
- construit le SGES (politiques, procédures, manuel, registre des risques)
- fait l'**analyse d'impact environnemental et social (EIES)** des projets
- rédige les **plans d'action correctifs (ESAP – Environmental and Social Action Plan)**
- accompagne les missions de suivi des bailleurs

## 3. Conformité aux Principes de l'Équateur (pour les banques)

Les grandes banques régionales — Ecobank, NSIA, Coris Bank, BOA, Société Générale, Orabank, UBA… — se sont souvent alignées sur les **Principes de l'Équateur** et sur les standards IFC pour pouvoir syndiquer avec des banques internationales. Le consultant aide à :
- catégoriser les projets (A, B, C selon le risque E&S)
- intégrer l'analyse E&S dans le processus de crédit
- former les chargés de crédit et les analystes de risque
- produire les rapports E&S vers les partenaires internationaux

## 4. Secteurs extractifs et agro-industriels (mines, pétrole & gaz, cacao, hévéa, anacarde, coton)

C'est un axe énorme en Afrique de l'Ouest, beaucoup plus qu'en Europe. Missions typiques :

- **Études d'Impact Environnemental et Social (EIES)** requises par les codes miniers/environnementaux nationaux (Code minier ivoirien, Code de l'environnement, ANDE en Côte d'Ivoire, DEEC au Sénégal, etc.)
- **Plans de Gestion Environnementale et Sociale (PGES)**
- **Plans de Réinstallation (PAR/RAP)** quand il y a déplacement de populations
- **Relations avec les communautés locales** (consultations, CLIP – consentement libre, informé et préalable)
- **Développement local** (contenu local, emploi local, formation)
- **Certifications sectorielles** : RSPO (huile de palme), Rainforest Alliance / UTZ (cacao, café), Fairtrade, Bonsucro (sucre), FSC (bois), ResponsibleSteel, IRMA (mines)
- **Lutte contre le travail des enfants** — enjeu majeur dans la filière cacao ivoirienne et ghanéenne, avec des obligations renforcées par le **règlement européen sur la déforestation importée (RDUE/EUDR)** et le **devoir de vigilance** des acheteurs européens
- **Traçabilité des chaînes d'approvisionnement** (géolocalisation des plantations pour l'EUDR)

## 5. Adaptation au devoir de vigilance et aux réglementations européennes… vues d'Afrique

Même sans CSRD locale, les entreprises ouest-africaines **subissent indirectement** la réglementation européenne parce qu'elles fournissent des clients européens. Le consultant aide à :
- répondre aux **questionnaires ESG des clients** (Nestlé, Mars, Mondelez, Barry Callebaut, Cargill, Olam, Michelin, Total, etc.)
- se préparer aux audits **Sedex/SMETA, EcoVadis, SA8000**
- répondre aux exigences de la **CS3D européenne** et du **règlement EUDR** répercutées sur les fournisseurs
- préparer les **déclarations de conformité** (absence de travail forcé, d'enfants, de déforestation)

C'est souvent un enjeu de **survie commerciale** : sans conformité, plus de contrat d'export.

## 6. RSE "locale" et labels régionaux

La RSE s'est structurée au niveau national avant l'ESG "financier". Au Sénégal, la Charte RSE et développement durable, initiée en 2012 par l'Initiative RSE Sénégal et le Conseil national du patronat, a été élaborée par 11 entreprises de différents secteurs (mines, industrie, BTP, banque, hôtellerie) et définit des engagements minimaux pour toute entreprise sénégalaise qui veut s'inscrire dans une politique de RSE, quelle que soit sa taille. Le consultant accompagne :
- les signataires de la **Charte RSE du Sénégal**, de la **Plateforme RSE Côte d'Ivoire**, du **RSE & Développement Durable Bénin**
- les certifications **ISO 26000** (lignes directrices RSE), **ISO 14001** (environnement), **ISO 45001** (santé-sécurité au travail), **ISO 37001** (anti-corruption)
- les labels **B Corp**, **Label RSE CGECI** (Confédération Générale des Entreprises de Côte d'Ivoire)
- l'alignement avec les **Objectifs de Développement Durable (ODD)** des Nations Unies
- l'adhésion au **Pacte Mondial des Nations Unies (UN Global Compact)**

## 7. Le volet environnemental (le "E") — spécificités ouest-africaines

- **Bilan carbone / GES** (scopes 1, 2, 3), souvent avec le protocole GHG Protocol, parfois avec des facteurs d'émission adaptés (réseau électrique ivoirien, sénégalais, mix énergétique…)
- **Efficacité énergétique** et **autoconsommation solaire** (un énorme sujet vu le coût de l'électricité et la fragilité du réseau)
- **Gestion de l'eau** (stress hydrique, prélèvements, rejets)
- **Gestion des déchets** dans des contextes où les filières de recyclage sont limitées
- **Déforestation et biodiversité** (boucliers forestiers ivoiriens, mangroves, zones classées)
- **Adaptation au changement climatique** : ici ce n'est pas théorique — sécheresses, inondations, érosion côtière à Abidjan, Cotonou, Lomé ; les entreprises doivent **évaluer leur vulnérabilité physique**
- **Pollution plastique, qualité de l'air urbain**

## 8. Le volet social (le "S") — spécificités ouest-africaines

C'est souvent là que le métier diffère le plus de l'Europe :

- **Santé & sécurité au travail (HSE/EHS)** : souvent le point de départ concret, surtout en industrie, BTP, mines
- **Conditions de travail** : formalisation des contrats, respect du Code du Travail, cotisations CNPS/IPRES, salaire minimum (SMIG)
- **Travail des enfants et travail forcé** dans les chaînes d'approvisionnement agricoles
- **Relations communautaires** : gestion des doléances, investissements communautaires, mécanismes de plainte
- **Contenu local** : embauche locale, sous-traitance locale, formation
- **Genre et autonomisation des femmes** : programmes d'inclusion économique des femmes (très demandés par les bailleurs)
- **Accès aux services de base** (eau, santé, éducation) quand l'entreprise est implantée dans une zone sous-équipée
- **Santé publique** (VIH/SIDA, paludisme, Ebola historiquement, et désormais préparation pandémique)
- **Sécurité** : gestion des forces de sécurité privées selon les **Principes Volontaires sur la Sécurité et les Droits de l'Homme** (crucial dans les zones minières et au Sahel)

## 9. Le volet gouvernance (le "G") — spécificités ouest-africaines

- **Anti-corruption** : un enjeu central, avec la loi ivoirienne anti-corruption, la HABG, l'OFNAC au Sénégal, les lois FCPA et UK Bribery Act qui s'appliquent extra-territorialement
- **Gouvernance d'entreprise OHADA** (Acte uniforme sur les sociétés commerciales)
- **Transparence fiscale** (ITIE – Initiative pour la Transparence des Industries Extractives, à laquelle la Côte d'Ivoire, le Sénégal, le Mali, le Burkina, le Niger adhèrent)
- **Conformité BCEAO** pour les banques et institutions financières (LBC/FT, KYC)
- **Protection des données** : lois ivoirienne 2013, sénégalaise 2008, règlement CEDEAO — équivalent local du RGPD
- **Structuration du conseil d'administration**, comité d'audit, code d'éthique
- **Gestion des conflits d'intérêts** dans des contextes où les liens familiaux/politiques sont denses

## 10. Finance durable et marchés de capitaux régionaux

Un axe qui monte rapidement. La Banque africaine de développement a initié en 2025 la mise en place d'une taxonomie de finance durable à l'échelle du continent, qui vise à orienter les capitaux vers des investissements à impact environnemental et social. Le consultant accompagne :
- les émissions d'**obligations vertes, sociales ou durables** sur la **BRVM**
- les **sustainability-linked loans** avec des banques régionales
- l'alignement avec la **taxonomie UE** (pour les émetteurs qui ciblent des investisseurs européens) et la future **taxonomie africaine**
- les financements mixtes (blended finance) avec les bailleurs
- la préparation des entreprises cotées BRVM à des exigences de disclosure ESG qui se profilent

## 11. Reporting extra-financier — version Afrique

Plutôt que la CSRD, ce qui est demandé ici :
- **Rapport annuel de développement durable** aligné **GRI Standards** (référentiel le plus utilisé en Afrique)
- Déclarations **TCFD** (risques climatiques) pour les grandes entreprises et institutions financières
- **CDP** (climat, eau, forêts) — demandé par les clients internationaux
- **Rapports aux bailleurs** (IFC AIMM, Proparco, BAD) avec indicateurs d'impact
- **Rapports ITIE** pour les extractives
- **Questionnaires EcoVadis, Sedex** pour les chaînes d'approvisionnement

## 12. Renforcement de capacités et formation

Parce que l'ESG est une discipline récente dans la région, une part non négligeable du métier consiste à **former**, beaucoup plus qu'en Europe : sensibiliser les dirigeants, former les équipes RH, HSE, achats, crédit, risque, communication. C'est quasiment toujours une composante des missions.

## 13. Structuration de la fonction ESG en interne

Le consultant aide souvent à **créer** ou **structurer** la direction RSE/ESG (qui n'existe pas encore dans beaucoup d'entreprises) : fiche de poste, rattachement hiérarchique, gouvernance interne, KPIs, budget.

---

## En résumé : différences clés Europe vs Afrique de l'Ouest

| Dimension | Europe | Afrique de l'Ouest |
|---|---|---|
| **Moteur principal** | Réglementation (CSRD, CS3D, Taxonomie) | Bailleurs internationaux, clients export, investisseurs d'impact |
| **Référentiels dominants** | ESRS, Taxonomie UE | IFC PS, Équateur, GRI, ISO 26000, certifications sectorielles |
| **Clients types** | Grandes entreprises cotées, ETI | Filiales de multinationales, banques, mines/pétrole, agro-industrie, PME exportatrices |
| **Enjeux dominants** | Décarbonation, double matérialité, reporting | HSE, communautés, contenu local, travail des enfants, déforestation, anti-corruption |
| **Contrainte** | Coût de conformité élevé mais obligatoire | Arbitrage entre ESG et survie économique, manque de données |
| **Finalité** | Éviter sanctions + attirer capitaux | Accéder aux financements + conserver les clients internationaux |

---

**Le cœur du métier en Afrique de l'Ouest**, c'est donc **d'être l'interface entre les standards internationaux et les réalités opérationnelles locales** : traduire des exigences IFC ou européennes en actions concrètes dans une PME sénégalaise, un groupe cacao ivoirien ou une mine burkinabè, tout en tenant compte du niveau de maturité, des contraintes budgétaires et du contexte socio-politique.

Si tu veux, je peux creuser un angle particulier : le marché du conseil ESG à Abidjan spécifiquement (qui sont les acteurs, comment se positionner), les secteurs les plus demandeurs aujourd'hui, ou les compétences et formations pour entrer dans le métier dans la région.
```








