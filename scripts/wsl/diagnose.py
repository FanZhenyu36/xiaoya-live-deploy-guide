"""Read-only GPU, dependency and accelerator diagnostic. No model is loaded."""
import importlib.metadata as md
import inspect
import shutil
import subprocess


def main():
    import torch
    import omnivoice
    print('OmniVoice source:', omnivoice.__file__)
    for name in ('torch','torchaudio','omnivoice','flashinfer-python','flashinfer-jit-cache','nvidia-cuda-nvcc'):
        try:
            print(name, md.version(name))
        except md.PackageNotFoundError:
            print(name, 'NOT INSTALLED')
    print('PyTorch CUDA:', torch.version.cuda, 'Available:', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('GPU:', torch.cuda.get_device_name(0), 'Capability:', torch.cuda.get_device_capability(0))
        free, total = torch.cuda.mem_get_info()
        print('Free / total VRAM GiB:', round(free/2**30,2), '/', round(total/2**30,2))
    try:
        from omnivoice.models.omnivoice_flashinfer import apply_flashinfer
        print('Accelerator entry:', inspect.signature(apply_flashinfer))
    except ImportError as exc:
        print('Accelerator import failed:', type(exc).__name__, str(exc))
    nvcc = shutil.which('nvcc')
    print('nvcc:', nvcc or 'NOT FOUND')
    if nvcc:
        subprocess.run([nvcc,'--version'],check=False)


if __name__ == '__main__':
    main()
