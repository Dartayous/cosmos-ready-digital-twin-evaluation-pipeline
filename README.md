# Cosmos-Ready Digital Twin Evaluation Pipeline

> A production-style digital twin evaluation pipeline designed for Cosmos-era physical AI systems.
---
## Overview

This project implements a production-style digital twin evaluation pipeline using Isaac Sim-style data capture and a Cosmos-ready AI integration architecture.

It demonstrates how simulation data can be structured, evaluated, and transformed into decision-ready outputs under varying real-world conditions.

The goal is NOT to fake Cosmos access.

The goal is to prove:
- I understand the actual pipeline needed for COSMOS Predict and Reason
- I could build it correctly
- I could create a structure this is ready to plug into Cosmos the moment it becomes available

---

## What This Project Demonstrates

- End-to-end digital twin evaluation pipeline design
- Simulation → AI → decision workflow integration
- Scenario-based perception robustness testing
- Production-style data structuring and artifact management
- Cosmos-ready architecture without relying on unavailable APIs
  
---

## Why This Project Matters

In real physical AI systems, the challenge is NOT just generating outputs.

It is:

- ingesting simulator data correctly
- preserving telemetry context
- evaluating perception robustness
- structuring AI requests and responses
- making downstream decisions

This project solves that pipeline problem.

---

## Architecture

Isaac Sim-style capture  
→ import_isaac_capture.py  
→ structured run bundle  

→ build_cosmos_request.py  
→ parse_cosmos_response.py  

→ mock mode (current)  
→ real Cosmos mode (future-ready scaffold)  

→ decision artifact  
→ evaluation report  
→ comparison across runs  

---

## Predict Simulation Flow

baseline run  
→ simulate_predict_output.py  
→ transformed scenario runs  

→ request / reasoning / decision pipeline  
→ comparison output  

---

## What Is Real vs Simulated

### Real / Implemented

- Isaac-style frame import  
- telemetry ingestion  
- structured run packaging  
- Cosmos request generation  
- response normalization  
- decision logic  
- comparison reporting  
- endpoint scaffolding  

### Simulated

- Cosmos Predict outputs (no public API yet)  
- Cosmos Reason executed in mock mode  

The architecture is REAL.  
Only the model call is simulated.

---

## Key Runs

### Baseline

- `run_0004`
- imported Isaac-style frames and telemetry
- used as evaluation baseline

---

### Simulated Predict Outputs

- `run_0004_predict_blur`
- `run_0004_predict_dim_lighting`
- `run_0004_predict_noise`
- `run_0004_predict_occlusion`

These runs simulate degraded perception conditions that would normally be handled by Cosmos Predict.

---

## Visual Results

### Blur Scenario
![Blur Scenario](images/predict_blur.png)

---

### Dim Lighting Scenario
![Dim Lighting](images/predict_dim.png)

---

### Noise Scenario
![Noise Scenario](images/predict_noise.png)

---

### Occlusion Scenario
![Occlusion Scenario](images/predict_occlusion.png)

---

### Comparison Output

```
run_0004_predict_blur         | conf: 0.61 | risk: medium | REVIEW | send_to_review_queue
run_0004_predict_dim_lighting | conf: 0.71 | risk: medium | REVIEW | send_to_review_queue
run_0004_predict_noise        | conf: 0.61 | risk: medium | REVIEW | send_to_review_queue
run_0004_predict_occlusion    | conf: 0.61 | risk: medium | REVIEW | send_to_review_queue
```

---



### Interpretation

- baseline run remains strongest
- degraded conditions reduce confidence
- all degraded runs are flagged for review
- no unsafe automatic decisions are made

This mirrors how real perception validation pipelines behave in production systems.

---

## Example Artifacts

Each run produces structured outputs:

- `frames/`
- `video/video.mp4`
- `telemetry/telemetry.json`
- `manifests/run_manifest.json`
- `requests/cosmos_request.json`
- `responses/cosmos_response.json`
- `decisions/decision.json`
- `reports/evaluation_report.md`

---

## Tools & Technologies

### Core Technologies

- Python
- OpenUSD (Universal Scene Description)
- NVIDIA Isaac Sim

---

### Data & Pipeline

- JSON-based structured data (telemetry, manifests, requests, responses)
- Scenario-based evaluation pipelines
- File-based run artifact system

---

### AI Integration Layer

- NVIDIA Cosmos (integration-ready architecture)
- Simulated Cosmos Predict outputs (no public API access)
- Mock Cosmos Reason execution layer

---

### Engineering Focus

- Perception robustness evaluation
- Scenario-based testing (blur, noise, lighting, occlusion)
- Confidence and risk scoring
- Decision routing (review vs automated action)
- Production-style pipeline architecture

---

## Engineering Note

This system is designed to separate simulation, inference, and evaluation layers — allowing real AI models (such as Cosmos Predict and Reason) to be integrated without changing the surrounding pipeline.

---

## 🧠 Author

Dartayous Hunter - Digital Twin Engineer (NVIDIA-focused)

---
