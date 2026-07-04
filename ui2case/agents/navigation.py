from __future__ import annotations
from typing import Any, List, Optional
from ..llm import parse_json
from ..prompts import NAVIGATION_EXEMPLAR, NAVIGATION_PROMPT
from ..schema import Transition, UIDesign

class NavigationAgent:

    def __init__(self, llm):
        self.llm = llm

    def run(self, design: UIDesign, recorder: Optional[Any]=None) -> List[Transition]:
        system = NAVIGATION_PROMPT
        system += '\n\nExample output:\n' + NAVIGATION_EXEMPLAR
        lines, images = ([], [])
        for p in design.pages:
            lines.append(f'Page_id: {p.page_id}')
            if p.image_path:
                images.append(p.image_path)
        user = 'Here are the pages in order; the first is the main page:\n' + '\n'.join(lines)
        if recorder:
            recorder.record_prompt('navigation', user, system)
        raw = self.llm.chat(system, user, images=images, meta={'agent': 'navigation'})
        if recorder:
            recorder.record_raw('navigation', raw)
        data = parse_json(raw)
        parsed = [{'source_page': d['source_page'], 'target_page': d['target_page'], 'action': d.get('action', '')} for d in data]
        if recorder:
            recorder.record_parsed('navigation', parsed)
        return parsed
