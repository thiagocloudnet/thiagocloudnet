"""Valida recursos locais, SVGs e opcionalmente URLs externas do README."""
import argparse
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--online', action='store_true')
    args = parser.parse_args()
    failures = []
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    links = set(re.findall(r'\]\(([^)]+)\)|src="([^"]+)"', readme))
    for pair in sorted(links):
        link = next(part for part in pair if part)
        if link.startswith('https://'):
            if args.online:
                try:
                    request = urllib.request.Request(link, headers={'User-Agent': 'ThiagoCloudNet-profile-validation'})
                    with urllib.request.urlopen(request, timeout=30) as response:
                        print(response.status, link)
                except Exception as error:
                    failures.append(f'{link}: {error}')
        elif not (ROOT / link.split('#')[0]).is_file():
            failures.append(f'Recurso ausente: {link}')
    for path in (ROOT / 'assets').glob('*.svg'):
        tree = ET.parse(path)
        for node in tree.iter():
            if node.tag.split('}')[-1] in {'script', 'foreignObject', 'image'}:
                failures.append(f'Elemento ativo/externo em {path.name}')
            if any(key.startswith('on') or key.split('}')[-1] == 'href' for key in node.attrib):
                failures.append(f'Atributo ativo/externo em {path.name}')
        if not tree.getroot().findall('{http://www.w3.org/2000/svg}title'):
            failures.append(f'Título acessível ausente: {path.name}')
    if failures:
        raise SystemExit('\n'.join(failures))
    print('OK: recursos, links solicitados e SVGs válidos.')

if __name__ == '__main__':
    main()
