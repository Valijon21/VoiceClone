#!/usr/bin/env python3
"""
Benchmark Runner for VoiceClone Models.
Measures: RTF, latency, cold start, peak VRAM/RAM, and error rates.
Supports Anadil Uzbek TTS and OpenVoice V2.
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

# Standard benchmark test sentences from docs/MODEL_BENCHMARK.md
CORPUS = {
    "uz": [
        {"id": "UZ-01", "text": "Assalomu alaykum, Voice Clone tizimiga xush kelibsiz!"},
        {"id": "UZ-02", "text": "O‘zbekiston tog‘lari va go‘zal bog‘larida bahor nafasi sezilmoqda."},
        {"id": "UZ-03", "text": "Ma’naviyat va ma’rifat inson qalbini yuksaltiruvchi buyuk ne’matdir."},
        {"id": "UZ-04", "text": "Shahrimiz ko‘chalarida tong paytida qushlarning yoqimli sayrashi eshitiladi."},
        {"id": "UZ-05", "text": "Bugun 2026-yil 11-oktabr, havo harorati 18 daraja iliq bo‘lishi kutilmoqda."},
        {"id": "UZ-06", "text": "Umumiy summa 450 000 so‘m bo‘lib, to‘lov muvaffaqiyatli qabul qilindi."},
        {"id": "UZ-07", "text": "Shohruh, Nodira, Abdulla va G‘ayrat bugungi uchrashuvga yetib kelishdi."},
        {"id": "UZ-08", "text": "Ertaga soat to‘qqizda bo‘lib o‘tadigan anjumanga siz ham borasizmi?"},
        {"id": "UZ-09", "text": "Qoyil! Bu ovoz xuddi haqiqiy insonga o‘xshab jaranglayapti-ku!"},
        {"id": "UZ-10", "text": "Sun’iy intellekt modeli neyron tarmoqlar orqali ovoz to‘lqinlarini sintez qiladi."},
    ],
    "ru": [
        {"id": "RU-01", "text": "Здравствуйте! Добро пожаловать в систему синтеза речи Voice Clone."},
        {"id": "RU-02", "text": "Сегодня 11 октября 2026 года, температура воздуха составляет плюс 18 градусов."},
        {"id": "RU-03", "text": "Александр Сергеевич и Екатерина Ивановна подтвердили участие в конференции."},
        {"id": "RU-04", "text": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров."},
        {"id": "RU-05", "text": "Скажите, пожалуйста, удалось ли вам завершить тестирование всех модулей вовремя?"},
    ],
    "en": [
        {"id": "EN-01", "text": "Hello! Welcome to the Voice Clone AI speech synthesis platform."},
        {"id": "EN-02", "text": "Today is October 11th, 2026, and the system is operating at 99.8% uptime."},
        {"id": "EN-03", "text": "She sells seashells by the seashore, and the shells she sells are seashells."},
        {"id": "EN-04", "text": "Could you please verify whether the consent verification passed on the server?"},
        {"id": "EN-05", "text": "Incredible! The synthetic audio matches the original speaker profile seamlessly!"},
    ]
}


def run_benchmark(model_name: str, lang: str = "en", device: str = "cpu", max_samples: int = 5):
    results_dir = Path(__file__).resolve().parent / "results"
    samples_dir = Path(__file__).resolve().parent / "samples"
    results_dir.mkdir(parents=True, exist_ok=True)
    samples_dir.mkdir(parents=True, exist_ok=True)

    items = CORPUS.get(lang, [])[:max_samples]
    if not items:
        print(f"No sentences available for language: {lang}")
        return

    print(f"=== Starting Benchmark ===")
    print(f"Model: {model_name} | Language: {lang} | Device: {device} | Samples: {len(items)}")

    benchmark_records = []
    summary = {
        "model": model_name,
        "language": lang,
        "device": device,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_samples": len(items),
        "successful_samples": 0,
        "failed_samples": 0,
        "cold_start_time_sec": None,
        "avg_rtf": None,
        "min_rtf": None,
        "max_rtf": None,
        "avg_generation_time_sec": None,
        "peak_vram_mb": None,
        "records": []
    }

    # Dry-run / model loading check
    t_start = time.perf_counter()
    model_loaded = False
    load_err = None

    try:
        if model_name == "anadil":
            if lang != "uz":
                raise ValueError("Anadil Uzbek TTS is exclusively designed for Uzbek language.")
            from voxcpm.core import VoxCPM
            ref_audio = samples_dir / "uzbek_reference_1.wav"
            if not ref_audio.exists():
                raise FileNotFoundError(f"Missing reference wav: {ref_audio}")
            tts = VoxCPM.from_pretrained(
                hf_model_id="openbmb/VoxCPM2",
                load_denoiser=False,
                optimize=False,
                device=device,
            )
            model_loaded = True
        elif model_name == "openvoice":
            if lang not in ["en", "es", "fr", "zh", "jp", "kr"]:
                raise ValueError(
                    f"OpenVoice V2 native MeloTTS backbone does not support '{lang}'. Native: en, es, fr, zh, jp, kr."
                )
            sys.path.insert(0, str(Path(__file__).resolve().parent / "openvoice" / "OpenVoice"))
            from openvoice.api import ToneColorConverter
            ref_audio = samples_dir / "english_reference_0.mp3"
            ckpt = Path(__file__).resolve().parent / "openvoice" / "checkpoints_v2" / "converter"
            converter = ToneColorConverter(str(ckpt / "config.json"), device=device)
            converter.load_ckpt(str(ckpt / "checkpoint.pth"))
            model_loaded = True
        else:
            raise ValueError(f"Unknown model: {model_name}")

        summary["cold_start_time_sec"] = round(time.perf_counter() - t_start, 3)
    except Exception as e:
        load_err = str(e)
        summary["failed_samples"] = len(items)
        summary["error"] = load_err
        print(f"Model Loading Failed: {load_err}")

    # Process items if model loaded successfully
    if model_loaded:
        import soundfile as sf
        import torch

        rtf_list = []
        gen_time_list = []

        for idx, item in enumerate(items):
            out_file = samples_dir / f"{model_name}_{lang}_{item['id']}.wav"
            record = {
                "id": item["id"],
                "text": item["text"],
                "status": "PENDING",
                "generation_time_sec": None,
                "audio_duration_sec": None,
                "rtf": None,
                "output_path": str(out_file),
                "error": None
            }

            try:
                t0 = time.perf_counter()
                if model_name == "anadil":
                    audio = tts.generate(
                        text=item["text"],
                        reference_wav_path=str(ref_audio),
                        cfg_value=2.0,
                        inference_timesteps=10,
                        normalize=True,
                    )
                    gen_time = time.perf_counter() - t0
                    sf.write(str(out_file), audio, tts.tts_model.sample_rate)
                elif model_name == "openvoice":
                    # Perform synthesis
                    from melo.api import TTS
                    melo_model = TTS(language="EN", device=device)
                    speaker_ids = melo_model.hps.data.spk2id
                    spk_id = speaker_ids["EN-Default"]
                    tmp_wav = samples_dir / "tmp_melo.wav"
                    melo_model.tts_to_file(item["text"], spk_id, str(tmp_wav), speed=1.0)
                    gen_time = time.perf_counter() - t0

                    # Tone conversion
                    target_se, _ = se_extractor.get_se(str(ref_audio), converter, vad=True)
                    source_se = torch.load(
                        str(Path(__file__).resolve().parent / "openvoice" / "checkpoints_v2" / "base_speakers" / "ses" / "en-default.pth"),
                        map_location=device
                    )
                    converter.convert(
                        audio_src_path=str(tmp_wav),
                        src_se=source_se,
                        tgt_se=target_se,
                        output_path=str(out_file)
                    )
                    if tmp_wav.exists():
                        tmp_wav.unlink()

                audio_info = sf.info(str(out_file))
                duration = audio_info.duration
                rtf = gen_time / duration if duration > 0 else 0

                record["status"] = "SUCCESS"
                record["generation_time_sec"] = round(gen_time, 3)
                record["audio_duration_sec"] = round(duration, 3)
                record["rtf"] = round(rtf, 3)

                rtf_list.append(rtf)
                gen_time_list.append(gen_time)
                summary["successful_samples"] += 1
                print(f"[{item['id']}] SUCCESS — RTF: {record['rtf']} | Gen: {record['generation_time_sec']}s | Dur: {record['audio_duration_sec']}s")

            except Exception as e:
                record["status"] = "FAILED"
                record["error"] = f"{type(e).__name__}: {str(e)}"
                summary["failed_samples"] += 1
                print(f"[{item['id']}] FAILED — {record['error']}")

            benchmark_records.append(record)

        if rtf_list:
            summary["avg_rtf"] = round(sum(rtf_list) / len(rtf_list), 3)
            summary["min_rtf"] = round(min(rtf_list), 3)
            summary["max_rtf"] = round(max(rtf_list), 3)
            summary["avg_generation_time_sec"] = round(sum(gen_time_list) / len(gen_time_list), 3)

        if device == "cuda" and torch.cuda.is_available():
            summary["peak_vram_mb"] = round(torch.cuda.max_memory_allocated() / (1024**2), 2)

    summary["records"] = benchmark_records

    # Save summary JSON
    summary_file = results_dir / f"benchmark_{model_name}_{lang}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Save combined summary
    master_summary_file = results_dir / "summary.json"
    master_data = {}
    if master_summary_file.exists():
        try:
            with open(master_summary_file, "r", encoding="utf-8") as f:
                master_data = json.load(f)
        except Exception:
            pass
    master_data[f"{model_name}_{lang}"] = summary
    with open(master_summary_file, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2)

    print(f"\nBenchmark completed. Summary saved to: {summary_file}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Voice Model Benchmark Runner")
    parser.add_argument("--model", choices=["anadil", "openvoice"], required=True)
    parser.add_argument("--lang", choices=["uz", "ru", "en"], required=True)
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cpu")
    parser.add_argument("--samples", type=int, default=5)
    args = parser.parse_args()

    run_benchmark(model_name=args.model, lang=args.lang, device=args.device, max_samples=args.samples)


if __name__ == "__main__":
    main()
