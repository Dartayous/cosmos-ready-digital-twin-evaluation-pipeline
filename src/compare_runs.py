from pathlib import Path
import json
import argparse


def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def load_run_data(run_dir: Path):
    response = load_json(run_dir / "responses" / "cosmos_response.json")
    decision = load_json(run_dir / "decisions" / "decision.json")
    return response, decision


def format_line(name, response, decision):
    if response is None or decision is None:
        return f"{name:25} | MISSING"

    conf = response["analysis"].get("visibility_confidence", None)
    risk = response["analysis"].get("risk_level", "N/A")
    approved = decision.get("approved_for_training", False)
    action = decision.get("next_step", "N/A")

    status = "APPROVED" if approved else "REVIEW"

    conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else "N/A"

    return f"{name:25} | conf: {conf_str} | risk: {risk:<6} | {status:<8} | {action}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", required=True)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    run_paths = sorted([p for p in runs_dir.glob(f"{args.prefix}*") if p.is_dir()])

    lines = ["# Run Comparison Report\n"]

    for run_path in run_paths:
        response, decision = load_run_data(run_path)
        lines.append(format_line(run_path.name, response, decision))

    report_text = "\n".join(lines)

    print(report_text)

    out_path = runs_dir / f"{args.prefix}_comparison.txt"
    with open(out_path, "w") as f:
        f.write(report_text)

    print(f"\nSaved comparison to: {out_path}")


if __name__ == "__main__":
    main()