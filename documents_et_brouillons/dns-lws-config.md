# Configuration DNS LWS — `esg.mefali.com`

## Enregistrement à créer

Panel LWS → **Domaines** → `mefali.com` → **Zone DNS** → **Ajouter une entrée**

| Champ | Valeur |
|---|---|
| Type | `A` |
| Sous-domaine | `esg` |
| Cible | `161.97.92.63` |
| TTL | `3600` |

## Optionnel — IPv6

| Champ | Valeur |
|---|---|
| Type | `AAAA` |
| Sous-domaine | `esg` |
| Cible | `2a02:c207:2308:3498::1` |
| TTL | `3600` |

## À éviter

- Pas de `CNAME` (un CNAME prend un nom, pas une IP)
- Pas d'entrée `www.esg`
- Pas de redirection web / parking LWS sur ce sous-domaine
