# Contract: Pattern d'enforcement tool calling dans les prompts

## Pattern "REGLE ABSOLUE"

Chaque node spécialisé qui doit forcer le tool calling DOIT suivre ce pattern dans ses `tool_instructions` :

```
## OUTILS DISPONIBLES
- `tool_name_1` : description courte
- `tool_name_2` : description courte

## REGLE ABSOLUE — TOOL CALLING OBLIGATOIRE
Quand l'utilisateur [condition], tu DOIS appeler `tool_name` AVANT de répondre.
- Ne JAMAIS [action interdite] sans avoir appelé le tool.
- Ne JAMAIS utiliser tes connaissances générales pour [action] — consulte la base via le tool.
- Si le tool échoue, informe l'utilisateur et réessaie.
```

## Application par module

### ESG Scoring Node
```
REGLE ABSOLUE : Quand l'utilisateur répond à des questions ESG, tu DOIS appeler
batch_save_esg_criteria (ou save_esg_criterion_score pour un seul critère) AVANT
de poser la question suivante. Ne JAMAIS évaluer un critère sans sauvegarder le score.
```

### Carbon Node
```
REGLE ABSOLUE : Quand l'utilisateur fournit une donnée de consommation, tu DOIS
appeler save_emission_entry pour chaque source identifiée AVANT de répondre.
Ne JAMAIS calculer des émissions sans les persister via le tool.
```

### Financing Node
```
REGLE ABSOLUE : Ne cite JAMAIS un nom de fonds sans avoir d'abord appelé
search_compatible_funds. Toute réponse sur les financements disponibles DOIT
être précédée d'un appel tool. Tes connaissances générales sur les fonds sont INTERDITES.
```

## Vérification

Un test unitaire par prompt DOIT vérifier la présence de "REGLE ABSOLUE" dans le texte généré.
