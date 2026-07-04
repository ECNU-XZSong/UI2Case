from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    model: str = 'doubao-1.5-vision-pro-32k'
    api_key: str = ''
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 4096
    mock: bool = False
    thinking: str = 'disabled'

    @staticmethod
    def _load_dotenv_fallback() -> None:
        for path in ('.env', os.path.join(os.getcwd(), '.env')):
            if not os.path.isfile(path):
                continue
            with open(path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    if line.startswith('export '):
                        line = line[len('export '):]
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
            break

    @classmethod
    def load(cls, mock: Optional[bool]=None) -> 'Config':
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            cls._load_dotenv_fallback()
        c = cls(model=os.environ.get('UI2CASE_MODEL', 'doubao-1.5-vision-pro-32k'), api_key=os.environ.get('UI2CASE_API_KEY', ''), base_url=os.environ.get('UI2CASE_BASE_URL') or None, temperature=float(os.environ.get('UI2CASE_TEMPERATURE', '0.0')), max_tokens=int(os.environ.get('UI2CASE_MAX_TOKENS', '4096')), mock=os.environ.get('UI2CASE_MOCK', '').lower() in ('1', 'true', 'yes'), thinking=os.environ.get('UI2CASE_THINKING', 'disabled'))
        if mock is not None:
            c.mock = mock
        if not c.api_key and (not c.mock):
            c.mock = True
        return c

    def to_public_dict(self) -> dict:
        return {'model': self.model, 'base_url': self.base_url, 'temperature': self.temperature, 'max_tokens': self.max_tokens, 'mock': self.mock, 'api_key_present': bool(self.api_key)}
