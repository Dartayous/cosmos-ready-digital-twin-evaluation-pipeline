# Project 08 Data Flow

## Goal
Project 08 demonstrates a Cosmos-style physical AI evaluation pipeline using an Isaac Sim warehouse scene, Carter robot sensor data, and structured reasoning outputs.

This project does NOT depend on fully working autonomous avoidance behavior.
It focuses on perception, packaging, reasoning, and downstream decision artifacts.

## Core Question
Can the obstacle still be detected reliably under scenario variation?

## System Flow

Simulation Environment
→ Sensor Capture
→ Structured Run Package
→ Cosmos Request Build
→ Cosmos Reasoning Output
→ Decision JSON
→ Evaluation Summary

## Layer Breakdown

### 1. Simulation Environment
Source:
- Isaac Sim warehouse scene
- Carter robot
- Box obstacle
- LiDAR baseline
- Optional RGB frame capture

Purpose:
- Produce physically grounded scene and sensor context

### 2. Sensor Capture
Inputs may include:
- LiDAR beams
- RGB frames
- camera metadata
- obstacle metadata
- robot pose

Purpose:
- Convert simulation state into structured artifacts

### 3. Structured Run Package
Each run stores:
- run manifest
- telemetry
- frame paths
- request JSON
- response JSON
- decision JSON
- markdown report

Purpose:
- make every evaluation reproducible
- avoid fake integration
- preserve machine-readable pipeline handoffs

### 4. Cosmos Request Build
The system packages:
- scene context
- selected images
- telemetry summary
- obstacle metadata
- evaluation questions

Purpose:
- provide a stable interface to a reasoning model
- keep prompts versioned and auditable

### 5. Cosmos Reasoning Output
The reasoning layer returns structured conclusions such as:
- obstacle_detectable
- visibility_confidence
- primary_factors
- recommendation

Purpose:
- interpret perception quality at a higher semantic level

### 6. Decision Layer
The local decision adapter converts reasoning output into:
- approved_for_training
- reason_code
- next_step

Purpose:
- make the reasoning usable by downstream systems

## Why This Is a Real Pipeline
This project avoids fake integration by requiring:
- saved inputs
- saved outputs
- explicit JSON contracts
- reproducible run folders
- model output normalization
- downstream machine-readable decisions

## Current v01 Baseline
Working:
- environment restored sufficiently
- Carter present
- LiDAR detects box and surrounding geometry

Not required for v01:
- full obstacle avoidance recovery
- path reacquisition behavior
- closed-loop mobile autonomy

## v01 Success Condition
Project 08 v01 is successful if:
1. a scenario can be selected
2. a run package can be created
3. a Cosmos-style request can be generated
4. a structured response can be parsed
5. a decision artifact can be produced