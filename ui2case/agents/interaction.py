from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..llm import parse_json
from ..prompts import INTERACTION_EXEMPLAR, INTERACTION_PROMPT
from ..schema import InteractionPoint, Page, UIDesign

class InteractionAgent:

    def __init__(self, llm):
        self.llm = llm

    def run_page(self, page: Page, recorder: Optional[Any]=None) -> List[InteractionPoint]:
        system = INTERACTION_PROMPT
        system += '\n\nExample output:\n' + INTERACTION_EXEMPLAR
        user = f'Identify interaction test points on this page. Page_id: {page.page_id}'
        images = [page.image_path] if page.image_path else []
        if recorder:
            recorder.record_prompt('interaction', user, system, page=page.page_id)
        raw = self.llm.chat(system, user, images=images, meta={'agent': 'interaction', 'page': page.page_id})
        if recorder:
            recorder.record_raw('interaction', raw, page=page.page_id)
        parsed = parse_json(raw)
        if recorder:
            recorder.record_parsed('interaction', parsed, page=page.page_id)
        return parsed

    def run(self, design: UIDesign, recorder: Optional[Any]=None) -> Dict[str, List[InteractionPoint]]:
        return {p.page_id: self.run_page(p, recorder=recorder) for p in design.pages}
