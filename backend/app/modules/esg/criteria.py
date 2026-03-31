"""Definition des 30 criteres ESG contextualises pour les PME africaines.

Grille de 30 criteres (10 par pilier E-S-G), chacun note de 0 a 10.
Adaptes au contexte UEMOA/CEDEAO et au secteur informel.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ESGCriterion:
    """Definition d'un critere ESG."""

    code: str
    pillar: str
    label: str
    description: str
    question: str


# --- Pilier Environnement (E1-E10) ---

ENVIRONMENT_CRITERIA: tuple[ESGCriterion, ...] = (
    ESGCriterion(
        code="E1",
        pillar="environment",
        label="Gestion des dechets",
        description="Pratiques de tri, recyclage et elimination des dechets.",
        question="Comment votre entreprise gere-t-elle ses dechets ? Avez-vous un systeme de tri ou de recyclage ?",
    ),
    ESGCriterion(
        code="E2",
        pillar="environment",
        label="Consommation d'energie",
        description="Niveau de consommation energetique et efforts de reduction.",
        question="Quelle est votre consommation energetique principale ? Avez-vous des initiatives pour la reduire ?",
    ),
    ESGCriterion(
        code="E3",
        pillar="environment",
        label="Emissions carbone",
        description="Emissions de gaz a effet de serre directes et indirectes.",
        question="Avez-vous une idee de vos emissions de CO2 ? Utilisez-vous des vehicules ou machines polluants ?",
    ),
    ESGCriterion(
        code="E4",
        pillar="environment",
        label="Ressources naturelles",
        description="Utilisation responsable des matieres premieres et ressources.",
        question="Comment gerez-vous vos matieres premieres ? Avez-vous des pratiques pour limiter le gaspillage ?",
    ),
    ESGCriterion(
        code="E5",
        pillar="environment",
        label="Biodiversite",
        description="Impact sur la faune, la flore et les ecosystemes locaux.",
        question="Votre activite a-t-elle un impact sur l'environnement naturel local (forets, cours d'eau, faune) ?",
    ),
    ESGCriterion(
        code="E6",
        pillar="environment",
        label="Gestion de l'eau",
        description="Consommation, traitement et protection des ressources en eau.",
        question="Comment gerez-vous votre consommation d'eau ? Traitez-vous vos eaux usees ?",
    ),
    ESGCriterion(
        code="E7",
        pillar="environment",
        label="Politique environnementale",
        description="Existence d'une politique ou charte environnementale formelle.",
        question="Avez-vous une politique environnementale ecrite ou des engagements formels en matiere d'environnement ?",
    ),
    ESGCriterion(
        code="E8",
        pillar="environment",
        label="Energies renouvelables",
        description="Utilisation de sources d'energie renouvelables (solaire, eolien, biomasse).",
        question="Utilisez-vous des energies renouvelables (panneaux solaires, biomasse) ? Envisagez-vous d'en adopter ?",
    ),
    ESGCriterion(
        code="E9",
        pillar="environment",
        label="Transport vert",
        description="Optimisation logistique et reduction de l'empreinte transport.",
        question="Comment organisez-vous vos transports et livraisons ? Cherchez-vous a reduire les trajets ou emissions ?",
    ),
    ESGCriterion(
        code="E10",
        pillar="environment",
        label="Economie circulaire",
        description="Reutilisation, reparation et valorisation des produits et materiaux.",
        question="Pratiquez-vous la reutilisation ou la valorisation de vos produits et sous-produits ?",
    ),
)

# --- Pilier Social (S1-S10) ---

SOCIAL_CRITERIA: tuple[ESGCriterion, ...] = (
    ESGCriterion(
        code="S1",
        pillar="social",
        label="Conditions de travail",
        description="Qualite de l'environnement de travail, horaires, contrats.",
        question="Quelles sont les conditions de travail dans votre entreprise ? Vos employes ont-ils des contrats formels ?",
    ),
    ESGCriterion(
        code="S2",
        pillar="social",
        label="Egalite hommes-femmes",
        description="Parite, egalite salariale et acces aux postes de responsabilite.",
        question="Quelle est la proportion de femmes dans votre entreprise, y compris aux postes de direction ?",
    ),
    ESGCriterion(
        code="S3",
        pillar="social",
        label="Formation et developpement",
        description="Programmes de formation continue et developpement des competences.",
        question="Proposez-vous des formations a vos employes ? Combien de jours par an en moyenne ?",
    ),
    ESGCriterion(
        code="S4",
        pillar="social",
        label="Impact communautaire",
        description="Contribution au developpement economique et social de la communaute locale.",
        question="Comment votre entreprise contribue-t-elle au developpement de votre communaute locale ?",
    ),
    ESGCriterion(
        code="S5",
        pillar="social",
        label="Sante et securite",
        description="Mesures de protection de la sante et securite des travailleurs.",
        question="Quelles mesures de securite et de sante au travail avez-vous mises en place ?",
    ),
    ESGCriterion(
        code="S6",
        pillar="social",
        label="Remuneration equitable",
        description="Niveau de remuneration juste et avantages sociaux.",
        question="Comment se situent vos remunerations par rapport au marche local ? Offrez-vous des avantages sociaux ?",
    ),
    ESGCriterion(
        code="S7",
        pillar="social",
        label="Inclusion et diversite",
        description="Politiques d'inclusion des personnes handicapees, minorites, jeunes.",
        question="Avez-vous des pratiques favorisant l'inclusion et la diversite dans votre recrutement ?",
    ),
    ESGCriterion(
        code="S8",
        pillar="social",
        label="Dialogue social",
        description="Communication interne, representation du personnel, gestion des conflits.",
        question="Comment se passe la communication avec vos employes ? Existe-t-il un representant du personnel ?",
    ),
    ESGCriterion(
        code="S9",
        pillar="social",
        label="Fournisseurs locaux",
        description="Part des achats aupres de fournisseurs locaux et nationaux.",
        question="Quelle proportion de vos achats provient de fournisseurs locaux ou nationaux ?",
    ),
    ESGCriterion(
        code="S10",
        pillar="social",
        label="Satisfaction employes",
        description="Mesure de la satisfaction, du turnover et de l'engagement des employes.",
        question="Quel est le niveau de satisfaction de vos employes ? Mesurez-vous le turnover ?",
    ),
)

