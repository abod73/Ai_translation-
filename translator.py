"""
AI Turkish Video Translator Bot - Translator Module
Multi-stage translation: NLLB for initial translation + optional LLM refinement.
Includes names dictionary protection.
"""

import os
import re
import json
import time
import asyncio
from typing import Optional
from dataclasses import dataclass

from config import config
from logger import get_logger
from utils import load_json_file, chunk_list

log = get_logger("translator")


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    model_used: str
    llm_refined: bool = False
    processing_time: float = 0.0


class NamesDictionary:
    """Manages character names to prevent translation."""

    def __init__(self, dict_path: str = None):
        self.dict_path = dict_path or config.NAMES_DICT_PATH
        self.names: dict[str, str] = {}
        self.reverse_names: dict[str, str] = {}
        self._placeholders: dict[str, str] = {}
        self._reverse_placeholders: dict[str, str] = {}
        self.load()

    def load(self):
        """Load names from JSON file."""
        data = load_json_file(self.dict_path)
        if data:
            self.names = data
            self.reverse_names = {v: k for k, v in data.items()}
            log.info(f"Loaded {len(self.names)} names from dictionary")
        else:
            log.warning("Names dictionary is empty or not found")
            self.names = {}
            self.reverse_names = {}

    def protect_names(self, text: str) -> tuple[str, dict[str, str]]:
        """
        Replace names with placeholders before translation.

        Returns:
            Tuple of (protected_text, placeholder_mapping)
        """
        if not self.names:
            return text, {}

        protected = text
        mapping = {}

        for i, (original, arabic) in enumerate(self.names.items()):
            placeholder = f"__NAME{i}__"
            # Replace both Turkish and Arabic versions
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            if pattern.search(protected):
                protected = pattern.sub(placeholder, protected)
                mapping[placeholder] = arabic

        return protected, mapping

    def restore_names(self, text: str, mapping: dict[str, str]) -> str:
        """Restore names from placeholders after translation."""
        if not mapping:
            return text

        restored = text
        for placeholder, arabic_name in mapping.items():
            restored = restored.replace(placeholder, arabic_name)

        return restored

    def post_fix_names(self, text: str) -> str:
        """
        Fix any names that were incorrectly translated.
        Applied after LLM refinement as a safety net.
        """
        if not self.reverse_names:
            return text

        fixed = text
        for arabic_name, turkish_name in self.reverse_names.items():
            # Find common mistranslations and fix them
            turkish_lower = turkish_name.lower()
            # If the Turkish name appears in the Arabic text, replace it
            pattern = re.compile(re.escape(turkish_name), re.IGNORECASE)
            if pattern.search(fixed):
                fixed = pattern.sub(arabic_name, fixed)

        return fixed


class NLLBTranslator:
    """NLLB (No Language Left Behind) translation engine."""

    # NLLB language codes
    LANG_CODES = {
        "tr": "tur_Latn",
        "ar": "arb_Arab",
        "en": "eng_Latn",
        "de": "deu_Latn",
        "fr": "fra_Latn",
        "es": "spa_Latn",
        "ku": "kmr_Latn",
    }

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self.device = None

    async def load_model(self):
        """Load the NLLB model."""
        if self._loaded:
            return

        self.device = config.get_device(config.TRANSLATION_DEVICE)
        log.info(f"Loading NLLB model: {config.TRANSLATION_MODEL} on {self.device}")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_sync)
        self._loaded = True
        log.info("NLLB model loaded successfully")

    def _load_sync(self):
        """Synchronous model loading."""
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            config.TRANSLATION_MODEL,
            src_lang="tur_Latn"
        )
        self._model = AutoModelForSeq2SeqLM.from_pretrained(
            config.TRANSLATION_MODEL,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )
        self._model.to(self.device)
        self._model.eval()

    async def translate_batch(
        self,
        texts: list[str],
        source_lang: str = "tr",
        target_lang: str = "ar"
    ) -> list[str]:
        """
        Translate a batch of texts.

        Args:
            texts: List of texts to translate.
            source_lang: Source language code.
            target_lang: Target language code.

        Returns:
            List of translated texts.
        """
        if not self._loaded:
            await self.load_model()

        if not texts:
            return []

        src_code = self.LANG_CODES.get(source_lang, "tur_Latn")
        tgt_code = self.LANG_CODES.get(target_lang, "arb_Arab")

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._translate_sync,
            texts,
            src_code,
            tgt_code
        )
        return results

    def _translate_sync(
        self,
        texts: list[str],
        src_code: str,
        tgt_code: str
    ) -> list[str]:
        """Synchronous translation for executor."""
        import torch

        self._tokenizer.src_lang = src_code
        results = []

        # Process in batches
        batches = chunk_list(texts, config.TRANSLATION_BATCH_SIZE)

        for batch in batches:
            inputs = self._tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=config.TRANSLATION_MAX_LENGTH
            ).to(self.device)

            tgt_lang_id = self._tokenizer.convert_tokens_to_ids(tgt_code)

            with torch.no_grad():
                generated = self._model.generate(
                    **inputs,
                    forced_bos_token_id=tgt_lang_id,
                    max_new_tokens=config.TRANSLATION_MAX_LENGTH,
                    num_beams=5,
                    early_stopping=True,
                )

            decoded = self._tokenizer.batch_decode(
                generated, skip_special_tokens=True
            )
            results.extend(decoded)

        return results

    def unload(self):
        """Unload model to free memory."""
        if self._model:
            del self._model
            del self._tokenizer
            self._model = None
            self._tokenizer = None
            self._loaded = False
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass


