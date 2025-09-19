import os
import asyncio
from typing import Dict, Any

from faster_whisper import WhisperModel
try:
    import ctranslate2  # type: ignore
except Exception:  # noqa: BLE001
    ctranslate2 = None  # type: ignore


def _format_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3_600_000
    remainder = total_ms % 3_600_000
    minutes = remainder // 60_000
    remainder = remainder % 60_000
    secs = remainder // 1000
    millis = remainder % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _write_srt(segments, srt_path: str):
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        for index, segment in enumerate(segments, start=1):
            start_time = _format_timestamp(segment.start)
            end_time = _format_timestamp(segment.end)
            text = (segment.text or "").strip()
            if not text:
                continue
            srt_file.write(f"{index}\n")
            srt_file.write(f"{start_time} --> {end_time}\n")
            srt_file.write(f"{text}\n\n")


def _resolve_device(device_pref: str) -> str:
    if device_pref not in ("auto", "cpu", "cuda"):
        return "cpu"
    if device_pref == "auto":
        try:
            if ctranslate2 is not None and ctranslate2.get_device_count("cuda") > 0:  # type: ignore[attr-defined]
                return "cuda"
        except Exception:  # noqa: BLE001
            pass
        return "cpu"
    return device_pref


def _transcribe_sync(video_file: str, cfg: Dict[str, Any]) -> str:
    model_size = cfg.get("model", "base")
    language = cfg.get("language", "en")
    device_pref = cfg.get("device", "auto")
    device = _resolve_device(device_pref)

    compute_type = "int8" if device == "cpu" else "float16"
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    segments, _ = model.transcribe(
        video_file,
        language=language,
        task="transcribe",
        vad_filter=True,
    )

    base, _ = os.path.splitext(video_file)
    srt_path = f"{base}.srt"
    _write_srt(segments, srt_path)
    return srt_path


async def transcribe_post(video_file: str, cfg: Dict[str, Any], logger) -> str:
    logger.info(f"📝 Starting transcription for {os.path.basename(video_file)}")
    try:
        srt_path = await asyncio.to_thread(_transcribe_sync, video_file, cfg)
        logger.info(f"✅ Transcription completed: {os.path.basename(srt_path)}")
        return srt_path
    except Exception as exc:  # noqa: BLE001
        logger.error(f"❌ Transcription failed for {os.path.basename(video_file)}: {str(exc)}")
        raise


