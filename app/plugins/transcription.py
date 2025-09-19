import os
import asyncio
from typing import Dict, Any
from datetime import timedelta

import srt
from faster_whisper import WhisperModel
try:
    import ctranslate2  # type: ignore
except Exception:  # noqa: BLE001
    ctranslate2 = None  # type: ignore


def _write_srt(segments, srt_path: str):
    subtitles = []
    index = 1
    for segment in segments:
        text = (segment.text or "").strip()
        if not text:
            continue
        start_td = timedelta(seconds=float(segment.start))
        end_td = timedelta(seconds=float(segment.end))
        subtitles.append(
            srt.Subtitle(index=index, start=start_td, end=end_td, content=text)
        )
        index += 1
    srt_text = srt.compose(subtitles)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_text)


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


