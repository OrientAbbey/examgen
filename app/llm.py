"""Client du fournisseur d'IA (aucune dépendance : urllib). Désactivé tant que EXAMGEN_LLM_* n'est pas configuré.

Deux protocoles :
  - « openai » : tout service compatible /chat/completions (Ollama, LM Studio, vLLM, llama.cpp, Groq, OpenRouter, Mistral, Gemini…)
  - « anthropic » : API Messages d'Anthropic.
Variables : EXAMGEN_LLM_PROVIDER (openai|anthropic), EXAMGEN_LLM_BASE_URL, EXAMGEN_LLM_MODEL, EXAMGEN_LLM_API_KEY,
            EXAMGEN_LLM_TIMEOUT (s), EXAMGEN_LLM_MAX_TOKENS, EXAMGEN_LLM_JSON_MODE (1 = response_format json_object)."""
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse


class LLMError(Exception):
    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    model: str
    api_key: str = ""
    timeout: float = 90.0
    max_tokens: int = 3000
    json_mode: bool = False
    retry_pause: float = 1.0

    @property
    def hote(self) -> str:
        return urlparse(self.base_url).netloc or self.base_url


def config_from_env(env=None):
    env = os.environ if env is None else env
    provider = (env.get("EXAMGEN_LLM_PROVIDER") or "openai").strip().lower()
    model = (env.get("EXAMGEN_LLM_MODEL") or "").strip()
    base = (env.get("EXAMGEN_LLM_BASE_URL") or ("https://api.anthropic.com" if provider == "anthropic" else "")).strip()
    key = (env.get("EXAMGEN_LLM_API_KEY") or "").strip()
    if provider not in ("openai", "anthropic") or not model or not base:
        return None
    if provider == "anthropic" and not key:
        return None
    return LLMConfig(provider, base.rstrip("/"), model, key, float(env.get("EXAMGEN_LLM_TIMEOUT", "90")), int(env.get("EXAMGEN_LLM_MAX_TOKENS", "3000")),
                     env.get("EXAMGEN_LLM_JSON_MODE", "0") == "1")


class LLMClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg

    def _post(self, url: str, headers: dict, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        derniere = None
        for tentative in (1, 2):                       # une relance sur 429 / 5xx / délai dépassé
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.cfg.timeout) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:200].replace(self.cfg.api_key or "\0", "***")
                derniere = LLMError("AI_UPSTREAM", "Le fournisseur d'IA a répondu HTTP %d (%s)" % (e.code, detail.strip()))
                if e.code not in (429, 500, 502, 503, 504):
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                derniere = LLMError("AI_INDISPONIBLE", "Fournisseur d'IA injoignable : %s" % getattr(e, "reason", e), 503)
            except ValueError:
                derniere = LLMError("AI_BAD_RESPONSE", "Réponse du fournisseur illisible")
                break
            if tentative == 1:
                time.sleep(self.cfg.retry_pause)
        raise derniere

    def complete(self, system: str, user: str) -> str:
        c = self.cfg
        if c.provider == "anthropic":
            data = self._post(c.base_url + "/v1/messages", {"x-api-key": c.api_key, "anthropic-version": "2023-06-01"},
                              {"model": c.model, "max_tokens": c.max_tokens, "temperature": 0.4, "system": system, "messages": [{"role": "user", "content": user}]})
            texte = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        else:
            body = {"model": c.model, "max_tokens": c.max_tokens, "temperature": 0.4,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            if c.json_mode:
                body["response_format"] = {"type": "json_object"}
            data = self._post(c.base_url + "/chat/completions", {"Authorization": "Bearer " + c.api_key} if c.api_key else {}, body)
            try:
                texte = data["choices"][0]["message"]["content"] or ""
            except (KeyError, IndexError, TypeError):
                raise LLMError("AI_BAD_RESPONSE", "Réponse du fournisseur inattendue")
        if not texte.strip():
            raise LLMError("AI_BAD_RESPONSE", "Réponse vide du fournisseur")
        return texte