class LLMRefiner:
    """LLM-based translation refinement (Qwen, Gemma, etc.)."""

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self.device = None

    async def load_model(self):
        """Load the LLM model."""
        if not config.USE_LLM_REFINEMENT:
            return
        if self._loaded:
            return

        self.device = config.get_device(config.LLM_DEVICE)
        log.info(f"Loading LLM model: {config.LLM_MODEL} on {self.device}")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_sync)
        self._loaded = True
        log.info("LLM model loaded successfully")

    def _load_sync(self):
        """Synchronous model loading."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            config.LLM_MODEL,
            trust_remote_code=True
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            config.LLM_MODEL,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            trust_remote_code=True,
            device_map="auto" if self.device == "cuda" else None,
        )
        if self.device != "cuda":
            self._model.to(self.device)
        self._model.eval()

    async def refine_translation(
        self,
        turkish_text: str,
        arabic_translation: str,
        context: str = ""
    ) -> str:
        """
        Refine an Arabic translation using LLM.

        Args:
            turkish_text: Original Turkish text.
            arabic_translation: Initial Arabic translation from NLLB.
            context: Optional previous context for coherence.

        Returns:
            Refined Arabic translation.
        """
        if not config.USE_LLM_REFINEMENT or not self._loaded:
            return arabic_translation

        prompt = self._build_prompt(turkish_text, arabic_translation, context)

        loop = asyncio.get_event_loop()
        refined = await loop.run_in_executor(
            None,
            self._generate_sync,
            prompt
        )
        return refined

    def _build_prompt(
        self,
        turkish: str,
        arabic: str,
        context: str
    ) -> str:
        """Build the refinement prompt."""
        system = (
            "أنت مترجم محترف متخصص في ترجمة المسلسلات التركية إلى العربية. "
            "مهمتك تحسين الترجمة العربية لتكون طبيعية وسلسة وتحافظ على أسلوب الحوار. "
            "القواعد:\n"
            "1. اجعل الحوار طبيعياً كما يتحدث العرب\n"
            "2. حافظ على الضمائر والسياق\n"
            "3. لا تترجم أسماء الأشخاص\n"
            "4. حافظ على نبرة الحوار (رسمي، عامي، عاطفي)\n"
            "5. إذا كان السطر يعتمد على ما قبله، حافظ على الترابط\n"
            "6. أجب بالترجمة المحسنة فقط بدون أي شرح"
        )

        user = f"النص التركي: {turkish}\nالترجمة الأولية: {arabic}"
        if context:
            user = f"السياق السابق: {context}\n\n{user}"
        user += "\n\nالترجمة المحسنة:"

        # Format for different model types
        if "qwen" in config.LLM_MODEL.lower():
            return (
                f"<|im_start|>system\n{system}<|im_end|>\n"
                f"<|im_start|>user\n{user}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
        elif "gemma" in config.LLM_MODEL.lower():
            return (
                f"<bos><start_of_turn>system\n{system}<end_of_turn>\n"
                f"<start_of_turn>user\n{user}<end_of_turn>\n"
                f"<start_of_turn>model\n"
            )
        else:
            return f"### System:\n{system}\n\n### User:\n{user}\n\n### Assistant:\n"

    def _generate_sync(self, prompt: str) -> str:
        """Synchronous generation for executor."""
        import torch

        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=config.LLM_MAX_NEW_TOKENS,
                temperature=config.LLM_TEMPERATURE,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        # Decode only the new tokens
        new_tokens = outputs[0][inputs.input_ids.shape[1]:]
        result = self._tokenizer.decode(new_tokens, skip_special_tokens=True)

        # Clean up the result
        result = result.strip()
        # Remove any trailing artifacts
        for stop in ["<|im_end|>", "<end_of_turn>", "###", "\n\n###"]:
            if stop in result:
                result = result[:result.index(stop)].strip()

        return result if result else prompt

    def unload(self):
        """Unload model."""
        if self._model:
            del self._model
            del self._tokenizer
            self._model = None
            self._tokenizer = None
            self._loaded = False
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass


class TranslationPipeline:
    """Complete translation pipeline combining NLLB + LLM + Names."""

    def __init__(self):
        self.nllb = NLLBTranslator()
        self.llm = LLMRefiner()
        self.names = NamesDictionary()

    async def initialize(self):
        """Load all required models."""
        await self.nllb.load_model()
        if config.USE_LLM_REFINEMENT:
            await self.llm.load_model()

    async def translate_segments(
        self,
        segments: list[dict],
        source_lang: str = "tr",
        target_lang: str = "ar"
    ) -> list[dict]:
        """
        Translate a list of speech segments.

        Args:
            segments: List of segment dicts with 'text', 'start', 'end' keys.
            source_lang: Source language code.
            target_lang: Target language code.

        Returns:
            List of segments with added 'translated_text' field.
        """
        start_time = time.time()
        log.info(f"Starting translation of {len(segments)} segments")

        # Step 1: Protect names
        protected_texts = []
        name_mappings = []
        for seg in segments:
            protected, mapping = self.names.protect_names(seg["text"])
            protected_texts.append(protected)
            name_mappings.append(mapping)

        # Step 2: NLLB Translation in batches
        translated_texts = await self.nllb.translate_batch(
            protected_texts, source_lang, target_lang
        )

        # Step 3: Restore names
        restored_texts = []
        for translated, mapping in zip(translated_texts, name_mappings):
            restored = self.names.restore_names(translated, mapping)
            restored = self.names.post_fix_names(restored)
            restored_texts.append(restored)

        # Step 4: LLM Refinement (optional, in context groups)
        if config.USE_LLM_REFINEMENT and self.llm._loaded:
            refined_texts = await self._refine_with_context(
                segments, protected_texts, restored_texts
            )
        else:
            refined_texts = restored_texts

        # Build result
        result_segments = []
        for seg, translated in zip(segments, refined_texts):
            result_seg = dict(seg)
            result_seg["translated_text"] = translated.strip()
            result_segments.append(result_seg)

        elapsed = time.time() - start_time
        log.info(f"Translation complete: {len(segments)} segments in {elapsed:.1f}s")

        return result_segments

    async def _refine_with_context(
        self,
        original_segments: list[dict],
        turkish_texts: list[str],
        arabic_texts: list[str]
    ) -> list[str]:
        """Refine translations with context using LLM."""
        refined = []
        context_window = 3  # Number of previous lines for context

        for i in range(len(arabic_texts)):
            # Build context from previous translations
            context_start = max(0, i - context_window)
            context_parts = arabic_texts[context_start:i]
            context = " | ".join(context_parts) if context_parts else ""

            refined_text = await self.llm.refine_translation(
                turkish_texts[i],
                arabic_texts[i],
                context
            )
            refined.append(refined_text)

        return refined

    async def translate_text(
        self,
        text: str,
        source_lang: str = "tr",
        target_lang: str = "ar"
    ) -> TranslationResult:
        """Translate a single text string."""
        start_time = time.time()

        protected, mapping = self.names.protect_names(text)
        results = await self.nllb.translate_batch([protected], source_lang, target_lang)
        translated = results[0] if results else ""
        translated = self.names.restore_names(translated, mapping)
        translated = self.names.post_fix_names(translated)

        if config.USE_LLM_REFINEMENT and self.llm._loaded:
            translated = await self.llm.refine_translation(text, translated)

        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_language=source_lang,
            target_language=target_lang,
            model_used=config.TRANSLATION_MODEL,
            llm_refined=config.USE_LLM_REFINEMENT,
            processing_time=time.time() - start_time,
        )

    def unload_all(self):
        """Unload all models."""
        self.nllb.unload()
        self.llm.unload()


# Global translation pipeline
translator = TranslationPipeline()
