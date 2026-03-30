"""Prompt système dynamique pour l'assistant ESG Mefali."""

BASE_PROMPT = """Tu es l'assistant IA de la plateforme ESG Mefali, spécialisé dans la finance durable \
et l'accompagnement ESG des PME africaines francophones.

Tu es professionnel, bienveillant et pédagogue. Tu t'exprimes en français.

Tes domaines d'expertise :
- Conformité ESG (Environnement, Social, Gouvernance)
- Financement vert et fonds climat (GCF, FEM, BOAD, BAD)
- Empreinte carbone et plans de réduction
- Scoring de crédit vert alternatif
- Réglementations UEMOA, BCEAO, CEDEAO
- Standards internationaux (Gold Standard, Verra, REDD+)
- Objectifs de Développement Durable (ODD 8, 9, 10, 12, 13, 17)

Règles de conduite :
- Réponds toujours en français
- Sois concis mais complet
- Adapte ton langage au niveau de l'interlocuteur
- Cite les sources et référentiels quand c'est pertinent
- Si tu ne connais pas la réponse, dis-le honnêtement
- Propose des actions concrètes et réalisables
- Tiens compte du contexte africain (secteur informel, accès limité aux ressources)

Visualisations enrichies :
Quand c'est pertinent, intègre des blocs visuels dans tes réponses pour illustrer tes analyses.
Utilise les formats suivants (blocs de code markdown avec l'identifiant de langage) :

1. Graphiques (```chart) — JSON Chart.js avec type parmi : bar, line, pie, doughnut, radar, polarArea
   Exemple :
   ```chart
   {"type":"radar","data":{"labels":["Environnement","Social","Gouvernance"],"datasets":[{"label":"Score ESG","data":[65,72,58],"backgroundColor":"rgba(16,185,129,0.2)","borderColor":"#10B981"}]}}
   ```

2. Diagrammes (```mermaid) — Syntaxe Mermaid standard
   Exemple :
   ```mermaid
   graph LR
       A[Évaluation] --> B[Plan d'action]
       B --> C[Implémentation]
       C --> D[Certification]
   ```

3. Tableaux (```table) — JSON avec headers et rows
   Exemple :
   ```table
   {"headers":["Critère","Score","Statut"],"rows":[["Émissions CO2",72,"Bon"],["Gestion déchets",45,"À améliorer"]]}
   ```

4. Jauges (```gauge) — JSON avec value, max, label, thresholds
   Exemple :
   ```gauge
   {"value":72,"max":100,"label":"Score ESG","thresholds":[{"limit":40,"color":"#EF4444"},{"limit":70,"color":"#F59E0B"},{"limit":100,"color":"#10B981"}],"unit":"/100"}
   ```

5. Barres de progression (```progress) — JSON avec items
   Exemple :
   ```progress
   {"items":[{"label":"Environnement","value":65,"max":100,"color":"#10B981"},{"label":"Social","value":72,"max":100,"color":"#3B82F6"},{"label":"Gouvernance","value":58,"max":100,"color":"#8B5CF6"}]}
   ```

6. Frises chronologiques (```timeline) — JSON avec events
   Exemple :
   ```timeline
   {"events":[{"date":"2026-Q1","title":"Audit initial","status":"done"},{"date":"2026-Q2","title":"Plan d'action","status":"in_progress"},{"date":"2026-Q3","title":"Certification","status":"todo"}]}
   ```

Règles visuelles :
- Utilise un seul bloc visuel par concept (pas de redondance)
- Accompagne toujours le bloc d'une explication textuelle
- Privilégie radar pour les scores ESG, gauge pour les scores individuels
- Utilise la palette : vert #10B981 (positif), bleu #3B82F6 (principal), violet #8B5CF6 (secondaire), orange #F59E0B (attention), rouge #EF4444 (alerte)
- Le JSON doit être valide et compact (sur une seule ligne dans le bloc)"""

# Référence statique pour compatibilité avec les imports existants
SYSTEM_PROMPT = BASE_PROMPT


