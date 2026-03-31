# Research: Scoring de Credit Vert Alternatif

**Feature**: 010-green-credit-scoring
**Date**: 2026-03-31

## R1: Algorithme de scoring hybride — Ponderation et normalisation

**Decision**: Algorithme a deux axes (solvabilite 50%, impact vert 50%) avec sous-facteurs ponderes, normalises sur 100, module par un coefficient de confiance [0.5, 1.0].

**Rationale**: L'approche bi-axiale reflete la double nature du credit vert : capacite de remboursement (solvabilite) ET contribution environnementale (impact vert). La ponderation 50/50 est equilibree pour le contexte PME africaines ou l'impact vert est aussi important que la solvabilite classique. Le coefficient de confiance penalise les scores bases sur des donnees insuffisantes sans les empecher.

**Alternatives considered**:
- Score unique pondere : rejete car ne permet pas de distinguer un bon profil financier a faible impact vert d'un fort impact vert avec solvabilite faible
- Ponderation 70/30 (solvabilite dominante) : rejete car trop proche d'un scoring bancaire classique, ne valorise pas assez l'impact vert
- Score sans coefficient de confiance : rejete car un score base sur 2 donnees ne doit pas avoir la meme valeur qu'un score base sur 10 sources verifiees

## R2: Integration des interactions intermediaires comme signal d'engagement

**Decision**: Les interactions intermediaires contribuent a deux sous-facteurs distincts :
1. **Engagement et serieux** (solvabilite) : nombre d'intermediaires contactes, rendez-vous pris, dossiers soumis
2. **Projets verts en cours** (impact vert) : statut des candidatures via intermediaire (poids croissant : interesse < contacting < applying < submitted)

**Rationale**: Un utilisateur qui prend rendez-vous avec une banque partenaire SUNREF et soumet un dossier demontre un engagement concret dans sa demarche verte. Ce signal comportemental est plus fiable que les declarations. Le statut des candidatures via intermediaire reflete la maturite reelle des projets verts.

**Barème d'engagement intermediaire** (contribution au sous-facteur sur 100) :
- Aucune interaction : 0 points
- Intermediaire contacte (status=contacting_intermediary) : +15 points par intermediaire (max 30)
- Rendez-vous pris (implicite dans contacting→applying) : +20 points
- Dossier soumis via intermediaire (status=submitted) : +30 points
- Dossier accepte : +20 points bonus

**Alternatives considered**:
- Compter uniquement les dossiers acceptes : rejete car trop restrictif, la demarche elle-meme est un signal
- Poids egal pour tous les statuts : rejete car ne reflete pas la progressivite de l'engagement

## R3: Calcul du niveau de confiance

**Decision**: Niveau de confiance base sur la couverture des sources de donnees et leur fraicheur.

**Formule**:
```
sources_disponibles = [profil, esg, carbone, documents, candidatures, intermediaires]
couverture = nombre_sources_avec_donnees / nombre_total_sources
fraicheur = moyenne(max(0, 1 - age_en_mois/12) pour chaque source)
confiance = 0.5 + (couverture * 0.3) + (fraicheur * 0.2)
```
- Plage : [0.5, 1.0]
- Niveaux affichage : tres_faible (<0.6), faible (0.6-0.7), moyen (0.7-0.8), bon (0.8-0.9), excellent (>0.9)

**Rationale**: Combine couverture (nombre de sources) et fraicheur (anciennete des donnees). Plancher a 0.5 pour ne jamais rendre un score nul meme avec peu de donnees.

**Alternatives considered**:
- Confiance binaire (suffisant/insuffisant) : rejete car trop simpliste
- Confiance sans plancher : rejete car un score * 0 est inutile

## R4: Visualisations conversationnelles (credit_node)

**Decision**: Reutiliser les blocs visuels existants (GaugeBlock, ChartBlock, ProgressBlock, MermaidBlock) du chat avec le format markdown specifique.

**Rationale**: Le frontend parse deja les blocs ```gauge, ```chart, ```progress, ```mermaid dans les messages du chat. Pas besoin de creer de nouveaux composants de rendu.

**Format des blocs**:
- Score global : ```gauge avec value, max, label, thresholds
- Sous-scores : ```gauge x2 (solvabilite + impact vert)
- Radar facteurs : ```chart type=radar avec labels et datasets
- Couverture sources : ```progress avec items label/value/max
- Parcours amelioration : ```mermaid flowchart TD
- Historique : ```chart type=line avec dates et scores

**Alternatives considered**:
- Creer des composants chat specifiques au credit : rejete car duplication inutile, les blocs existants couvrent tous les besoins

## R5: Attestation PDF — Format et contenu

**Decision**: Attestation PDF generee via WeasyPrint + Jinja2, pattern identique aux modules reports et applications.

**Contenu de l'attestation**:
1. En-tete avec logo et titre "Attestation de Score de Credit Vert"
2. Informations entreprise (nom, secteur, localisation)
3. Score combine avec jauge visuelle
4. Sous-scores solvabilite et impact vert
5. Niveau de confiance avec explication
6. Top 5 facteurs contributeurs
7. Date de generation et date de validite (6 mois)
8. Mention legale : "Ce document est informatif et ne constitue pas un score de credit officiel"

**Rationale**: Reutilise la stack PDF existante. Le format est professionnel mais clairement marque comme informatif pour eviter toute confusion avec un scoring bancaire officiel.

## R6: Gestion du versioning et historique des scores

**Decision**: Chaque generation cree une nouvelle version (auto-increment). L'historique est conserve indefiniment. Le score le plus recent est le score "actif".

**Rationale**: Permet de tracer l'evolution et de comparer. Le versioning simple par auto-increment suffit (pas besoin de semver pour un score).

**Validite**: 6 mois par defaut. Apres expiration, le score reste consultable mais marque "expire" et l'utilisateur est invite a regenerer.
