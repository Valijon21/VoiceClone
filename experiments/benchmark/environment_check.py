#!/usr/bin/env python3
"""
Environment Check Script for VoiceClone Benchmark.
Inspects OS, Python, CPU, GPU, CUDA, Disk space, and Git information.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_git_info():
    info = {"branch": None, "remote": None, "commit": None, "clean": None}
    try:
        # Use safe.directory config override
        branch = subprocess.check_output(
            ["git", "-c", "safe.directory=*", "branch", "--show-current"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["branch"] = branch or "master (no commit)"
    except Exception:
        info["branch"] = "master (detached or no commit)"

    try:
        remote = subprocess.check_output(
            ["git", "-c", "safe.directory=*", "remote", "get-url", "origin"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["remote"] = remote
    except Exception:
        info["remote"] = "origin not set"

    try:
        commit = subprocess.check_output(
            ["git", "-c", "safe.directory=*", "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["commit"] = commit
    except Exception:
        info["commit"] = "No commits yet"

    try:
        status = subprocess.check_output(
            ["git", "-c", "safe.directory=*", "status", "--porcelain"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["clean"] = len(status) == 0
    except Exception:
        info["clean"] = False

    return info


def get_disk_info():
    drives = {}
    for drive in ["C:", "D:"]:
        try:
            usage = shutil.disk_usage(drive + "\\")
            drives[drive] = {
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
            }
        except Exception as e:
            drives[drive] = {"error": str(e)}
    return drives


def get_gpu_info():
    gpu_info = {
        "gpu_detected": False,
        "name": None,
        "vram_total_mb": None,
        "driver_version": None,
        "cuda_version_supported": None,
    }
    try:
        smi_out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            text=True
        ).strip()
        parts = [p.strip() for p in smi_out.split(",")]
        if len(parts) >= 3:
            gpu_info["gpu_detected"] = True
            gpu_info["name"] = parts[0]
            gpu_info["vram_total_mb"] = float(parts[1])
            gpu_info["driver_version"] = parts[2]
    except Exception as e:
        gpu_info["error"] = str(e)

    # Check CUDA version via nvidia-smi banner
    try:
        smi_banner = subprocess.check_output(["nvidia-smi"], text=True)
        for line in smi_banner.splitlines():
            if "CUDA Version:" in line:
                idx = line.find("CUDA Version:")
                gpu_info["cuda_version_supported"] = line[idx:].split()[2]
                break
    except Exception:
        pass

    return gpu_info


def get_torch_info():
    info = {
        "installed": False,
        "version": None,
        "cuda_available": False,
        "torch_cuda_version": None,
        "device_name": None,
    }
    try:
        import torch
        info["installed"] = True
        info["version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        info["torch_cuda_version"] = torch.version.cuda
        if torch.cuda.is_available():
            info["device_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    except Exception as e:
        info["error"] = str(e)
    return info


def check_internet():
    import urllib.request
    endpoints = {
        "huggingface": "https://huggingface.co",
        "github": "https://github.com",
    }
    status = {}
    for name, url in endpoints.items():
        try:
            code = urllib.request.urlopen(url, timeout=5).getcode()
            status[name] = {"reachable": True, "status_code": code}
        except Exception as e:
            status[name] = {"reachable": False, "error": str(e)}
    return status


def run_env_check():
    report = {
        "os": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
        },
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "disk": get_disk_info(),
        "gpu": get_gpu_info(),
        "torch": get_torch_info(),
        "internet": check_internet(),
        "git": get_git_info(),
    }
    return report


if __name__ == "__main__":
    rep = run_env_check()
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "environment_info.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"Environment check completed. Saved to {out_path}")
    print(json.dumps(rep, indent=2))
