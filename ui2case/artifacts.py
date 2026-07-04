from __future__ import annotations
import os
from typing import Any, Dict, Optional
from .io import ensure_dir, safe_name, write_json, write_text

class RunRecorder:

    def __init__(self, run_dir: str):
        self.run_dir = ensure_dir(run_dir)
        for sub in ('prompts', 'raw_outputs', 'parsed_outputs'):
            ensure_dir(os.path.join(self.run_dir, sub))

    def path(self, *parts: str) -> str:
        return os.path.join(self.run_dir, *parts)

    def save_config(self, config: Dict[str, Any]) -> None:
        write_json(self.path('config.json'), config)

    def save_design(self, design: Dict[str, Any]) -> None:
        write_json(self.path('design.json'), design)

    def record_prompt(self, agent: str, user_text: str, system_text: str, page: Optional[str]=None) -> None:
        stem = self._stem(agent, page)
        write_text(self.path('prompts', f'{stem}.txt'), f'[SYSTEM]\n{system_text}\n\n[USER]\n{user_text}\n')

    def record_raw(self, agent: str, raw: str, page: Optional[str]=None) -> None:
        write_text(self.path('raw_outputs', f'{self._stem(agent, page)}.txt'), raw)

    def record_parsed(self, agent: str, parsed: Any, page: Optional[str]=None) -> None:
        write_json(self.path('parsed_outputs', f'{self._stem(agent, page)}.json'), parsed)

    def record_result(self, result: Dict[str, Any]) -> None:
        write_json(self.path('result.json'), result)

    def record_error(self, name: str, error: BaseException) -> None:
        write_json(self.path('error.json'), {'where': name, 'type': type(error).__name__, 'message': str(error)})

    def _stem(self, agent: str, page: Optional[str]=None) -> str:
        if page:
            return f'{safe_name(agent)}_{safe_name(page)}'
        return safe_name(agent)
