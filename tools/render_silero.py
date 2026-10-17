"""Render a Russian lecture with a previously downloaded Silero model."""

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path


def main() -> None:
    """Validate spoken text, synthesize paragraphs, and publish an MP3 atomically."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--voice", choices=["aidar", "baya", "kseniya", "eugene", "xenia"],
        default="xenia",
    )
    args = parser.parse_args()
    text = args.script.read_text(encoding="utf-8").strip()
    if not text or re.search(r"[A-Za-z0-9]", text):
        parser.error("Use nonempty Russian spoken text; spell out Latin names and numbers.")
    paragraphs = [" ".join(p.split()) for p in text.split("\n\n") if p.strip()]
    if any(len(p) > 900 for p in paragraphs):
        parser.error("Split paragraphs longer than 900 characters before rendering.")
    if not args.model.is_file():
        parser.error("Download the verified Silero model first; this renderer is offline.")

    import numpy as np
    import soundfile as sf
    import torch

    started = time.monotonic()
    torch.set_num_threads(4)
    model = torch.package.PackageImporter(str(args.model)).load_pickle("tts_models", "model")
    sample_rate = 48000
    parts = []
    with torch.inference_mode():
        for paragraph in paragraphs:
            audio = model.apply_tts(
                text=paragraph, speaker=args.voice, sample_rate=sample_rate,
                put_accent=True, put_yo=True, put_stress_homo=True, put_yo_homo=True,
            ).cpu().numpy()
            if not audio.size or not np.isfinite(audio).all():
                raise ValueError("Model returned empty or nonfinite audio.")
            parts.extend([audio, np.zeros(int(sample_rate * 0.25), dtype=np.float32)])
    waveform = np.concatenate(parts)
    duration = waveform.size / sample_rate
    if not 0 < duration <= 300:
        raise ValueError(f"Episode duration {duration:.2f}s exceeds the five-minute limit.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="silero-", dir=args.output.parent) as directory:
        directory = Path(directory)
        wav = directory / "lecture.wav"
        mp3 = directory / "lecture.mp3"
        sf.write(wav, waveform, sample_rate, subtype="PCM_16")
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(wav),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100",
            "-b:a", "128k", str(mp3),
        ], check=True)
        mp3.replace(args.output)
    print(json.dumps({"voice": args.voice, "paragraphs": len(paragraphs),
                      "duration_seconds": round(duration, 3),
                      "render_seconds": round(time.monotonic() - started, 3)}))


if __name__ == "__main__":
    main()
