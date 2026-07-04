from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional
from .agents import InteractionAgent, LayoutAgent, NavigationAgent, SynthesisAgent
from .schema import UIDesign, UI2CaseResult

class UI2CasePipeline:

    def __init__(self, llm, parallel: bool=True):
        self.llm = llm
        self.nav = NavigationAgent(llm)
        self.layout = LayoutAgent(llm)
        self.inter = InteractionAgent(llm)
        self.syn = SynthesisAgent()
        self.parallel = parallel

    def run(self, design: UIDesign, recorder: Optional[Any]=None) -> UI2CaseResult:
        if recorder:
            recorder.save_design(design.to_json(base_dir=recorder.run_dir))
        transitions = self.nav.run(design, recorder=recorder)
        if self.parallel:
            with ThreadPoolExecutor(max_workers=2) as ex:
                f_layout = ex.submit(self.layout.run, design, recorder)
                f_inter = ex.submit(self.inter.run, design, recorder)
                layout = f_layout.result()
                interaction = f_inter.result()
        else:
            layout = self.layout.run(design, recorder=recorder)
            interaction = self.inter.run(design, recorder=recorder)
        test_case = self.syn.assemble(design, transitions, layout, interaction)
        if recorder:
            recorder.record_parsed('synthesis', test_case)
        result = UI2CaseResult(design_id=design.design_id, transitions=transitions, layout=layout, interaction=interaction, test_case=test_case, metadata={'parallel': self.parallel})
        if recorder:
            recorder.record_result(result.to_dict())
        return result
