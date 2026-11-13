"""Create a private runtime config without modifying an existing installation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def create_config(stage_root: Path, runtime_root: Path) -> bool:
    target = stage_root / 'config.json'
    if target.exists():
        print('[SKIP] Existing config.json preserved.')
        return False
    template = Path(__file__).resolve().parents[1] / 'config' / 'stage.example.json'
    conf = json.loads(template.read_text(encoding='utf-8'))
    for name in ('voices', 'songs', 'audio', 'secrets', 'logs'):
        (runtime_root / name).mkdir(parents=True, exist_ok=True)
    conf['llm']['key_file'] = str((runtime_root / 'secrets' / 'deepseek.key').resolve())
    conf['tts']['voices_dir'] = str((runtime_root / 'voices').resolve())
    conf['tts']['files_dir'] = str((runtime_root / 'audio').resolve())
    conf['tts']['song_dirs'] = [str((runtime_root / 'songs').resolve())]
    stage_root.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(conf, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('[OK] Private config created. Fill your Vidu Key, avatar ID and LLM key locally.')
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage-root', type=Path, required=True)
    ap.add_argument('--runtime-root', type=Path, required=True)
    args = ap.parse_args()
    create_config(args.stage_root.resolve(), args.runtime_root.resolve())


if __name__ == '__main__':
    main()
