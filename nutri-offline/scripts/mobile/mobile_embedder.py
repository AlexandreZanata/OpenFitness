"""Mobile embedder — ONNX int8 runtime with SentenceTransformer fallback."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from mobile_paths import EMBEDDER_ONNX, MOBILE_EMBED_DIM, MOBILE_EMBED_MODEL, ROOT


class MobileEmbedder:
    def __init__(
        self,
        *,
        onnx_path: Path = EMBEDDER_ONNX,
        model_name: str = MOBILE_EMBED_MODEL,
        device: str = "cpu",
    ) -> None:
        self._onnx_path = onnx_path
        self._model_name = model_name
        self._device = device
        self._session = None
        self._tokenizer = None
        self._fallback_model = None

        if onnx_path.is_file():
            self._load_onnx()
        else:
            self._load_fallback()

    @property
    def backend(self) -> str:
        if self._session is not None:
            return "onnx-int8"
        return "sentence-transformers"

    def _load_onnx(self) -> None:
        import onnxruntime as ort
        from transformers import AutoTokenizer

        os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._session = ort.InferenceSession(
            str(self._onnx_path),
            providers=["CPUExecutionProvider"],
        )

    def _load_fallback(self) -> None:
        import sys

        rag_dir = Path(__file__).resolve().parents[1] / "rag"
        sys.path.insert(0, str(rag_dir))
        from embed import load_embedder  # noqa: E402

        self._fallback_model = load_embedder(self._device, model_name=self._model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._session is not None:
            return [self._encode_onnx(text) for text in texts]
        assert self._fallback_model is not None
        import sys

        rag_dir = Path(__file__).resolve().parents[1] / "rag"
        sys.path.insert(0, str(rag_dir))
        from embed import encode_texts  # noqa: E402

        return encode_texts(self._fallback_model, texts, show_progress=False)

    def _encode_onnx(self, text: str) -> list[float]:
        assert self._tokenizer is not None and self._session is not None
        encoded = self._tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )
        inputs = {input_name: encoded[input_name] for input_name in encoded if input_name in {i.name for i in self._session.get_inputs()}}
        outputs = self._session.run(None, inputs)
        vector = outputs[0]
        if vector.ndim > 1:
            vector = vector[0]
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        if len(vector) != MOBILE_EMBED_DIM:
            vector = vector[:MOBILE_EMBED_DIM]
        return vector.astype(np.float32).tolist()