# --- Pilier Gouvernance (G1-G10) ---

GOVERNANCE_CRITERIA: tuple[ESGCriterion, ...] = (
    ESGCriterion(
        code="G1",
        pillar="governance",
        label="Transparence financiere",
        description="Clarte et accessibilite des comptes et rapports financiers.",
        question="Vos comptes financiers sont-ils tenus a jour et accessibles aux parties prenantes ?",
    ),
    ESGCriterion(
        code="G2",
        pillar="governance",
        label="Structure de decision",
        description="Organisation du pouvoir decisionnel et contre-pouvoirs.",
        question="Comment sont prises les decisions strategiques dans votre entreprise ? Existe-t-il un conseil ?",
    ),
    ESGCriterion(
        code="G3",
        pillar="governance",
        label="Ethique des affaires",
        description="Respect des regles ethiques dans les relations commerciales.",
        question="Comment gerez-vous l'ethique dans vos relations commerciales (clients, fournisseurs, partenaires) ?",
    ),
    ESGCriterion(
        code="G4",
        pillar="governance",
        label="Conformite reglementaire",
        description="Respect des lois et reglementations en vigueur.",
        question="Etes-vous en conformite avec les reglementations locales (fiscale, sociale, environnementale) ?",
    ),
    ESGCriterion(
        code="G5",
        pillar="governance",
        label="Politique anti-corruption",
        description="Mesures de prevention et de lutte contre la corruption.",
        question="Avez-vous une politique anti-corruption formelle ? Comment gerez-vous les risques de corruption ?",
    ),
    ESGCriterion(
        code="G6",
        pillar="governance",
        label="Gestion des risques",
        description="Identification, evaluation et mitigation des risques strategiques.",
        question="Avez-vous un processus d'identification et de gestion des risques pour votre entreprise ?",
    ),
    ESGCriterion(
        code="G7",
        pillar="governance",
        label="Responsabilite du dirigeant",
        description="Engagement personnel du dirigeant dans la strategie ESG.",
        question="En tant que dirigeant, comment vous impliquez-vous personnellement dans les sujets ESG ?",
    ),
    ESGCriterion(
        code="G8",
        pillar="governance",
        label="Communication parties prenantes",
        description="Dialogue avec les actionnaires, employes, communautes et regulateurs.",
        question="Comment communiquez-vous avec vos differentes parties prenantes (employes, clients, communaute) ?",
    ),
    ESGCriterion(
        code="G9",
        pillar="governance",
        label="Confidentialite des donnees",
        description="Protection des donnees personnelles et professionnelles.",
        question="Comment protegez-vous les donnees personnelles de vos clients et employes ?",
    ),
    ESGCriterion(
        code="G10",
        pillar="governance",
        label="Planification de succession",
        description="Plans de continuite et de transmission de l'entreprise.",
        question="Avez-vous un plan de succession ou de continuite pour votre entreprise ?",
    ),
)

# Tous les criteres indexes par code
ALL_CRITERIA: tuple[ESGCriterion, ...] = (
    ENVIRONMENT_CRITERIA + SOCIAL_CRITERIA + GOVERNANCE_CRITERIA
)

CRITERIA_BY_CODE: dict[str, ESGCriterion] = {c.code: c for c in ALL_CRITERIA}

PILLAR_CRITERIA: dict[str, tuple[ESGCriterion, ...]] = {
    "environment": ENVIRONMENT_CRITERIA,
    "social": SOCIAL_CRITERIA,
    "governance": GOVERNANCE_CRITERIA,
}

PILLAR_LABELS: dict[str, str] = {
    "environment": "Environnement",
    "social": "Social",
    "governance": "Gouvernance",
}

PILLAR_ORDER: list[str] = ["environment", "social", "governance"]

TOTAL_CRITERIA: int = len(ALL_CRITERIA)
