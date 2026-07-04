from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..llm import parse_json
from ..prompts import LAYOUT_EXEMPLAR, LAYOUT_PROMPT
from ..schema import LayoutArea, Page, UIDesign

class LayoutAgent:

    def __init__(self, llm):
        self.llm = llm

    def run_page(self, page: Page, recorder: Optional[Any]=None) -> List[LayoutArea]:
        system = LAYOUT_PROMPT
        system += '\n\nExample output:\n' + LAYOUT_EXEMPLAR
        user = f'Analyze the layout of this page. Page_id: {page.page_id}'
        images = [page.image_path] if page.image_path else []
        if recorder:
            recorder.record_prompt('layout', user, system, page=page.page_id)
        raw = self.llm.chat(system, user, images=images, meta={'agent': 'layout', 'page': page.page_id})
        if recorder:
            recorder.record_raw('layout', raw, page=page.page_id)
        parsed = parse_json(raw)
        if recorder:
            recorder.record_parsed('layout', parsed, page=page.page_id)
        return parsed

    def run(self, design: UIDesign, recorder: Optional[Any]=None) -> Dict[str, List[LayoutArea]]:
        return {p.page_id: self.run_page(p, recorder=recorder) for p in design.pages}
