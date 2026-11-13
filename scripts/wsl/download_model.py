"""Download the official checkpoint only when explicitly run."""
from __future__ import annotations
import argparse


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--local-dir', help='Optional explicit directory; default is the HF cache.')
    ap.add_argument('--revision', default='c5fdb5ccb189668d56333f77ba2629f4cd7535f4')
    a = ap.parse_args()
    from huggingface_hub import snapshot_download
    from check_model import validate_model
    from pathlib import Path
    p = snapshot_download('k2-fsa/OmniVoice', revision=a.revision, local_dir=a.local_dir)
    missing = validate_model(Path(p))
    if missing:
        raise SystemExit('Downloaded snapshot incomplete: ' + ', '.join(missing))
    print('[OK] Model:', p)
    print('Set OMNIVOICE_MODEL to this directory if it is not the default cache.')


if __name__ == '__main__':
    main()
