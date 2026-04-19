# Project 08 — Cosmos-Ready Digital Twin Evaluation Pipeline

## Overview

This project demonstrates a digital twin evaluation pipeline built around Isaac Sim-style perception data, structured run packaging, telemetry-aware analysis, simulated Cosmos Predict outputs, and a dual-mode Cosmos Reason integration layer.

The goal was not to claim production deployment of NVIDIA Cosmos, but to build a **real, honest, end-to-end system** that is ready for hosted Cosmos services as they become accessible.

This project shows how simulation outputs can be packaged, evaluated, compared, and routed into downstream decision artifacts in a way that mirrors real physical AI workflows.

---

## Why This Project Matters

For physical AI and digital twin workflows, the core challenge is not just generating scenes. The challenge is building a robust pipeline that can:

- ingest simulator outputs
- preserve telemetry and context
- evaluate perception quality across scenario variants
- structure AI requests and responses
- produce downstream decisions for training or review

This project solves that pipeline problem.

---

## What This Project Does

This repository implements:

- Isaac-style frame import into structured run bundles
- sidecar telemetry ingestion
- telemetry-aware mock reasoning
- simulated Cosmos Predict-style output generation
- dual-mode Cosmos Reason integration:
  - `mock`
  - `real_cosmos` scaffold
- request / response / decision artifact generation
- cross-run comparison reporting
- video generation for run playback

---

## Architecture

```text
Isaac Sim-style capture
→ import_isaac_capture.py
→ structured run bundle
→ build_cosmos_request.py
→ parse_cosmos_response.py
    ├── mock mode
    └── real_cosmos mode scaffold
→ decision artifact
→ evaluation report
→ comparison across runs

For Predict-style testing:

baseline run
→ simulate_predict_output.py
→ transformed future-world runs
→ request / reasoning / decision pipeline
→ comparison output

---
```
## What Is Real vs Simulated
Real / Implemented
Isaac-style frame import
telemetry import from sidecar JSON
run packaging
request generation
response normalization
decision generation
comparison reporting
endpoint harnesses for future hosted integration

---

## Simulated / Scaffolded
Cosmos Predict outputs are currently simulated locally because the public Build interface available during this project exposed a demo experience, not user-upload API inference.
Cosmos Reason is currently executed in mock mode locally, but the real_cosmos call path, config switch, endpoint harness, and normalization logic are already implemented and validated through the network layer.

---

## Key Runs

### Baseline
run_0004
imported Isaac-style frames and sidecar telemetry
used as the main baseline for evaluation

### Simulated Predict Outputs
run_0004_predict_dim_lighting
run_0004_predict_blur
run_0004_predict_noise
run_0004_predict_occlusion

These runs simulate future-world output conditions that would later be replaced by hosted Cosmos Predict results.
---

## Results

### Comparison Output
run_0004_predict_blur          | conf: 0.61 | risk: medium | REVIEW | send_to_review_queue
run_0004_predict_dim_lighting  | conf: 0.71 | risk: medium | REVIEW | send_to_review_queue
run_0004_predict_noise         | conf: 0.61 | risk: medium | REVIEW | send_to_review_queue
run_0004_predict_occlusion     | conf: 0.61 | risk: medium | REVIEW | send_to_review_queue

### Interpretation
the imported baseline remains strongest
transformed runs degrade perception confidence
degraded runs are routed for manual review instead of automatic inclusion

This mirrors how perception robustness evaluation would work in a real pipeline.

---

## Example Artifacts

This project produces structured artifacts for every run:

frames/
video/video.mp4
telemetry/telemetry.json
manifests/run_manifest.json
requests/cosmos_request.json
responses/cosmos_response.json
decisions/decision.json
reports/evaluation_report.md

---

## Example Media To Include

Add screenshots or GIFs for:

baseline imported run
dim lighting variant
blur variant
noise variant
occlusion variant

Also include:

a screenshot of run_0004_predict_comparison.txt
a sample cosmos_response.json
a sample evaluation_report.md

---

## Folder Structure
configs/
docs/
images/
prompts/
runs/
src/
usd/
README.md

### Important scripts:

src/import_isaac_capture.py
src/build_cosmos_request.py
src/parse_cosmos_response.py
src/evaluate_obstacle_visibility.py
src/simulate_predict_output.py
src/compare_runs.py
src/test_cosmos_endpoint.py
src/test_cosmos_predict_endpoint.py

---

## Current Limits

This project does not claim that real public hosted Cosmos Predict or Cosmos Reason custom-input API inference was available at the time of implementation.

Instead, it demonstrates:

the real pipeline architecture
the real ingestion and evaluation flow
the real endpoint-ready integration layer
simulated Predict outputs and mock Reason execution where platform access was not publicly exposed

This was an intentional engineering boundary, not a shortcut.

---

## Next Phase

The next upgrade path is:

replace simulated Predict outputs with hosted Cosmos Predict outputs
replace mock Reason with hosted Cosmos Reason responses
compare hosted-model outputs against the current mock and telemetry-aware evaluation flow

---

## Why This Repo Is Valuable

This repo demonstrates that I can:

build digital twin evaluation systems around simulation outputs
design structured AI integration layers
ingest telemetry and reason over scenario variation
recover from real engineering setbacks such as storage corruption and rebuild deterministically
prepare a pipeline for hosted model integration without pretending access exists where it does not

This is exactly the kind of systems thinking required in digital twin, robotics, and physical AI engineering.


---

# Add a `.gitignore`

Create `.gitignore` in the project root with this:

```gitignore
__pycache__/
*.pyc
*.pyo
*.swp
.DS_Store
Thumbs.db