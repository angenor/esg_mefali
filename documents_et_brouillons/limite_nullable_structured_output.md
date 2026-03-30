# Limite des champs nullable dans Structured Output (LLM)

## Le probleme

Quand on utilise `with_structured_output(MonSchema)` de LangChain pour demander au LLM de retourner du JSON structure, le schema Pydantic est converti en JSON Schema et envoye au provider LLM.

Chaque champ `str | None`, `int | None`, `bool | None` etc. genere un `anyOf` (union type) dans le JSON Schema :

```json
{
  "company_name": {
    "anyOf": [{"type": "string"}, {"type": "null"}]
  }
}
```

**Anthropic impose une limite de 16 parametres avec union types** dans un meme schema. Au-dela, l'API retourne une erreur 400 :

```
Schemas contains too many parameters with union types (17 parameters with type
arrays or anyOf). This causes exponential compilation cost. Reduce the number
of nullable or union-typed parameters (limit: 16 parameters with unions).
```

## Pourquoi c'est un piege

- L'erreur est **silencieuse** si on catch les exceptions (comme dans notre `extract_profile_from_message`)
- Ca peut fonctionner avec un provider (OpenAI, Mistral) et casser avec un autre (Anthropic)
- Ajouter un seul champ nullable peut tout casser
- La limite peut varier selon les providers

## Notre solution

Structurer le schema en **sous-objets imbriques** pour reduire les union types au niveau racine :

```python
# AVANT : 17 champs nullable au niveau racine = ERREUR
class ProfileExtraction(BaseModel):
    company_name: str | None = None    # union type 1
    sector: SectorEnum | None = None   # union type 2
    ...                                # union type 17 -> BOOM

# APRES : 2 sous-objets avec default_factory = 0 union types au niveau racine
class IdentityExtraction(BaseModel):   # 8 nullable ici (isole)
    company_name: str | None = None
    sector: SectorEnum | None = None
    ...

class ESGExtraction(BaseModel):        # 8 nullable ici (isole)
    has_waste_management: bool | None = None
    ...

class ProfileExtraction(BaseModel):
    identity: IdentityExtraction = Field(default_factory=IdentityExtraction)
    esg: ESGExtraction = Field(default_factory=ESGExtraction)
```

Les sous-objets avec `default_factory` ne sont **pas des union types** (pas de `| None`), donc ils ne comptent pas dans la limite. Chaque sous-objet a ses propres 8 nullable, bien en-dessous de la limite.

## Regles a retenir

1. **Ne jamais depasser 12 champs nullable** au meme niveau d'un schema d'extraction (marge de securite)
2. **Toujours structurer en sous-objets** quand le nombre de champs depasse 10
3. **Utiliser `flat_dict()`** pour aplatir le resultat apres extraction (methode helper sur le schema)
4. **Ne jamais catch silencieusement** les erreurs d'extraction sans au moins logger le message d'erreur

## Fichiers concernes

- `backend/app/modules/company/schemas.py` — `ProfileExtraction`, `IdentityExtraction`, `ESGExtraction`
- `backend/app/chains/extraction.py` — appel `with_structured_output(ProfileExtraction)`
- `backend/app/api/chat.py` — `extract_and_update_profile()` utilise `flat_dict()`
- `backend/app/graph/nodes.py` — `profiling_node` utilise `flat_dict()`
