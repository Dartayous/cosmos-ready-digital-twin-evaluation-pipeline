# Cosmos Reasoning Request

## Run Info
- Run ID: run_0002
- Scenario ID: dim_lighting
- USD File: usd/working/warehouse_runtime_p08_v01.usda
- Capture Mode: offline_replay

## Scene Context
- Environment: warehouse
- Robot: nova_carter_drive_to_goal
- Obstacle: box
- Baseline: LiDAR indicates obstacle is present in the scene

## Image Sequence
- runs/run_0002_dim_lighting/frames/frame_0000.png
- runs/run_0002_dim_lighting/frames/frame_0001.png
- runs/run_0002_dim_lighting/frames/frame_0002.png

## Evaluation Questions
1. Is the box obstacle visually detectable in this sequence?
2. How confident are you that the obstacle remains visible enough for perception or training use?
3. What environmental factors most affect visibility in this run?
4. Would you retain this run for obstacle avoidance or perception training?

## Required JSON Output
{
  "run_id": "run_0002",
  "scenario_id": "dim_lighting",
  "model_name": "cosmos_reason_or_mock_contract",
  "analysis": {
    "obstacle_detectable": true,
    "visibility_confidence": 0.0,
    "primary_factors": ["factor_1", "factor_2"],
    "risk_level": "low|medium|high"
  },
  "recommendation": {
    "dataset_label": "good_training_example|borderline_example|reject_example",
    "action": "retain_for_training|review_manually|exclude_from_training"
  }
}