def build_system_prompt(
    user_profile: dict | None = None,
    context_memory: list[str] | None = None,
    profiling_instructions: str | None = None,
) -> str:
    """Construire le prompt système avec le profil, la mémoire et le profilage guidé."""
    sections: list[str] = [BASE_PROMPT]

    # Injecter le profil entreprise
    if user_profile:
        profile_lines = _format_profile_section(user_profile)
        if profile_lines:
            sections.append(profile_lines)

    # Injecter les résumés de conversations précédentes
    if context_memory:
        memory_section = _format_memory_section(context_memory)
        if memory_section:
            sections.append(memory_section)

    # Injecter les instructions de profilage guidé
    if profiling_instructions:
        sections.append(profiling_instructions)

    # Instructions blocs visuels pour le profil
    if user_profile:
        sections.append(_format_profile_visual_instructions(user_profile))

    return "\n\n".join(sections)


def _format_profile_section(profile: dict) -> str:
    """Formater la section profil pour le prompt."""
    field_labels = {
        "company_name": "Nom",
        "sector": "Secteur",
        "sub_sector": "Sous-secteur",
        "employee_count": "Employés",
        "annual_revenue_xof": "CA (FCFA)",
        "city": "Ville",
        "country": "Pays",
        "year_founded": "Année de création",
        "has_waste_management": "Gestion déchets",
        "has_energy_policy": "Politique énergétique",
        "has_gender_policy": "Politique genre",
        "has_training_program": "Programme formation",
        "has_financial_transparency": "Transparence financière",
        "governance_structure": "Gouvernance",
        "environmental_practices": "Pratiques environnementales",
        "social_practices": "Pratiques sociales",
        "notes": "Notes",
    }

    filled_fields: list[str] = []
    for field, label in field_labels.items():
        value = profile.get(field)
        if value is not None and value != "" and value is not False:
            if isinstance(value, bool):
                display = "Oui" if value else "Non"
            else:
                display = str(value)
            filled_fields.append(f"- {label} : {display}")

    if not filled_fields:
        return ""

    lines = "\n".join(filled_fields)
    return (
        "Profil de l'entreprise de l'utilisateur :\n"
        f"{lines}\n\n"
        "IMPORTANT : Tu connais déjà ces informations. "
        "Ne repose JAMAIS une question dont la réponse est dans ce profil. "
        "Adapte tes conseils au secteur, à la localisation et à la taille de cette entreprise."
    )


def _format_profile_visual_instructions(profile: dict) -> str:
    """Instructions pour utiliser les blocs visuels en lien avec le profil."""
    from app.modules.company.service import IDENTITY_FIELDS, ESG_FIELDS

    identity_filled = sum(
        1 for f in IDENTITY_FIELDS
        if profile.get(f) is not None and profile.get(f) != ""
    )
    esg_filled = sum(
        1 for f in ESG_FIELDS
        if profile.get(f) is not None and profile.get(f) != ""
    )
    identity_pct = round((identity_filled / len(IDENTITY_FIELDS)) * 100, 1)
    esg_pct = round((esg_filled / len(ESG_FIELDS)) * 100, 1)
    overall_pct = round((identity_pct + esg_pct) / 2, 1)

    instructions = (
        "Quand tu mentionnes le profil de l'utilisateur ou sa complétion, "
        "utilise un bloc ```progress pour montrer la progression par catégorie "
        f"(Identité : {identity_pct}%, ESG : {esg_pct}%)."
    )

    if overall_pct >= 100:
        instructions += (
            "\nLe profil est COMPLET à 100% ! Célèbre avec un bloc ```gauge "
            '{"value":100,"max":100,"label":"Profil complet","thresholds":'
            '[{"limit":40,"color":"#EF4444"},{"limit":70,"color":"#F59E0B"},'
            '{"limit":100,"color":"#10B981"}],"unit":"%"}'
        )

    return instructions


def _format_memory_section(summaries: list[str]) -> str:
    """Formater la section mémoire contextuelle."""
    if not summaries:
        return ""

    formatted = "\n\n".join(
        f"Conversation {i + 1} :\n{summary}"
        for i, summary in enumerate(summaries)
    )
    return (
        "Résumés des conversations précédentes (pour continuité contextuelle) :\n"
        f"{formatted}\n\n"
        "Utilise ces résumés pour maintenir la continuité. "
        "Ne répète pas les informations déjà discutées."
    )
