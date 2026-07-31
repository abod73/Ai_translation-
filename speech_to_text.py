"""
AI Turkish Video Translator Bot - Speech to Text Module
Uses Faster Whisper Large V3 for Turkish speech recognition with VAD.
"""

import os
import asyncio
import time
from typing import Optional
from dataclasses import dataclass, field

from config import config
from logger import get_logger

log = get_logger("speech_to_text")


@dataclass
class SpeechSegment:
    """A single segment of transcribed speech."""
    id: int
    start: float
    end: float
    text: str
    words: list[dict] = field(default_factory=list)
    avg_logprob: float = 0.0
    confidence: float = 0.0

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start": self.start,
            "end": self.end,
            "text": self.text.strip(),
            "confidence": self.confidence,
        }


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    segments: list[SpeechSegment]
    language: str
    language_probability: float
    duration: float
    processing_time: float
    text: str = ""

    @property
    def total_segments(self) -> int:
        return len(self.segments)


class SpeechToText:
    """Faster Whisper speech recognition engine."""

    def __init__(self):
        self._model = None
        self._model_loaded = False
        self.device = None
        self.compute_type = None

    def _determine_device(self):
        """Determine the best device and compute type."""
        self.device = config.get_device(config.WHISPER_DEVICE)
        self.compute_type = config.get_whisper_compute_type(self.device)
        log.info(f"Whisper device: {self.device}, compute_type: {self.compute_type}")

    async def load_model(self):
        """Load the Faster Whisper model."""
        if self._model_loaded:
            return

        self._determine_device()
        log.info(f"Loading Faster Whisper model: {config.WHISPER_MODEL}")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model_sync)
        self._model_loaded = True
        log.info("Faster Whisper model loaded successfully")

    def _load_model_sync(self):
        """Synchronous model loading."""
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            config.WHISPER_MODEL,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=os.cpu_count() or 4,
            num_workers=1,
        )

    async def transcribe(
        self,
        audio_path: str,
        language: str = None,
        task: str = "transcribe"
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text with timestamps.

        Args:
            audio_path: Path to the audio/video file.
            language: Source language code (default: from config).
            task: 'transcribe' or 'translate'.

        Returns:
            TranscriptionResult with segments and metadata.
        """
        if not self._model_loaded:
            await self.load_model()

        language = language or config.SOURCE_LANGUAGE
        log.info(f"Starting transcription: {audio_path} (lang: {language})")

        start_time = time.time()
        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio_path,
            language,
            task
        )

        processing_time = time.time() - start_time
        log.info(
            f"Transcription complete: {result.total_segments} segments "
            f"in {processing_time:.1f}s"
        )
        return result

    def _transcribe_sync(
        self,
        audio_path: str,
        language: str,
        task: str
    ) -> TranscriptionResult:
        """Synchronous transcription for executor."""
        segments_gen, info = self._model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=config.WHISPER_BEAM_SIZE,
            vad_filter=config.WHISPER_VAD_FILTER,
            vad_parameters={
                "min_silence_duration_ms": config.WHISPER_VAD_MIN_SILENCE_MS,
                "min_speech_duration_ms": config.WHISPER_VAD_MIN_SPEECH_MS,
                "threshold": 0.5,
                "neg_threshold": 0.15,
                "speech_pad_ms": 200,
            },
            word_timestamps=config.WHISPER_WORD_TIMESTAMPS,
            condition_on_previous_text=True,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
        )

        segments = []
        full_text_parts = []

        for i, segment in enumerate(segments_gen):
            words = []
            if segment.words:
                words = [
                    {
                        "start": w.start,
                        "end": w.end,
                        "word": w.word.strip(),
                        "probability": w.probability,
                    }
                    for w in segment.words
                ]

            seg = SpeechSegment(
                id=i,
                start=round(segment.start, 3),
                end=round(segment.end, 3),
                text=segment.text.strip(),
                words=words,
                avg_logprob=segment.avg_logprob,
                confidence=max(0, min(1, 1 + segment.avg_logprob)),
            )
            segments.append(seg)
            full_text_parts.append(seg.text)

        full_text = " ".join(full_text_parts)

        return TranscriptionResult(
            segments=segments,
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
            processing_time=0,  # Will be set by caller
            text=full_text,
        )

    async def extract_audio(
        self,
        video_path: str,
        output_path: str = None
    ) -> str:
        """
        Extract audio from video file using FFmpeg.

        Args:
            video_path: Path to the video file.
            output_path: Optional output path for audio.

        Returns:
            Path to the extracted audio file.
        """
        from utils import run_command

        if not output_path:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_audio.wav"

        cmd = [
            config.FFMPEG_PATH,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_path
        ]

        log.info(f"Extracting audio: {video_path} -> {output_path}")
        returncode, stdout, stderr = await run_command(cmd, timeout=600)

        if returncode != 0:
            log.error(f"FFmpeg audio extraction failed: {stderr}")
            raise RuntimeError(f"Audio extraction failed: {stderr[:200]}")

        log.info(f"Audio extracted: {output_path}")
        return output_path

    async def transcribe_video(
        self,
        video_path: str,
        language: str = None
    ) -> TranscriptionResult:
        """
        Full pipeline: extract audio from video and transcribe.

        Args:
            video_path: Path to video file.
            language: Source language code.

        Returns:
            TranscriptionResult.
        """
        # Extract audio first
        audio_path = await self.extract_audio(video_path)

        try:
            # Transcribe
            result = await self.transcribe(audio_path, language)
            return result
        finally:
            # Cleanup audio file
            if config.DELETE_TEMP_FILES and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass

    def unload_model(self):
        """Unload the model to free memory."""
        if self._model:
            del self._model
            self._model = None
            self._model_loaded = False
            log.info("Whisper model unloaded")

            # Try to free GPU memory
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass


# Global STT instance
stt = SpeechToText()
