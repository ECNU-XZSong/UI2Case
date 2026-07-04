from __future__ import annotations
import base64
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

def encode_image(path: str) -> str:
    with open(path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    ext = os.path.splitext(path)[1].lstrip('.').lower() or 'png'
    if ext == 'jpg':
        ext = 'jpeg'
    return f'data:image/{ext};base64,{data}'

def parse_json(text: str) -> Any:
    if not text:
        raise ValueError('empty model response')
    t = text.strip()
    fence = re.search('```(?:json)?\\s*(.*?)```', t, re.DOTALL)
    if fence:
        t = fence.group(1).strip()
    try:
        return json.loads(t, strict=False)
    except json.JSONDecodeError:
        pass
    for opener, closer in (('[', ']'), ('{', '}')):
        s, e = (t.find(opener), t.rfind(closer))
        if s != -1 and e > s:
            try:
                return json.loads(t[s:e + 1], strict=False)
            except json.JSONDecodeError:
                continue
    fixed = _fix_escapes(t)
    if fixed != t:
        try:
            return json.loads(fixed, strict=False)
        except json.JSONDecodeError:
            pass
        for opener, closer in (('[', ']'), ('{', '}')):
            s, e = (fixed.find(opener), fixed.rfind(closer))
            if s != -1 and e > s:
                try:
                    return json.loads(fixed[s:e + 1], strict=False)
                except json.JSONDecodeError:
                    continue
    try:
        from json_repair import repair_json
        obj = repair_json(t, return_objects=True)
        if isinstance(obj, (list, dict)) and obj:
            return obj
    except Exception:
        pass
    salvaged = _salvage_objects(t) or _salvage_objects(fixed)
    if salvaged:
        return salvaged
    raise ValueError(f'could not parse JSON from response:\n{text[:500]}')

def _fix_escapes(t: str) -> str:
    t = re.sub('\\\\u(?![0-9a-fA-F]{4})', '', t)
    t = re.sub('\\\\([^"\\\\/bfnrtu])', '\\1', t)
    return t

def _salvage_objects(t: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    depth = 0
    start: Optional[int] = None
    in_str = False
    esc = False
    for i, ch in enumerate(t):
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}' and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    obj = json.loads(t[start:i + 1], strict=False)
                    if isinstance(obj, dict):
                        out.append(obj)
                except json.JSONDecodeError:
                    pass
                start = None
    return out

class BaseLLM:

    def chat(self, system: str, user_text: str, images: Optional[List[str]]=None, meta: Optional[Dict[str, Any]]=None) -> str:
        raise RuntimeError('BaseLLM.chat is abstract and must be provided by a concrete LLM class')

class OpenAICompatibleLLM(BaseLLM):

    def __init__(self, model: str, api_key: str, base_url: Optional[str]=None, temperature: float=0.0, max_tokens: int=4096, extra_body: Optional[Dict[str, Any]]=None, timeout: float=300.0, empty_retries: int=2):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_body = extra_body or None
        self.empty_retries = empty_retries

    def chat(self, system, user_text, images=None, meta=None) -> str:
        content: List[Dict[str, Any]] = [{'type': 'text', 'text': user_text}]
        for img in images or []:
            url = img if img.startswith('data:') else encode_image(img)
            content.append({'type': 'image_url', 'image_url': {'url': url}})
        kwargs: Dict[str, Any] = {}
        if self.extra_body:
            kwargs['extra_body'] = self.extra_body
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}]
        last_diag = ''
        for attempt in range(self.empty_retries + 1):
            resp = self.client.chat.completions.create(model=self.model, messages=messages, temperature=self.temperature, max_tokens=self.max_tokens, **kwargs)
            choice = resp.choices[0]
            text = self._message_text(choice.message)
            if text.strip():
                return text
            last_diag = self._empty_diag(resp, choice, meta)
            if attempt < self.empty_retries:
                time.sleep(0.75 * (attempt + 1))
        raise ValueError(last_diag)

    def _message_text(self, message) -> str:
        content = getattr(message, 'content', None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get('text') or ''))
                else:
                    parts.append(str(getattr(item, 'text', '') or ''))
            return ''.join(parts)
        return ''

    def _empty_diag(self, resp, choice, meta) -> str:
        meta = meta or {}
        usage = getattr(resp, 'usage', None)
        if hasattr(usage, 'model_dump'):
            usage = usage.model_dump()
        message = getattr(choice, 'message', None)
        if hasattr(message, 'model_dump'):
            msg = message.model_dump()
            msg.pop('content', None)
        else:
            msg = str(message)
        return f"empty model response from {self.model} (agent={meta.get('agent')}, page={meta.get('page')}, finish_reason={getattr(choice, 'finish_reason', None)}, usage={usage}, message_without_content={msg})"

class MockLLM(BaseLLM):

    def __init__(self, registry: Optional[Dict[str, Any]]=None):
        from .mock_data import MOCK_REGISTRY
        self.registry = registry or MOCK_REGISTRY

    def chat(self, system, user_text, images=None, meta=None) -> str:
        meta = meta or {}
        agent = meta.get('agent')
        page = meta.get('page')
        if agent == 'navigation':
            return json.dumps(self.registry['navigation'], ensure_ascii=False)
        if agent in ('layout', 'interaction'):
            return json.dumps(self.registry[agent].get(page, []), ensure_ascii=False)
        return '[]'

def is_doubao(model: Optional[str], base_url: Optional[str]) -> bool:
    m = (model or '').lower()
    b = (base_url or '').lower()
    return m.startswith('doubao') or m.startswith('ep-') or 'volces' in b or ('/ark' in b)

def is_qwen(model: Optional[str], base_url: Optional[str]) -> bool:
    m = (model or '').lower()
    b = (base_url or '').lower()
    return m.startswith('qwen') or 'dashscope' in b or 'aliyuncs' in b

def is_gemini(model: Optional[str], base_url: Optional[str]) -> bool:
    return 'gemini' in (model or '').lower()

def thinking_extra_body(model, base_url, thinking: str) -> Optional[Dict[str, Any]]:
    if not thinking:
        return None
    if is_doubao(model, base_url):
        return {'thinking': {'type': thinking}}
    if is_qwen(model, base_url):
        return {'enable_thinking': thinking == 'enabled'}
    if is_gemini(model, base_url):
        if thinking == 'enabled':
            return {'reasoning': {'enabled': True}}
        if 'pro' in (model or '').lower():
            return {'reasoning': {'effort': 'low'}}
        return {'reasoning': {'enabled': False}}
    return None

def get_llm(config) -> BaseLLM:
    if config.mock or not config.api_key:
        return MockLLM()
    return OpenAICompatibleLLM(model=config.model, api_key=config.api_key, base_url=config.base_url, temperature=config.temperature, max_tokens=config.max_tokens, extra_body=thinking_extra_body(config.model, config.base_url, getattr(config, 'thinking', 'disabled')), empty_retries=int(os.environ.get('UI2CASE_EMPTY_RETRIES', '2')))
