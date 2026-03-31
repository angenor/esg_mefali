"""Generation de graphiques SVG pour les rapports ESG.

Utilise matplotlib pour generer des graphiques en SVG inline
compatibles avec WeasyPrint.
"""

import io
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# Couleurs du theme ESG Mefali
COLORS = {
    "environment": "#22c55e",
    "social": "#3b82f6",
    "governance": "#a855f7",
    "overall": "#f59e0b",
    "sector_avg": "#94a3b8",
    "bg": "#f8fafc",
    "text": "#1e293b",
    "grid": "#e2e8f0",
}

PILLAR_LABELS = {
    "environment": "Environnement",
    "social": "Social",
    "governance": "Gouvernance",
}


def _fig_to_svg(fig: plt.Figure) -> str:
    """Convertir une figure matplotlib en chaine SVG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    svg_content = buf.getvalue().decode("utf-8")
    # Extraire uniquement la balise <svg ...> ... </svg>
    start = svg_content.find("<svg")
    return svg_content[start:] if start >= 0 else svg_content


def generate_radar_chart_svg(
    scores: dict[str, float],
    size: tuple[float, float] = (5.5, 5.5),
) -> str:
    """Generer un radar chart SVG des 3 piliers E-S-G.

    Args:
        scores: Dict avec cles 'environment', 'social', 'governance' (0-100).
        size: Taille de la figure en pouces.

    Returns:
        Chaine SVG du graphique radar.
    """
    labels = [PILLAR_LABELS[k] for k in ("environment", "social", "governance")]
    values = [scores.get(k, 0) for k in ("environment", "social", "governance")]
    colors = [COLORS[k] for k in ("environment", "social", "governance")]

    # Fermer le polygone
    num_vars = len(labels)
    angles = [n / num_vars * 2 * math.pi for n in range(num_vars)]
    angles += angles[:1]
    values_closed = values + values[:1]

    fig, ax = plt.subplots(figsize=size, subplot_kw={"polar": True})

    # Grille de fond
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=9, color=COLORS["text"])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=13, fontweight="bold", color=COLORS["text"])

    # Remplissage
    ax.fill(angles, values_closed, alpha=0.25, color=COLORS["overall"])
    ax.plot(angles, values_closed, linewidth=2, color=COLORS["overall"])

    # Points colores par pilier
    for i, (angle, value, color) in enumerate(zip(angles[:-1], values, colors)):
        ax.scatter(angle, value, c=color, s=100, zorder=5, edgecolors="white", linewidths=2)
        ax.annotate(
            f"{value:.0f}",
            xy=(angle, value),
            xytext=(0, 14),
            textcoords="offset points",
            ha="center",
            fontsize=12,
            fontweight="bold",
            color=color,
        )

    ax.grid(color=COLORS["grid"], linewidth=0.5)
    ax.spines["polar"].set_color(COLORS["grid"])

    return _fig_to_svg(fig)


def generate_bar_chart_svg(
    criteria_scores: list[dict],
    pillar_label: str,
    size: tuple[float, float] = (7, 3.5),
) -> str:
    """Generer un graphique en barres horizontales des scores par critere.

    Args:
        criteria_scores: Liste de dicts avec 'code', 'label', 'score', 'max'.
        pillar_label: Nom du pilier pour le titre.
        size: Taille de la figure en pouces.

    Returns:
        Chaine SVG du graphique barres.
    """
    labels = [c["label"] for c in criteria_scores]
    scores = [c["score"] for c in criteria_scores]
    max_score = criteria_scores[0]["max"] if criteria_scores else 10

    fig, ax = plt.subplots(figsize=size)

    y_pos = np.arange(len(labels))
    bar_colors = [
        COLORS["environment"] if s >= 7
        else COLORS["overall"] if s >= 4
        else "#ef4444"
        for s in scores
    ]

    bars = ax.barh(y_pos, scores, color=bar_colors, height=0.6, edgecolor="white", linewidth=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10, color=COLORS["text"])
    ax.set_xlim(0, max_score)
    ax.set_xlabel("Score", fontsize=10, color=COLORS["text"])
    ax.set_title(pillar_label, fontsize=13, fontweight="bold", color=COLORS["text"], pad=10)

    # Afficher la valeur sur chaque barre
    for bar, score in zip(bars, scores):
        ax.text(
            bar.get_width() + 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{score}/{max_score}",
            va="center",
            fontsize=10,
            color=COLORS["text"],
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["grid"])
    ax.spines["left"].set_color(COLORS["grid"])
    ax.tick_params(axis="x", colors=COLORS["text"], labelsize=8)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.3, alpha=0.5)
    ax.invert_yaxis()

    fig.tight_layout()
    return _fig_to_svg(fig)


def generate_benchmark_chart_svg(
    company_scores: dict[str, float],
    sector_averages: dict[str, float],
    sector_name: str,
    size: tuple[float, float] = (7, 4),
) -> str:
    """Generer un graphique comparatif entreprise vs moyenne sectorielle.

    Args:
        company_scores: Scores de l'entreprise (environment, social, governance, overall).
        sector_averages: Moyennes sectorielles.
        sector_name: Nom du secteur pour la legende.
        size: Taille de la figure en pouces.

    Returns:
        Chaine SVG du graphique benchmark.
    """
    categories = ["Environnement", "Social", "Gouvernance", "Global"]
    keys = ["environment", "social", "governance", "overall"]

    company_vals = [company_scores.get(k, 0) for k in keys]
    sector_vals = [sector_averages.get(k, 0) for k in keys]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=size)

    bars1 = ax.bar(
        x - width / 2,
        company_vals,
        width,
        label="Votre entreprise",
        color=COLORS["overall"],
        edgecolor="white",
        linewidth=0.5,
    )
    bars2 = ax.bar(
        x + width / 2,
        sector_vals,
        width,
        label=f"Moyenne {sector_name}",
        color=COLORS["sector_avg"],
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_ylim(0, 100)
    ax.set_ylabel("Score", fontsize=9, color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, color=COLORS["text"])
    ax.legend(fontsize=10, loc="upper right")

    # Valeurs sur les barres
    for bars in (bars1, bars2):
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 1.5,
                f"{height:.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color=COLORS["text"],
            )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["grid"])
    ax.spines["left"].set_color(COLORS["grid"])
    ax.tick_params(colors=COLORS["text"], labelsize=8)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.3, alpha=0.5)

    fig.tight_layout()
    return _fig_to_svg(fig)
