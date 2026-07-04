# UI2Case: A Multi-Agent Framework for Test Case Generation from UI Designs via Multimodal Large Language Models

## Directory Structure

- `ui2case/`: core implementation of UI2Case.
- `ui2case/agents/`: Navigation, Layout, Interaction, and Synthesis agents.
- `ui2case/prompts.py`: task prompts used by the MLLM-guided agents.
- `scripts/run_ui2case.py`: command-line entry point for running UI2Case.
- `datasets/rico_36/`: public RICO-36 UI data.
- `data/sample/`: minimal mock example for offline execution.
- `tests/`: offline smoke test.

## Requirements

Python 3.10 or later is recommended.
Install the required packages with:

```bash
pip install -r requirements.txt
```

## Offline Smoke Test

The following command checks the pipeline with the offline mock backend and does not require an API key:

```bash
python3 -B tests/test_pipeline.py
```

## Running UI2Case

Run the included mock example:

```bash
python3 scripts/run_ui2case.py --design data/sample/design.json --mock
```

Run UI2Case on a custom UI design file:

```bash
python3 scripts/run_ui2case.py --design path/to/design.json --out output.json
```

## Input Format

The input design file is a JSON file containing a design identifier and an ordered list of UI pages.
The first page is treated as the entry page.

```json
{
  "design_id": "example-ui",
  "pages": [
    {"page_id": "Page_0", "image": "Page_0.png"},
    {"page_id": "Page_1", "image": "Page_1.png"}
  ]
}
```

Image paths are resolved relative to the location of the design JSON file.

## Model Configuration

For real MLLM calls, configure the model through environment variables:

```bash
export UI2CASE_MODEL="your-model-name"
export UI2CASE_BASE_URL="your-openai-compatible-endpoint"
export UI2CASE_API_KEY="your-api-key"
```

## Data Availability

The public RICO-36 data is provided under `datasets/rico_36/`.

The industrial UI designs used in the paper cannot be released due to confidentiality agreements.
