"""Reject credential-like values and private runtime files before publication."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

PATTERNS = [
    re.compile(r'vda_[A-Za-z0-9_\-]{30,}'),
    re.compile(r'gh[pousr]_[A-Za-z0-9]{24,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{30,}'),
    re.compile(r'(?i)(?:Bearer|Token)\s+[A-Za-z0-9_\-]{35,}'),
    re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
    re.compile(r'(?i)C:[/\\]Users[/\\]Administrator[/\\]'),
]
FORBIDDEN_SUFFIXES = {'.key','.exe','.wav','.mp3','.mp4','.safetensors','.bin','.pth','.pt','.jit'}
FORBIDDEN_NAMES = {'settings.local.json','.credentials.yaml','.credentials.yml','config.json','config.json.bak','.env'}


def scan(root: Path) -> list[str]:
    issues = []
    for p in root.rglob('*'):
        if '.git' in p.relative_to(root).parts or '__pycache__' in p.parts or not p.is_file():
            continue
        name = p.relative_to(root).as_posix()
        if p.suffix.lower() in FORBIDDEN_SUFFIXES or p.name in FORBIDDEN_NAMES:
            issues.append(f'{name}: private/runtime file type')
            continue
        try:
            text = p.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:
            issues.append(f'{name}: unexpected binary file')
            continue
        for index, pattern in enumerate(PATTERNS):
            if pattern.search(text):
                issues.append(f'{name}: credential/private-path rule {index+1}')
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    a = ap.parse_args()
    issues = scan(a.root.resolve())
    if issues:
        print('\n'.join(issues))
        raise SystemExit(1)
    print('[OK] No credential-like values, private runtime files, or bundled models/media found.')


if __name__ == '__main__':
    main()
