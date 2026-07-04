from __future__ import annotations
from typing import Any, Dict, List
from ..schema import InteractionPoint, LayoutArea, Transition, UIDesign

class SynthesisAgent:

    def assemble(self, design: UIDesign, transitions: List[Transition], layout: Dict[str, List[LayoutArea]], interaction: Dict[str, List[InteractionPoint]]) -> Dict[str, Any]:
        by_source: Dict[str, List[Transition]] = {}
        for t in transitions:
            by_source.setdefault(t['source_page'], []).append(t)

        def _assemble(page_id: str, path: frozenset) -> Dict[str, Any]:
            node: Dict[str, Any] = {'page_id': page_id, 'layout': layout.get(page_id, []), 'interaction': interaction.get(page_id, []), 'transition': []}
            for t in by_source.get(page_id, []):
                target = t['target_page']
                if target in path:
                    node['transition'].append({'action': t['action'], 'sub_page': {'page_id': target, 'cyclic_ref': True}})
                    continue
                sub = _assemble(target, path | {target})
                node['transition'].append({'action': t['action'], 'sub_page': sub})
            return node
        root = design.entry_page
        return _assemble(root, frozenset({root}))
