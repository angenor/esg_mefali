# Research: Calculateur d'Empreinte Carbone Conversationnel

**Date**: 2026-03-31 | **Feature**: 007-carbon-footprint-calculator

## R1: Facteurs d'emission Afrique de l'Ouest

**Decision**: Utiliser les facteurs d'emission fournis dans la spec, stockes en constantes Python dans `emission_factors.py`.

**Rationale**: Les facteurs sont specifiques au contexte (electricite CI = 0.41 kgCO2e/kWh reflète le mix energetique ivoirien). Les stocker en constantes Python permet une mise a jour facile sans migration BDD, et suit le pattern existant de `esg/weights.py`.

**Alternatives considered**:
- Table BDD pour les facteurs → Rejetee : surcharge pour des valeurs rarement modifiees, YAGNI
- API externe (ADEME, IEA) → Rejetee : pas de source fiable specifique Afrique de l'Ouest en API, latence ajoutee

## R2: Pattern du noeud conversationnel

**Decision**: Suivre exactement le pattern du `esg_scoring_node` existant — machine a etats dans `carbon_data` du `ConversationState`, progression par categorie avec sauvegarde partielle.

**Rationale**: Le pattern est prouve, teste et coherent avec l'architecture existante. Le `esg_scoring_node` gere deja la progression par pilier (E→S→G), la reprise d'evaluations interrompues, et les visualisations inline. Le `carbon_node` suit la meme logique avec progression par categorie d'emissions.

**Alternatives considered**:
- Formulaire multi-etapes frontend → Rejetee : viole le principe III (Conversation-Driven UX)
- Noeud generique avec configuration JSON → Rejetee : abstraction prematuree, YAGNI (principe VII)

## R3: Categories d'emissions

**Decision**: 5 categories alignees sur le GHG Protocol simplifie : Energie, Transport, Dechets, Processus industriels (optionnel), Agriculture (optionnel).

**Rationale**: Le GHG Protocol est la reference mondiale. Les 3 categories principales (Energie, Transport, Dechets) couvrent 80%+ des emissions des PME. Les categories optionnelles (Processus industriels, Agriculture) ne sont proposees que si le secteur de l'entreprise le justifie.

**Alternatives considered**:
- Scope 1/2/3 GHG Protocol complet → Rejetee : trop complexe pour les PME, le Scope 3 est difficile a estimer sans donnees fournisseurs
- Categories libres → Rejetee : pas de structure pour les calculs automatiques

## R4: Equivalences parlantes

**Decision**: Utiliser des equivalences contextualisees Afrique (vols regionaux, trajets urbains) stockees en constantes Python.

**Rationale**: Les equivalences doivent parler aux utilisateurs cibles. "Equivalent a X vols Paris-Dakar" est plus parlant que "equivalent a X vols New York-Los Angeles" pour une PME ivoirienne.

**Valeurs de reference**:
- 1 vol Paris-Dakar ≈ 1.2 tCO2e (aller simple, classe economique)
- 1 an de conduite moyenne ≈ 2.4 tCO2e (15 000 km, consommation moyenne)
- 1 arbre absorbe ≈ 25 kgCO2e/an (arbre tropical mature)

## R5: Benchmarks sectoriels

**Decision**: Donnees estimees stockees en constantes Python dans `benchmarks.py`, avec fallback vers secteurs similaires.

**Rationale**: Il n'existe pas de base de donnees publique fiable de benchmarks carbone par secteur pour les PME d'Afrique de l'Ouest. Les estimations sont basees sur des moyennes internationales ajustees au contexte. Le pattern suit `esg/weights.py`.

**Alternatives considered**:
- API externe de benchmarks → Rejetee : pas de source fiable pour le contexte
- Pas de benchmark → Rejetee : la comparaison sectorielle est dans la spec (User Story 4)

## R6: Conversion FCFA vers unites physiques

**Decision**: Le carbon_node gere la conversion intelligente via le LLM. Si l'utilisateur donne un montant en FCFA (ex: facture electricite), le LLM estime la consommation physique en utilisant les tarifs moyens (ex: ~100 FCFA/kWh pour CIE).

**Rationale**: Les PME africaines ont souvent leurs factures en FCFA plutot qu'en kWh. Le LLM peut guider la conversion de maniere conversationnelle, en demandant des precisions si necessaire.

**Tarifs de reference (stockes dans emission_factors.py)**:
- Electricite CIE : ~100 FCFA/kWh (tranche sociale), ~85-130 FCFA/kWh (professionnel)
- Diesel : ~700 FCFA/L
- Essence : ~615 FCFA/L
- Gaz butane : ~6 000 FCFA/12.5 kg
