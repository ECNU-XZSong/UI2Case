from __future__ import annotations
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class Page:
    page_id: str
    image_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UIDesign:
    design_id: str
    pages: List[Page] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def entry_page(self) -> str:
        if not self.pages:
            raise ValueError('UIDesign must contain at least one page')
        return self.pages[0].page_id

    @classmethod
    def from_json(cls, obj: Dict[str, Any], base_dir: str='') -> 'UIDesign':
        pages: List[Page] = []
        for p in obj['pages']:
            img = p.get('image')
            if img and base_dir:
                img = os.path.join(base_dir, img)
            metadata = {k: v for k, v in p.items() if k not in {'page_id', 'image'}}
            pages.append(Page(page_id=p['page_id'], image_path=img, metadata=metadata))
        return cls(design_id=obj.get('design_id', 'design'), pages=pages, metadata=obj.get('metadata', {}))

    def to_json(self, base_dir: str='') -> Dict[str, Any]:
        pages = []
        for p in self.pages:
            image = p.image_path
            if image and base_dir:
                try:
                    image = os.path.relpath(image, base_dir)
                except ValueError:
                    image = p.image_path
            entry = {'page_id': p.page_id, 'image': image}
            entry.update(p.metadata)
            pages.append(entry)
        return {'design_id': self.design_id, 'pages': pages, 'metadata': self.metadata}
Transition = Dict[str, Any]
LayoutArea = Dict[str, Any]
InteractionPoint = Dict[str, Any]

@dataclass
class UI2CaseResult:
    design_id: str
    transitions: List[Transition]
    layout: Dict[str, List[LayoutArea]]
    interaction: Dict[str, List[InteractionPoint]]
    test_case: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
