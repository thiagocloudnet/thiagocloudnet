"""Gera SVGs estáticos exclusivamente com dados públicos do GitHub."""
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER = 'thiagocloudnet'

def api(route, *args):
    result = subprocess.run(['gh', 'api', route, *args], capture_output=True, text=True, encoding='utf-8', check=True)
    return json.loads(result.stdout)

def svg(title, lines):
    height = 105 + len(lines) * 36
    rows = ''.join(f'<text x="28" y="{91 + i * 36}" fill="#EAF2FF" font-size="18">{escape(line)}</text>' for i, line in enumerate(lines))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {height}" role="img"><title>{escape(title)}</title><rect width="760" height="{height}" rx="18" fill="#0B1220"/><g font-family="Arial, sans-serif"><text x="28" y="42" fill="#19C786" font-size="24">{escape(title)}</text>{rows}</g></svg>\n'

def main():
    repos = []
    page = 1
    while True:
        batch = api(f'users/{USER}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    repos = [r for r in repos if not r['fork'] and not r['private']]
    languages = Counter()
    for repo in repos:
        languages.update(api(f'repos/{USER}/{repo["name"]}/languages'))
    query = 'query { user(login:"thiagocloudnet") { contributionsCollection { startedAt endedAt contributionCalendar { totalContributions } totalCommitContributions totalIssueContributions totalPullRequestContributions } } }'
    collection = api('graphql', '-f', f'query={query}')['data']['user']['contributionsCollection']
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    stats = [f'{len(repos)} repositórios públicos próprios · {sum(r["stargazers_count"] for r in repos)} estrelas',
             f'{collection["contributionCalendar"]["totalContributions"]} contribuições · {collection["totalCommitContributions"]} commits',
             f'{collection["totalPullRequestContributions"]} pull requests · {collection["totalIssueContributions"]} issues',
             f'Janela: {collection["startedAt"][:10]} a {collection["endedAt"][:10]}', f'Coleta: {date}']
    total = sum(languages.values())
    lines = [f'{name}: {count / total:.1%} · {count:,} bytes' for name, count in languages.most_common()] if total else ['Sem bytes de linguagens disponíveis.']
    outputs = {'stats.svg': svg('Atividade pública · ThiagoCloudNet', stats), 'linguagens.svg': svg('Linguagens · bytes de código público', lines + [f'Coleta: {date}'])}
    # Toda coleta termina antes de substituir os gráficos; falhas de API preservam o cache.
    for name, content in outputs.items():
        path = ROOT / 'assets' / name
        temp = path.with_suffix('.tmp')
        temp.write_text(content, encoding='utf-8')
        os.replace(temp, path)

if __name__ == '__main__':
    main()
