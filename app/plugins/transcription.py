import os
import asyncio
from typing import Dict, Any

try:
    import torch  # type: ignore
except Exception:  # noqa: BLE001
    torch = None  # type: ignore


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
            if torch is not None and hasattr(torch, "cuda") and torch.cuda.is_available():  # type: ignore[attr-defined]
                return "cuda"
        except Exception:  # noqa: BLE001
            pass
        return "cpu"
    return device_pref


def _build_whisper_cmd(video_file: str, cfg: Dict[str, Any]) -> list[str]:
    model_size = cfg.get("model", "base")
    language = cfg.get("language", "en")
    device = _resolve_device(cfg.get("device", "auto"))

    output_dir = os.path.dirname(video_file) or "."
    cmd = [
        "whisper",
        "--model",
        model_size,
        "--language",
        language,
        "--output_format",
        "srt",
        "--device",
        device,
        "--output_dir",
        output_dir,
        video_file,
    ]
    return cmd


async def transcribe_post(video_file: str, cfg: Dict[str, Any], logger) -> str:
    device = _resolve_device(cfg.get("device", "auto"))
    model_size = cfg.get("model", "base")
    logger.info(
        f"📝 Starting transcription for {os.path.basename(video_file)} (model={model_size}, device={device})"
    )
    cmd = _build_whisper_cmd(video_file, cfg)
    try:
        proc = await asyncio.create_subprocess_exec(*cmd)
        rc = await proc.wait()
        base, _ = os.path.splitext(video_file)
        srt_path = f"{base}.srt"
        if rc == 0 and os.path.exists(srt_path):
            logger.info(f"✅ Transcription completed: {os.path.basename(srt_path)}")
            return srt_path
        raise RuntimeError(f"whisper exited with code {rc}")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"❌ Transcription failed for {os.path.basename(video_file)}: {str(exc)}")
        raise


