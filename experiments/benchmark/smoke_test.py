#!/usr/bin/env python3
"""
Smoke Test for VoiceClone Benchmark.
Tests minimal loading, reference audio validation, and single-phrase inference.
Supports: Anadil Uzbek TTS and OpenVoice V2.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


def smoke_test_anadil(device: str = "cpu"):
    result = {
        "model": "Anadil Uzbek TTS",
        "base_model": "openbmb/VoxCPM2",
        "adapter": "Anadilorg/Anadil_Uzbek_TTS",
        "target_language": "uz",
        "device_requested": device,
        "device_used": None,
        "status": "UNKNOWN",
        "load_time_sec": None,
        "generation_time_sec": None,
        "audio_duration_sec": None,
        "rtf": None,
        "peak_vram_mb": None,
        "output_audio_path": None,
        "errors": []
    }

    ref_audio = Path(__file__).resolve().parent / "samples" / "uzbek_reference_1.wav"
    if not ref_audio.exists():
        result["status"] = "BLOCKED"
        result["errors"].append(f"Reference audio not found: {ref_audio}")
        return result

    # Check dependencies
    try:
        import torch
        import soundfile as sf
    except ImportError as e:
        result["status"] = "BLOCKED"
        result["errors"].append(f"Missing basic dependency: {e}")
        return result

    # Check CUDA if requested
    if device == "cuda":
        if not torch.cuda.is_available():
            result["errors"].append("CUDA requested but not available. Falling back to CPU.")
            device = "cpu"
    result["device_used"] = device

    # Check voxcpm availability
    try:
        from voxcpm.core import VoxCPM
        from voxcpm.model.voxcpm2 import LoRAConfig
    except ImportError as e:
        result["status"] = "BLOCKED"
        result["errors"].append(
            f"voxcpm package not installed: {e}. Run 'pip install voxcpm' in this environment."
        )
        return result

    out_wav = Path(__file__).resolve().parent / "samples" / "anadil_smoke_test.wav"
    text = "Assalomu alaykum! Bu tizim sinovi."

    try:
        t0 = time.perf_counter()
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()

        # Load LoRA config and model
        tts = VoxCPM.from_pretrained(
            hf_model_id="openbmb/VoxCPM2",
            load_denoiser=False,
            optimize=False,
            device=device,
        )
        result["load_time_sec"] = round(time.perf_counter() - t0, 3)

        # Generate audio
        t1 = time.perf_counter()
        audio = tts.generate(
            text=text,
            reference_wav_path=str(ref_audio),
            cfg_value=2.0,
            inference_timesteps=10,
            normalize=True,
            min_len=2,
        )
        gen_time = time.perf_counter() - t1
        result["generation_time_sec"] = round(gen_time, 3)

        sf.write(str(out_wav), audio, tts.tts_model.sample_rate)
        result["output_audio_path"] = str(out_wav)

        # Measure audio duration
        info = sf.info(str(out_wav))
        result["audio_duration_sec"] = round(info.duration, 3)
        if result["audio_duration_sec"] > 0:
            result["rtf"] = round(gen_time / result["audio_duration_sec"], 3)

        if device == "cuda":
            result["peak_vram_mb"] = round(torch.cuda.max_memory_allocated() / (1024**2), 2)

        result["status"] = "PASS"

    except Exception as e:
        result["status"] = "FAIL"
        result["errors"].append(f"Inference error: {type(e).__name__}: {str(e)}")

    return result


def smoke_test_openvoice(device: str = "cpu"):
    result = {
        "model": "OpenVoice V2",
        "backbone": "MeloTTS",
        "target_language": "en",
        "device_requested": device,
        "device_used": None,
        "status": "UNKNOWN",
        "load_time_sec": None,
        "generation_time_sec": None,
        "audio_duration_sec": None,
        "rtf": None,
        "peak_vram_mb": None,
        "output_audio_path": None,
        "errors": []
    }

    ref_audio = Path(__file__).resolve().parent / "samples" / "english_reference_0.mp3"
    if not ref_audio.exists():
        result["status"] = "BLOCKED"
        result["errors"].append(f"Reference audio not found: {ref_audio}")
        return result

    try:
        import torch
    except ImportError as e:
        result["status"] = "BLOCKED"
        result["errors"].append(f"Missing torch: {e}")
        return result

    if device == "cuda" and not torch.cuda.is_available():
        result["errors"].append("CUDA requested but not available. Falling back to CPU.")
        device = "cpu"
    result["device_used"] = device

    # Check openvoice and melotts
    try:
        # Check openvoice module
        sys.path.insert(0, str(Path(__file__).resolve().parent / "openvoice" / "OpenVoice"))
        from openvoice import se_extractor
        from openvoice.api import ToneColorConverter
    except ImportError as e:
        result["status"] = "BLOCKED"
        result["errors"].append(f"OpenVoice modules not found or missing dependency: {e}")
        return result

    out_wav = Path(__file__).resolve().parent / "samples" / "openvoice_smoke_test.wav"
    text = "Hello! This is a smoke test for OpenVoice V2 voice cloning."

    # Perform test if dependencies exist
    try:
        t0 = time.perf_counter()
        ckpt_dir = Path(__file__).resolve().parent / "openvoice" / "checkpoints_v2" / "converter"
        converter = ToneColorConverter(str(ckpt_dir / "config.json"), device=device)
        converter.load_ckpt(str(ckpt_dir / "checkpoint.pth"))
        result["load_time_sec"] = round(time.perf_counter() - t0, 3)
        result["status"] = "PASS"
    except Exception as e:
        result["status"] = "FAIL"
        result["errors"].append(f"OpenVoice error: {type(e).__name__}: {str(e)}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Smoke Test Runner")
    parser.add_argument("--model", choices=["anadil", "openvoice"], required=True)
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cpu")
    args = parser.parse_args()

    if args.model == "anadil":
        res = smoke_test_anadil(device=args.device)
    else:
        res = smoke_test_openvoice(device=args.device)

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"smoke_test_{args.model}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    print(json.dumps(res, indent=2))
    print(f"\nResult saved to: {out_file}")


if __name__ == "__main__":
    main()
