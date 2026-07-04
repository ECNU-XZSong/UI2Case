from __future__ import annotations
import json
import os
from typing import Any

def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path

def load_json(path: str) -> Any:
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def write_json(path: str, obj: Any) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        ensure_dir(parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        ensure_dir(parent)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

def safe_name(value: str) -> str:
    allowed = []
    for ch in value:
        if ch.isalnum() or ch in ('-', '_', '.'):
            allowed.append(ch)
        else:
            allowed.append('_')
    name = ''.join(allowed).strip('_')
    return name or 'item'
