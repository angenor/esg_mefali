"""Helper partage : instructions communes pour le tool ask_interactive_question.

Injecte dans les 7 prompts des modules metier (chat, esg_scoring, carbon,
financing, application, credit, action_plan, profiling). Chaque prompt module
ajoute ses propres exemples specifiques en plus de ces regles generiques.
"""

WIDGET_INSTRUCTION = """## OUTIL INTERACTIF — ask_interactive_question

Tu disposes d'un outil `ask_interactive_question` qui rend tes questions plus
agreables : au lieu d'une liste textuelle, l'utilisateur clique sur des boutons.

### Quand l'utiliser
- Question fermee a 2 a 8 options courtes (≤ 120 caracteres par option).
- Choix unique (`question_type='qcu'`) OU choix multiples (`question_type='qcm'`).
- Variante avec justification libre amusante :
  `qcu_justification` ou `qcm_justification` (+ `requires_justification=true`,
  + `justification_prompt` engageant — ex : « Raconte-nous pourquoi ! »).

### Quand NE PAS l'utiliser
- Questions ouvertes (« Decris ton activite »).
- Questions factuelles libres (« Quel est le nom de ton entreprise ? »).
- Plus de 8 options : reduis ou pose en texte.
- Quand les options ne sont pas mutuellement claires.

### Regles d'emploi obligatoires
1. **Un seul appel par tour** : ne pose jamais deux questions interactives
   simultanement.
2. **Pas de texte apres l'appel** : le frontend affiche le widget, attend la
   reponse, et un nouveau tour LLM demarre. N'ajoute aucun texte de relance.
3. **Options en francais avec accents** (é, è, à, ç, …) et libelles courts.

### INTERDIT ABSOLU — Ne jamais ecrire le JSON en texte
- Ne JAMAIS ecrire `{"question_type":...,"options":[...]}` ou tout fragment
  de cette structure dans ton message (ni avant, ni apres l'appel tool).
- Ne JAMAIS repeter en texte les champs `question_type`, `options`, `prompt`,
  `min_selections`, `max_selections`, `requires_justification`.
- Le widget s'affiche automatiquement a partir du tool call structure. Tout
  JSON en texte pollue la bulle assistant et casse l'experience utilisateur.
- Appelle le tool, PUIS STOP. Aucun texte de decoration, aucune repetition
  verbale des options, aucune annotation technique.
4. **Emojis facultatifs** mais bienvenus pour rendre les options reconnaissables.
5. **min_selections / max_selections** : pour QCM, fixe-les explicitement
   selon l'intention (ex : « 1 a 3 sources d'energie »).
6. **Justification** : a reserver aux questions ou la nuance compte
   (perceptions, motivations, blocages). Limite : 400 caracteres cote user.

### Exemple d'invocation
```
ask_interactive_question(
  question_type="qcu",
  prompt="Quel est ton secteur principal ?",
  options=[
    {"id": "agri", "label": "Agriculture", "emoji": "🌾"},
    {"id": "energy", "label": "Énergie", "emoji": "⚡"},
    {"id": "recycle", "label": "Recyclage", "emoji": "♻️"},
  ],
)
```
"""
