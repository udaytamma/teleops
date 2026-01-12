"""Run tests with coverage and write summary results."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree


def _parse_junit(path: Path) -> dict:
    if not path.exists():
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "pass_rate": 0.0}
    tree = ElementTree.parse(path)
    root = tree.getroot()

    total = 0
    failed = 0
    skipped = 0

    for suite in root.findall("testsuite"):
        total += int(suite.attrib.get("tests", "0"))
        failed += int(suite.attrib.get("failures", "0")) + int(suite.attrib.get("errors", "0"))
        skipped += int(suite.attrib.get("skipped", "0"))

    passed = max(total - failed - skipped, 0)
    pass_rate = (passed / total) if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": round(pass_rate, 4),
    }


def _parse_coverage(path: Path) -> dict:
    if not path.exists():
        return {"percent_covered": 0.0}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "percent_covered": round(data.get("totals", {}).get("percent_covered", 0.0), 2)
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    storage_dir = root / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    junit_path = storage_dir / "junit.xml"
    cov_json = storage_dir / "coverage.json"
    cov_xml = storage_dir / "coverage.xml"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=teleops",
        f"--cov-report=json:{cov_json}",
        f"--cov-report=xml:{cov_xml}",
        f"--junitxml={junit_path}",
    ]

    result = subprocess.run(cmd, cwd=str(root))

    junit_summary = _parse_junit(junit_path)
    coverage_summary = _parse_coverage(cov_json)

    summary = {
        "status": "passed" if result.returncode == 0 else "failed",
        "coverage": coverage_summary,
        "tests": junit_summary,
    }
    (storage_dir / "test_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
