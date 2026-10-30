#!/usr/bin/env python3
"""Génère assets/stats.svg depuis l'API GraphQL de GitHub (sans service tiers).

Remplace github-readme-stats.vercel.app, dont l'instance publique est
suspendue (DEPLOYMENT_PAUSED). Même thème graphite/bleu que le reste du
profil. Les données sont celles visibles avec le jeton fourni : dépôts
publics et contributions de l'année écoulée.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from html import escape

USER = os.environ.get("STATS_USER", "Eizi0")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/stats.svg"

QUERY = """
query($login: String!, $from: DateTime!) {
  user(login: $login) {
    name
    contributionsCollection(from: $from) {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
    }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { stargazerCount }
    }
  }
}
"""


def fetch():
    if not TOKEN:
        sys.exit("GH_TOKEN manquant")
    since = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = json.dumps({"query": QUERY, "variables": {"login": USER, "from": since}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data or not data.get("data", {}).get("user"):
        sys.exit(f"Réponse GraphQL invalide : {data}")
    return data["data"]["user"]


def main():
    u = fetch()
    c = u["contributionsCollection"]
    stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
    rows = [
        ("Étoiles reçues", stars),
        ("Commits (12 derniers mois)", c["totalCommitContributions"] + c["restrictedContributionsCount"]),
        ("Pull requests", u["pullRequests"]["totalCount"]),
        ("Issues", u["issues"]["totalCount"]),
        ("Dépôts publics", u["repositories"]["totalCount"]),
    ]
    name = escape(u.get("name") or USER)
    lines = []
    for i, (label, value) in enumerate(rows):
        y = 70 + i * 25
        lines.append(
            f'<g transform="translate(25,{y})">'
            f'<text class="stat" x="0" y="0">{escape(label)} :</text>'
            f'<text class="stat bold" x="230" y="0">{value}</text></g>'
        )
    svg = f"""<svg width="467" height="195" viewBox="0 0 467 195" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d">
  <title id="t">Statistiques GitHub de {name}</title>
  <desc id="d">{escape(', '.join(f'{l} : {v}' for l, v in rows))}</desc>
  <style>
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #5AB0FF; }}
    .stat {{ font: 600 14px 'Segoe UI', Ubuntu, "Helvetica Neue", Sans-Serif; fill: #c9d6e8; }}
    .bold {{ font-weight: 700; }}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" width="466" height="194" fill="#0a101c" stroke="#22304a"/>
  <text class="header" x="25" y="35">Statistiques GitHub de {name}</text>
  {''.join(lines)}
</svg>
"""
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUT} écrit : {rows}")


main()
