import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui2case.agents import SynthesisAgent
from ui2case.config import Config
from ui2case.llm import get_llm
from ui2case.pipeline import UI2CasePipeline
from ui2case.schema import Page, UIDesign

def _sample_design():
    return UIDesign(design_id='t', pages=[Page('Page_0'), Page('Page_1'), Page('Page_2')])

def test_pipeline_runs_offline_and_reproduces_example():
    llm = get_llm(Config.load(mock=True))
    result = UI2CasePipeline(llm).run(_sample_design())
    assert len(result.transitions) == 2
    tc = result.test_case
    assert tc['page_id'] == 'Page_0'
    assert len(tc['interaction']) == 8
    targets = {t['sub_page']['page_id'] for t in tc['transition']}
    assert targets == {'Page_1', 'Page_2'}

def test_synthesis_handles_cycles():
    design = UIDesign(design_id='cyc', pages=[Page('Page_0'), Page('Page_1')])
    transitions = [{'source_page': 'Page_0', 'target_page': 'Page_1', 'action': 'go'}, {'source_page': 'Page_1', 'target_page': 'Page_0', 'action': 'back'}]
    tree = SynthesisAgent().assemble(design, transitions, {}, {})
    page1 = tree['transition'][0]['sub_page']
    back = page1['transition'][0]['sub_page']
    assert back.get('cyclic_ref') is True
if __name__ == '__main__':
    test_pipeline_runs_offline_and_reproduces_example()
    test_synthesis_handles_cycles()
    print('ok')
