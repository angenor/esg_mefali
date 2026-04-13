"""Helper partage : instructions pour le tool trigger_guided_tour.

Injecte dans les 6 prompts systeme des modules eligibles au guidage visuel
(chat post-onboarding, esg_scoring, carbon, financing, credit, action_plan).
Les modules application, document, profiling et router ne recoivent PAS
ce prompt — le guidage ne concerne pas les phases de saisie ou d'extraction.

Voir story 6.2 : le tool `trigger_guided_tour` existe deja (story 6.1),
cette instruction active sa capacite d'appel par le LLM.
"""

GUIDED_TOUR_INSTRUCTION = """## OUTIL GUIDAGE VISUEL — trigger_guided_tour

Tu disposes d'un outil `trigger_guided_tour` qui lance un parcours interactif
sur l'interface (flechage, popovers, navigation inter-pages). L'utilisateur
voit alors ses resultats explique-pas-a-pas sur les ecrans dedies.

### Parcours disponibles
- `show_esg_results` — Resultats de l'evaluation ESG (/esg/results)
- `show_carbon_results` — Bilan carbone et plan de reduction (/carbon/results)
- `show_financing_catalog` — Catalogue de fonds verts et matchs (/financing)
- `show_credit_score` — Score credit vert alternatif (/credit-score)
- `show_action_plan` — Feuille de route 6-12-24 mois (/action-plan)
- `show_dashboard_overview` — Vue d'ensemble du tableau de bord (/dashboard)

### Quand proposer un guidage
1. **Apres completion d'un module** : evaluation ESG terminee, bilan carbone
   finalise, plan d'action genere, dossier financement soumis, score de credit
   calcule. C'est le moment ideal pour montrer les resultats visuellement.
2. **Sur demande explicite de l'utilisateur** : il dit « montre-moi »,
   « guide-moi vers », « ou sont mes resultats », « visualise-moi »,
   « fais-moi visiter », ou toute formulation indiquant clairement qu'il
   veut etre accompagne vers un ecran.

### Regles de declenchement obligatoires

1. **Apres un module (proposition)** : appelle d'abord `ask_interactive_question`
   pour demander le consentement de l'utilisateur.
   - `question_type="qcu"`
   - 2 options : `{"id":"yes","label":"Oui, montre-moi","emoji":"👀"}` et
     `{"id":"no","label":"Non merci","emoji":"🙏"}`.
   Si l'utilisateur choisit `yes` au tour suivant, appelle alors
   `trigger_guided_tour(tour_id)`.

2. **Sur demande explicite (declenchement direct)** : appelle
   `trigger_guided_tour(tour_id)` IMMEDIATEMENT, SANS passer par
   `ask_interactive_question`. L'intent est deja clair, pas besoin
   de consentement supplementaire.

3. **Un seul guidage par tour** : ne declenche jamais plusieurs parcours
   dans la meme reponse. Attends le retour de l'utilisateur avant de
   proposer un autre parcours.

4. **Pas de texte apres l'appel** : une fois `trigger_guided_tour` appele,
   le frontend prend la main, le widget de chat se retracte automatiquement
   et le parcours demarre. N'ajoute aucun texte apres le tool call.

5. **Securite du champ `context`** (NFR10 — rappel) :
   - `context` peut porter un prenom ou des chiffres non sensibles pour
     personnaliser le texte du popover (ex : `{"user_first_name": "Fatou"}`,
     `{"pillar_top": "Social"}`, `{"score": 72}`).
   - JAMAIS d'IDs techniques (`user_id`, `conversation_id`), de tokens,
     d'emails, de mots de passe, ni de donnees PII ou financieres sensibles.

### Exemple 1 — Proposition post-module (evaluation ESG terminee)

Apres avoir cloture une evaluation ESG complete (30 criteres notes,
visuels radar+gauge+table affiches), propose le guidage :
```
ask_interactive_question(
  question_type="qcu",
  prompt="Evaluation terminee ! Veux-tu que je te montre tes resultats en detail sur l'ecran ?",
  options=[
    {"id":"yes","label":"Oui, montre-moi","emoji":"👀"},
    {"id":"no","label":"Non merci","emoji":"🙏"},
  ],
)
```
Si l'utilisateur choisit `yes` au tour suivant :
```
trigger_guided_tour(
  tour_id="show_esg_results",
  context={"pillar_top":"Social"},
)
```

### Exemple 2 — Declenchement direct (demande explicite)

Utilisateur : « Montre-moi mes resultats carbone »
```
trigger_guided_tour(
  tour_id="show_carbon_results",
)
```
Pas de `ask_interactive_question` : l'utilisateur a deja demande
explicitement, toute question de consentement serait redondante.

### Exemple 3 — Declenchement direct avec contexte

Utilisateur : « Guide-moi vers le catalogue des fonds verts, je cherche pour
mon projet solaire »
```
trigger_guided_tour(
  tour_id="show_financing_catalog",
  context={"project_hint":"solaire"},
)
```
"""
