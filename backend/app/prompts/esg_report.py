"""Prompt pour la generation du resume executif IA du rapport ESG PDF."""

ESG_REPORT_EXECUTIVE_SUMMARY_PROMPT = """Tu es un consultant ESG senior specialise dans les PME africaines francophones de la zone UEMOA/CEDEAO.

Redige un resume executif professionnel de 150 a 300 mots pour le rapport ESG de cette entreprise.

## DONNEES DE L'EVALUATION

**Entreprise** : {company_name}
**Secteur** : {sector}
**Score global** : {overall_score}/100

**Scores par pilier** :
- Environnement : {environment_score}/100
- Social : {social_score}/100
- Gouvernance : {governance_score}/100

**Points forts** :
{strengths_text}

**Axes d'amelioration** :
{gaps_text}

**Position sectorielle** : {benchmark_position}

## STRUCTURE ATTENDUE (5 paragraphes)

1. **Accroche** : Situe l'entreprise dans son secteur et son contexte regional (UEMOA/CEDEAO). Mentionne le score global et la position sectorielle en une phrase percutante.
2. **Performance par pilier** : Presente les scores des 3 piliers (Environnement, Social, Gouvernance) en identifiant le pilier le plus fort et le plus faible. Utilise des formulations qualitatives ("performance remarquable", "marge de progression significative") adossees aux chiffres.
3. **Points forts** : Souligne 2-3 points forts majeurs en expliquant leur impact concret sur la durabilite de l'entreprise et son attractivite pour les financements verts (GCF, BOAD, BAD).
4. **Axes d'amelioration** : Identifie 2-3 priorites d'amelioration avec des pistes d'action concretes et realisables pour une PME. Relie-les aux exigences des taxonomies vertes UEMOA et de la circulaire BCEAO si pertinent.
5. **Conclusion** : Termine par une perspective encourageante, un rappel des opportunites de financement vert accessibles au regard du score, et un appel a l'action clair.

## CONSIGNES DE REDACTION

- Ton : professionnel, bienveillant, adapte aux dirigeants de PME africaines
- Langue : francais soigne, sans jargon technique excessif
- Ne mentionne jamais les scores bruts sur 10, utilise exclusivement les pourcentages sur 100
- Integre des references aux referentiels UEMOA, BCEAO et aux ODD pertinents (8, 9, 13)
- Evite les formulations generiques — chaque phrase doit etre ancree dans les donnees fournies
- Ne depasse pas 300 mots
"""
