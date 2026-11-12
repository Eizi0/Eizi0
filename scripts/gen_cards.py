#!/usr/bin/env python3
"""Génère une carte SVG par dépôt (assets/card-<dépôt>.svg) depuis l'API REST de GitHub.

Remplace les cartes de github-readme-stats.vercel.app, dont l'instance publique est suspendue
(DEPLOYMENT_PAUSED : les images s'affichaient cassées). Aucun service tiers : seuls les dépôts
publics sont lus, et GitHub sert directement les fichiers du dépôt. Même thème graphite/bleu que
le reste du profil.

Usage : GH_TOKEN=... python3 scripts/gen_cards.py [dossier_de_sortie]
"""
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from html import escape

USER = os.environ.get("STATS_USER", "Eizi0")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"

# Les dépôts affichés sur le profil, dans l'ordre du README.
REPOS = ["memhunter", "agents-md-attack-vector-research", "Wazuh-Rules", "proxui", "OpenDLM"]

BG, BORDER, TITLE, TEXT, MUTED, ACCENT = "#0a101c", "#22304a", "#5AB0FF", "#c9d6e8", "#8794ad", "#46C98B"
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Rust": "#dea584", "Go": "#00ADD8",
    "Shell": "#89e051", "PowerShell": "#5391FE", "HCL": "#844FBA", "HTML": "#e34c26", "CSS": "#563d7c",
    "Jinja": "#a52a22", "Dockerfile": "#384d54", "YAML": "#cb171e",
}
WIDTH, HEIGHT = 400, 124
DESC_CHARS, DESC_LINES = 52, 2


def fetch(repo):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{USER}/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-cards",
                 **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def wrap(text):
    lines = textwrap.wrap(text or "Aucune description.", DESC_CHARS)
    if len(lines) > DESC_LINES:
        lines = lines[:DESC_LINES]
        lines[-1] = lines[-1].rstrip(" .,;:")[: DESC_CHARS - 1] + "…"
    return lines


def card(data):
    name = escape(data["name"])
    lines = wrap(data.get("description"))
    desc = "".join(f'<text x="24" y="{62 + 18 * i}" class="d">{escape(line)}</text>' for i, line in enumerate(lines))
    lang = data.get("language")
    footer_y = HEIGHT - 20
    parts = []
    x = 24
    if lang:
        parts.append(f'<circle cx="{x + 5}" cy="{footer_y - 4}" r="5" fill="{LANG_COLORS.get(lang, "#8b949e")}"/>'
                     f'<text x="{x + 16}" y="{footer_y}" class="m">{escape(lang)}</text>')
        x += 16 + 8 * len(lang) + 16
    parts.append(f'<path transform="translate({x} {footer_y - 12})" fill="{MUTED}" d="M8 .25a.75.75 0 01.67.42l1.88 3.8 4.2.61a.75.75 0 01.41 1.28l-3.04 2.96.72 4.18a.75.75 0 01-1.09.79L8 12.3l-3.75 1.97a.75.75 0 01-1.09-.79l.72-4.18L.84 6.36a.75.75 0 01.41-1.28l4.2-.61L7.33.67A.75.75 0 018 .25z"/>'
                 f'<text x="{x + 20}" y="{footer_y}" class="m">{data.get("stargazers_count", 0)}</text>')
    x += 20 + 10 * len(str(data.get("stargazers_count", 0))) + 22
    parts.append(f'<path transform="translate({x} {footer_y - 12})" fill="{MUTED}" d="M5 3.25a1.75 1.75 0 11-2.5 1.58v6.34a1.75 1.75 0 101.5 0V9.5h4.25a2.25 2.25 0 002.25-2.25v-.42a1.75 1.75 0 10-1.5 0v.42a.75.75 0 01-.75.75H4V4.83A1.75 1.75 0 005 3.25z"/>'
                 f'<text x="{x + 20}" y="{footer_y}" class="m">{data.get("forks_count", 0)}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{name} : {escape(' '.join(lines))}">
<style>
.t{{font:600 17px 'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif;fill:{TITLE}}}
.d{{font:400 13px 'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif;fill:{TEXT}}}
.m{{font:400 12px 'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif;fill:{MUTED}}}
</style>
<rect x="0.5" y="0.5" rx="6" width="{WIDTH - 1}" height="{HEIGHT - 1}" fill="{BG}" stroke="{BORDER}"/>
<path transform="translate(24 17)" fill="{ACCENT}" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8zM5 12.25a.25.25 0 01.25-.25h3.5a.25.25 0 01.25.25v3.25a.25.25 0 01-.4.2l-1.45-1.087a.249.249 0 00-.3 0L5.4 15.7a.25.25 0 01-.4-.2z"/>
<text x="46" y="30" class="t">{name}</text>
{desc}
{''.join(parts)}
</svg>
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    failures = 0
    for repo in REPOS:
        path = os.path.join(OUT, f"card-{repo.lower()}.svg")
        try:
            svg = card(fetch(repo))
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
            # On garde l'ancienne carte plutôt que d'écraser par du vide.
            print(f"{repo}: échec ({e}), carte précédente conservée", file=sys.stderr)
            failures += 1
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"{repo}: {path}")
    return 1 if failures == len(REPOS) else 0


if __name__ == "__main__":
    sys.exit(main())
