import re
from typing import Dict, List, Optional, Set

from ..base import BaseModel, PrivateAttr
try:  # pydantic v2 config helper
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore


class TorchBertNerStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, Dict]
    model_path: str
    vocab_path: str
    label_map: Dict[int, str]
    device: Optional[str] = None

    # Silence protected namespace warning for field 'model_path'
    model_config = ConfigDict(protected_namespaces=())  # type: ignore[call-arg]

    _model: Optional[object] = PrivateAttr(default=None)
    _keys: Optional[Set[str]] = PrivateAttr(default_factory=set)
    _vocab: Optional[Dict[str, int]] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._keys = {k.lower() for k in self.locations_db.keys()}
        try:
            import torch  # type: ignore
            self._model = torch.jit.load(self.model_path, map_location=self.device or ("cuda" if torch.cuda.is_available() else "cpu"))
            self._model.eval()
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "TorchScript model load failed. Provide a local torchscript file for BERT NER (model_path)."
            ) from e
        try:
            vocab: Dict[str, int] = {}
            with open(self.vocab_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    token = line.strip()
                    if token:
                        vocab[token] = i
            self._vocab = vocab
        except Exception as e:  # pragma: no cover
            raise ImportError("Failed to load vocab.txt for WordPiece tokenization (vocab_path)") from e

    def _wordpiece_tokenize(self, text: str) -> List[str]:
        if not self._vocab:
            return []
        tokens: List[str] = []
        for word in re.findall(r"[\w'-]+", text.lower()):
            if word in self._vocab:
                tokens.append(word)
                continue
            i = 0
            sub_tokens: List[str] = []
            while i < len(word):
                j = len(word)
                piece = None
                while i < j:
                    sub = word[i:j]
                    if sub in self._vocab:
                        piece = sub
                        break
                    if ("##" + sub) in self._vocab:
                        piece = "##" + sub
                        break
                    j -= 1
                if piece is None:
                    sub_tokens = ["[UNK]"]
                    break
                sub_tokens.append(piece)
                i = j if piece == sub else j
            tokens.extend(sub_tokens)
        if "[CLS]" in (self._vocab or {}):
            tokens = ["[CLS]"] + tokens
        if "[SEP]" in (self._vocab or {}):
            tokens = tokens + ["[SEP]"]
        return tokens

    def _encode(self, tokens: List[str]):
        if not self._vocab:
            return None
        ids = [self._vocab.get(t, self._vocab.get("[UNK]", 0)) for t in tokens]
        attn = [1] * len(ids)
        return ids, attn

    def extract(self, text: str) -> List[str]:
        if not text or self._model is None:
            return []
        tokens = self._wordpiece_tokenize(text)
        enc = self._encode(tokens)
        if not enc:
            return []
        ids, attn = enc
        try:
            import torch  # type: ignore
            ids_t = torch.tensor([ids])
            attn_t = torch.tensor([attn])
            logits = self._model(ids_t, attn_t)
            if hasattr(logits, "detach"):
                probs = torch.softmax(logits.detach(), dim=-1)
                pred = torch.argmax(probs, dim=-1).squeeze(0).tolist()
            else:
                return []
        except Exception:
            return []
        labels = [self.label_map.get(i, "O") for i in pred]
        ents: Set[str] = set()
        current: List[str] = []
        for tok, lab in zip(tokens, labels):
            if lab.startswith("B-") or (lab != "O" and not lab.startswith("I-")):
                if current:
                    ents.add(" ".join([t.replace("##", "") for t in current]).strip())
                    current = []
                current.append(tok)
            elif lab.startswith("I-") and current:
                current.append(tok)
            else:
                if current:
                    ents.add(" ".join([t.replace("##", "") for t in current]).strip())
                    current = []
        if current:
            ents.add(" ".join([t.replace("##", "") for t in current]).strip())
        keys = self._keys or set()
        matches = {e.lower() for e in ents if e.lower() in keys}
        return list(matches or {e.lower() for e in ents})
