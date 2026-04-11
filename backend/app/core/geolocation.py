"""Détection de pays via géolocalisation IP.

Utilise le service gratuit ipapi.co (1000 requêtes/jour, sans clé API)
pour résoudre une adresse IP en pays. Retourne le nom du pays en français
pour les pays ciblés par la plateforme (UEMOA/CEDEAO, CEMAC, francophones).
"""

import logging

import httpx
from fastapi import Request

logger = logging.getLogger(__name__)

# Mapping ISO 3166-1 alpha-2 → nom de pays en français.
# Couvre prioritairement les zones UEMOA, CEDEAO, CEMAC et pays francophones.
COUNTRY_NAMES_FR: dict[str, str] = {
    # UEMOA / CEDEAO
    "CI": "Côte d'Ivoire",
    "SN": "Sénégal",
    "ML": "Mali",
    "BF": "Burkina Faso",
    "NE": "Niger",
    "TG": "Togo",
    "BJ": "Bénin",
    "GW": "Guinée-Bissau",
    "GN": "Guinée",
    "NG": "Nigéria",
    "GH": "Ghana",
    "LR": "Libéria",
    "SL": "Sierra Leone",
    "CV": "Cap-Vert",
    "GM": "Gambie",
    # CEMAC / Afrique centrale
    "CM": "Cameroun",
    "GA": "Gabon",
    "CG": "République du Congo",
    "CD": "République démocratique du Congo",
    "TD": "Tchad",
    "CF": "République centrafricaine",
    "GQ": "Guinée équatoriale",
    # Afrique du Nord
    "MA": "Maroc",
    "DZ": "Algérie",
    "TN": "Tunisie",
    "LY": "Libye",
    "EG": "Égypte",
    # Autres Afrique
    "MR": "Mauritanie",
    "MG": "Madagascar",
    "DJ": "Djibouti",
    "KM": "Comores",
    "RW": "Rwanda",
    "BI": "Burundi",
    "ET": "Éthiopie",
    "KE": "Kenya",
    "TZ": "Tanzanie",
    "UG": "Ouganda",
    "ZA": "Afrique du Sud",
    # Europe francophone
    "FR": "France",
    "BE": "Belgique",
    "CH": "Suisse",
    "LU": "Luxembourg",
    "MC": "Monaco",
    # Amérique francophone
    "CA": "Canada",
    "HT": "Haïti",
}

# Liste ordonnée pour le dropdown frontend (renvoyée par l'API).
SUPPORTED_COUNTRIES: list[str] = [
    # UEMOA en tête (cœur de cible)
    "Côte d'Ivoire",
    "Sénégal",
    "Mali",
    "Burkina Faso",
    "Niger",
    "Togo",
    "Bénin",
    "Guinée-Bissau",
    # CEDEAO
    "Guinée",
    "Nigéria",
    "Ghana",
    "Libéria",
    "Sierra Leone",
    "Cap-Vert",
    "Gambie",
    # CEMAC
    "Cameroun",
    "Gabon",
    "République du Congo",
    "République démocratique du Congo",
    "Tchad",
    "République centrafricaine",
    "Guinée équatoriale",
    # Afrique du Nord
    "Maroc",
    "Algérie",
    "Tunisie",
    "Libye",
    "Égypte",
    # Autres Afrique
    "Mauritanie",
    "Madagascar",
    "Djibouti",
    "Comores",
    "Rwanda",
    "Burundi",
    "Éthiopie",
    "Kenya",
    "Tanzanie",
    "Ouganda",
    "Afrique du Sud",
    # Europe francophone
    "France",
    "Belgique",
    "Suisse",
    "Luxembourg",
    "Monaco",
    # Amérique francophone
    "Canada",
    "Haïti",
    # Fallback
    "Autre",
]

_GEOLOCATION_TIMEOUT_SECONDS = 2.5
_GEOLOCATION_URL = "https://ipapi.co/{ip}/json/"
_GEOLOCATION_SELF_URL = "https://ipapi.co/json/"


def get_client_ip(request: Request) -> str | None:
    """Extraire l'IP client réelle en tenant compte des reverse proxies.

    Priorise les en-têtes `X-Forwarded-For` (premier IP) et `X-Real-IP`
    typiquement injectés par nginx ou un load balancer.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For: client, proxy1, proxy2 → on veut le premier
        first = forwarded.split(",")[0].strip()
        if first:
            return first

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return None


def _is_private_ip(ip: str) -> bool:
    """Détecter les IP locales/privées pour lesquelles la géolocalisation échouera."""
    if not ip:
        return True
    if ip in {"127.0.0.1", "::1", "localhost", "testclient"}:
        return True
    if ip.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18.",
                      "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
                      "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
                      "172.29.", "172.30.", "172.31.")):
        return True
    return False


def _resolve_country_name(data: dict) -> str | None:
    """Extraire le nom de pays français depuis la réponse ipapi.co."""
    country_code = data.get("country") or data.get("country_code")
    if not country_code:
        return None

    fr_name = COUNTRY_NAMES_FR.get(country_code.upper())
    if fr_name is None:
        # Fallback : nom en anglais retourné par l'API
        return data.get("country_name") or None
    return fr_name


async def detect_country_from_ip(ip: str | None) -> str | None:
    """Résoudre une IP en nom de pays français.

    - Si l'IP est publique : requête `ipapi.co/<ip>/json/`
    - Si l'IP est privée/locale (dev sur localhost, réseau interne) :
      fallback sur `ipapi.co/json/` qui résout via l'IP publique sortante
      du serveur. En dev, c'est l'IP du développeur ; en prod derrière
      nginx configuré avec `X-Forwarded-For`, ce chemin n'est normalement
      pas emprunté (on a la vraie IP client).

    Retourne `None` si le service externe échoue (timeout, rate limit,
    erreur réseau) ou si le code pays est inconnu.
    """
    try:
        async with httpx.AsyncClient(timeout=_GEOLOCATION_TIMEOUT_SECONDS) as client:
            if ip is None or _is_private_ip(ip):
                url = _GEOLOCATION_SELF_URL
            else:
                url = _GEOLOCATION_URL.format(ip=ip)

            response = await client.get(url)
            if response.status_code != 200:
                logger.debug("Géolocalisation %s : status %s", url, response.status_code)
                return None

            return _resolve_country_name(response.json())
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.debug("Échec géolocalisation (ip=%s) : %s", ip, exc)
        return None


async def detect_country_from_request(request: Request) -> str | None:
    """Combinaison pratique : extraire l'IP du `Request` et résoudre le pays."""
    ip = get_client_ip(request)
    return await detect_country_from_ip(ip)
