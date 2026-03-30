# API Contract: Authentication

**Base path**: `/api/auth`

## POST /api/auth/register

Creer un nouveau compte utilisateur.

**Request body** :
```json
{
  "email": "user@example.com",
  "password": "motdepasse123",
  "full_name": "Amadou Diallo",
  "company_name": "EcoSolaire SARL"
}
```

**Validation** :
- `email` : format email valide, unique
- `password` : minimum 8 caracteres
- `full_name` : requis, 1-255 caracteres
- `company_name` : requis, 1-255 caracteres

**Reponse 201** :
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Amadou Diallo",
  "company_name": "EcoSolaire SARL",
  "created_at": "2026-03-30T10:00:00Z"
}
```

**Erreurs** :
- `400` : Validation echouee (email invalide, mot de passe trop court)
- `409` : Email deja utilise

---

## POST /api/auth/login

Authentifier un utilisateur et retourner les jetons.

**Request body** :
```json
{
  "email": "user@example.com",
  "password": "motdepasse123"
}
```

**Reponse 200** :
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Erreurs** :
- `401` : Identifiants invalides (message generique, ne revele pas si l'email existe)

---

## POST /api/auth/refresh

Rafraichir le jeton d'acces.

**Request body** :
```json
{
  "refresh_token": "eyJ..."
}
```

**Reponse 200** :
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Erreurs** :
- `401` : Refresh token invalide ou expire

---

## GET /api/auth/me

Recuperer le profil de l'utilisateur connecte.

**Headers** : `Authorization: Bearer <access_token>`

**Reponse 200** :
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Amadou Diallo",
  "company_name": "EcoSolaire SARL",
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T10:00:00Z"
}
```

**Erreurs** :
- `401` : Token manquant ou invalide
