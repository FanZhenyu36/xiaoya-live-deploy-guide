"""Check LLM credentials and model listing without starting Vidu or generating a reply."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import urllib.request
import urllib.error


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,required=True)
    a=ap.parse_args()
    conf=json.loads(a.config.read_text(encoding='utf-8-sig'))['llm']
    key_path=Path(conf['key_file'])
    if not key_path.is_absolute():
        key_path=a.config.parent/key_path
    if not key_path.is_file():
        ap.exit(1,'[ERROR] LLM key file does not exist.\n')
    key=key_path.read_text(encoding='utf-8-sig').strip()
    if not key:
        ap.exit(1,'[ERROR] LLM key file is empty.\n')
    req=urllib.request.Request(conf['base_url'].rstrip('/')+'/models',
                               headers={'Authorization':'Bearer '+key})
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            data=json.load(response)
    except urllib.error.HTTPError as exc:
        ap.exit(1,f'[ERROR] LLM /models returned HTTP {exc.code}. Verify the service, key and base URL.\n')
    ids=[str(item.get('id','')) for item in data.get('data',[]) if isinstance(item,dict)]
    chosen=conf.get('model','')
    if chosen not in ids:
        ap.exit(1,f'[ERROR] Configured model not found in listing. Available model IDs: {ids}\n')
    print(f'[OK] LLM credentials accepted; model listed: {chosen}')
    print('[INFO] This checks listing access, not chat-generation quality or inference availability.')


if __name__=='__main__':
    main()
