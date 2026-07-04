from __future__ import annotations
import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui2case.artifacts import RunRecorder
from ui2case.config import Config
from ui2case.io import load_json, write_json
from ui2case.llm import get_llm
from ui2case.pipeline import UI2CasePipeline
from ui2case.schema import UIDesign

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--design', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--run-dir', default=None)
    ap.add_argument('--mock', action='store_true', help='force offline mock backend')
    ap.add_argument('--no-parallel', action='store_true')
    args = ap.parse_args()
    cfg = Config.load(mock=True if args.mock else None)
    llm = get_llm(cfg)
    recorder = RunRecorder(args.run_dir) if args.run_dir else None
    if recorder:
        recorder.save_config(cfg.to_public_dict())
    base = os.path.dirname(os.path.abspath(args.design))
    design = UIDesign.from_json(load_json(args.design), base_dir=base)
    pipe = UI2CasePipeline(llm, parallel=not args.no_parallel)
    result = pipe.run(design, recorder=recorder)
    out = args.out or f'output_{design.design_id}.json'
    write_json(out, result.to_dict())
    backend = 'mock (offline)' if cfg.mock else f'{cfg.model}'
    print(f'[ui2case] backend={backend} -> wrote {out}')
if __name__ == '__main__':
    main()
