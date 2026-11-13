"""OmniVoice demo with optional FlashInfer and CUDA Graph; no automatic cloud calls."""
from __future__ import annotations
import argparse
import os
from check_model import locate_model


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model', default=os.environ.get('OMNIVOICE_MODEL', ''))
    ap.add_argument('--port', type=int, default=9877)
    ap.add_argument('--host', default='0.0.0.0', help='WSL-local service; keep Windows firewall private.')
    ap.add_argument('--no-flashinfer', action='store_true')
    ap.add_argument('--cuda-graph', action='store_true')
    ap.add_argument('--graph-buckets', default='5,10')
    a = ap.parse_args()
    if a.no_flashinfer and a.cuda_graph:
        ap.error('--cuda-graph requires FlashInfer')
    import torch
    from omnivoice import OmniVoice
    from omnivoice.cli.demo import build_demo
    if not torch.cuda.is_available():
        raise SystemExit('CUDA unavailable. Run diagnose.py and fix the driver / PyTorch environment.')
    path = str(locate_model(a.model))
    print(f'[INFO] Model: {path}', flush=True)
    model = OmniVoice.from_pretrained(path, device_map='cuda', dtype=torch.float16, load_asr=False)
    if not a.no_flashinfer:
        from omnivoice.models.omnivoice_flashinfer import apply_flashinfer
        buckets = [int(x) for x in a.graph_buckets.split(',') if x.strip()]
        apply_flashinfer(model, enable_cuda_graph=a.cuda_graph,
                        cuda_graph_buckets=buckets if a.cuda_graph else None)
        print(f'[OK] FlashInfer applied. CUDA Graph={a.cuda_graph}', flush=True)
    else:
        print('[INFO] Standard PyTorch mode, no FlashInfer.', flush=True)
    demo = build_demo(model, path)
    demo.queue().launch(server_name=a.host, server_port=a.port)


if __name__ == '__main__':
    main()
