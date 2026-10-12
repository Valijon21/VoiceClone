"""Hardware Detection and Environment Profiling Module (VC-083)."""

import logging
from typing import Any

logger = logging.getLogger("voiceclone.inference.hardware")


def detect_hardware_capabilities() -> dict[str, Any]:
    """Inspect system accelerators (CUDA GPU vs CPU fallback) and available VRAM."""
    capabilities: dict[str, Any] = {
        "accelerator": "cpu",
        "device_name": "CPU Fallback",
        "cuda_available": False,
        "cuda_version": None,
        "vram_total_mb": 0,
        "vram_recommended_mb": 4096,
        "sufficient_vram": False,
        "recommended_device": "cpu",
        "status": "OPERATIONAL",
        "warnings": [],
    }

    try:
        import torch

        if torch.cuda.is_available():
            capabilities["cuda_available"] = True
            capabilities["cuda_version"] = torch.version.cuda
            props = torch.cuda.get_device_properties(0)
            capabilities["device_name"] = props.name
            vram_mb = int(props.total_memory / (1024 * 1024))
            capabilities["vram_total_mb"] = vram_mb

            if vram_mb >= capabilities["vram_recommended_mb"]:
                capabilities["accelerator"] = "cuda"
                capabilities["recommended_device"] = "cuda:0"
                capabilities["sufficient_vram"] = True
            else:
                capabilities["accelerator"] = "cuda_low_vram"
                capabilities["recommended_device"] = "cuda:0"
                capabilities["sufficient_vram"] = False
                capabilities["warnings"].append(
                    f"VRAM ({vram_mb} MB) is below recommended 4096 MB. Concurrency must be locked to 1."
                )
        else:
            capabilities["warnings"].append(
                "NVIDIA CUDA accelerator not available. Synthesis will run on CPU with higher latency."
            )
    except Exception as exc:
        capabilities["warnings"].append(f"Could not query PyTorch hardware properties: {exc}")

    return capabilities
