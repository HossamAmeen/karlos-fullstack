#!/usr/bin/env python3
"""Builds reports/QA_REPORT.md from api-results.xml, ui-results.json, local suite
results and the hand-written findings.md."""
import json
import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path

R = Path(__file__).parent / "reports"


def api():
    rows = []
    p = R / "api-results.xml"
    if not p.exists():
        return rows
    for tc in ET.parse(p).getroot().iter("testcase"):
        status = "PASS"
        if tc.find("failure") is not None or tc.find("error") is not None:
            status = "FAIL"
        elif tc.find("skipped") is not None:
            status = "SKIP"
        rows.append((tc.get("name"), status, float(tc.get("time", 0))))
    return rows


def ui():
    rows = []
    p = R / "ui-results.json"
    if not p.exists():
        return rows

    def walk(suite, prefix=""):
        for spec in suite.get("specs", []):
            res = spec["tests"][0]["results"]
            status = "PASS" if spec["ok"] else "FAIL"
            if spec["ok"] and len(res) > 1:
                status = "FLAKY"
            rows.append((f"{prefix}{spec['title']}", status, sum(r["duration"] for r in res) / 1000))
        for sub in suite.get("suites", []):
            walk(sub, prefix + (sub["title"] + " › " if sub.get("title") and not sub["title"].endswith(".ts") else ""))

    for s in json.loads(p.read_text())["suites"]:
        walk(s)
    return rows


def table(rows):
    out = ["| Test | Result | Time (s) |", "|---|---|---|"]
    out += [f"| {n} | {s} | {t:.2f} |" for n, s, t in rows]
    return "\n".join(out)


def summary(rows):
    c = {k: sum(1 for r in rows if r[1] == k) for k in ("PASS", "FAIL", "FLAKY", "SKIP")}
    return f"{len(rows)} total — {c['PASS']} pass, {c['FAIL']} fail, {c['FLAKY']} flaky, {c['SKIP']} skipped"


a, u = api(), ui()
findings = (Path(__file__).parent / "findings.md")
text = f"""# Karlos QA Report

Generated: {dt.datetime.now():%Y-%m-%d %H:%M}

## Summary

| Suite | Result |
|---|---|
| Live API (pytest + requests) | {summary(a)} |
| Live UI (Playwright, Chrome) | {summary(u)} |

{findings.read_text() if findings.exists() else ''}

## Live API results

{table(a)}

## Live UI results

{table(u)}
"""
(R / "QA_REPORT.md").write_text(text)
print(R / "QA_REPORT.md")
