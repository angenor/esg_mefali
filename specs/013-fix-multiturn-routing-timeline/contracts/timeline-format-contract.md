# Timeline Format Contract

## Format canonique (prompts backend)

```json
{
  "events": [
    {
      "date": "Mois 1-2",
      "title": "Titre de l'action",
      "status": "todo",
      "description": "Detail optionnel"
    }
  ]
}
```

### Champs obligatoires par evenement
- `date` (string) : Periode ou date
- `title` (string) : Titre de l'evenement
- `status` (string) : `"done"`, `"in_progress"`, ou `"todo"`

### Champs optionnels par evenement
- `description` (string) : Detail supplementaire

## Normalisation frontend (TimelineBlock.vue)

### Cle de la liste d'evenements
Priorite de resolution :
1. `events` (canonique)
2. `phases` (alias)
3. `items` (alias)
4. `steps` (alias)

### Champs par evenement
| Canonique     | Alias acceptes          | Defaut    |
|---------------|-------------------------|-----------|
| `date`        | `period`, `timeframe`   | (requis)  |
| `title`       | `name`, `label`         | (requis)  |
| `status`      | `state`                 | `"todo"`  |
| `description` | `details`, `content`    | `null`    |

### Regles de validation
- Si aucune des cles (`events`, `phases`, `items`, `steps`) n'est trouvee → erreur affichee
- Si un evenement n'a ni `date`/`period`/`timeframe` ni `title`/`name`/`label` → evenement ignore
- JSON invalide → message d'erreur sans crash
