"""Preview local TTS without creating a Vidu live. Requires an already running stage."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import urllib.request
import wave


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', default='http://127.0.0.1:8795')
    ap.add_argument('--text', default='你好，这是一段语音测试。')
    ap.add_argument('--out', type=Path, default=Path('tts-preview.wav'))
    a = ap.parse_args()
    if a.out.exists():
        ap.error('Output exists; choose another --out path.')
    body = json.dumps({'text':a.text}).encode('utf-8')
    req = urllib.request.Request(a.base.rstrip('/')+'/api/tts/preview',data=body,
                                 headers={'Content-Type':'application/json'})
    # Local traffic must not accidentally pass through a cloud proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req,timeout=180) as r:
            data = r.read()
    except urllib.error.HTTPError as exc:
        print(f'HTTP {exc.code}:',exc.read().decode('utf-8',errors='replace')[:500])
        raise SystemExit(1)
    a.out.write_bytes(data)
    with wave.open(str(a.out),'rb') as w:
        seconds=w.getnframes()/w.getframerate()
        print(f'[OK] {a.out.resolve()} : {seconds:.2f}s, {w.getframerate()}Hz, {w.getnchannels()}ch')


if __name__ == '__main__':
    main()
