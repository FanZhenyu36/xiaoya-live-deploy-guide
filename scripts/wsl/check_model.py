"""Locate an existing OmniVoice snapshot; follow HF symlinks, never redownload silently."""
from __future__ import annotations
import argparse
import os
from pathlib import Path

REQUIRED = ('config.json', 'tokenizer.json', 'model.safetensors',
            'audio_tokenizer/config.json', 'audio_tokenizer/model.safetensors')


def validate_model(path: Path) -> list[str]:
    missing = []
    for name in REQUIRED:
        f = path / name
        if not f.is_file() or f.stat().st_size == 0:
            missing.append(name)
    return missing


def locate_model(explicit: str = '') -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        missing = validate_model(p)
        if missing:
            raise ValueError('Model files missing or broken symlinks: ' + ', '.join(missing))
        return p
    hub = Path(os.environ.get('HF_HUB_CACHE') or os.environ.get('HUGGINGFACE_HUB_CACHE') or
               str(Path(os.environ.get('HF_HOME', str(Path.home() / '.cache/huggingface'))) / 'hub'))
    repo = hub / 'models--k2-fsa--OmniVoice'
    candidates = []
    ref = repo / 'refs/main'
    if ref.is_file():
        candidates.append(repo / 'snapshots' / ref.read_text().strip())
    if (repo / 'snapshots').is_dir():
        candidates.extend(sorted((repo / 'snapshots').iterdir(), reverse=True))
    for p in candidates:
        if p.is_dir() and not validate_model(p):
            return p.resolve()
    raise FileNotFoundError('No complete cached OmniVoice model. Use --model PATH or run download_model.py.')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model', default=os.environ.get('OMNIVOICE_MODEL', ''))
    a = ap.parse_args()
    try:
        print(locate_model(a.model))
    except (ValueError, FileNotFoundError) as exc:
        ap.exit(1, f'[ERROR] {exc}\n')


if __name__ == '__main__':
    main()
