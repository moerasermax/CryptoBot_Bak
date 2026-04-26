"""
[S69 Phase 1] Sidecar 端點 smoke test — 用 FastAPI TestClient in-process 驗，無需啟 uvicorn。

跑法：
    cd ai_ops/sidecar
    python smoke_test.py

VCP-1 對齊：驗證 study/create → suggest → tell 三段協議能正確流通並回傳建議參數。
"""
from __future__ import annotations

import sys

from fastapi.testclient import TestClient

from app import app

# Windows 終端預設 cp950 不能輸出 em-dash / emoji；對齊 DiagnosticTool/Program.cs 風格走 UTF-8。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = TestClient(app)


def main() -> int:
    # 1) healthz
    r = client.get("/healthz")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok", r.json()
    print(f"[1] healthz OK — {r.json()}")

    # 2) create study with two parameter dimensions (one int, one float)
    create_payload = {
        "direction": "maximize",
        "parameters": [
            {"name": "FastSmaPeriod", "min": 5, "max": 20, "step": 1},
            {"name": "BbStdDev", "min": 1.5, "max": 3.0, "step": 0.5},
        ],
    }
    r = client.post("/study/create", json=create_payload)
    assert r.status_code == 200, r.text
    study_id = r.json()["study_id"]
    assert isinstance(study_id, str) and len(study_id) > 0
    print(f"[2] study created — id={study_id[:8]}…")

    # 3) two suggest+tell rounds — verify parameters land on legal grid points
    legal_fast = set(range(5, 21, 1))
    legal_std = {1.5, 2.0, 2.5, 3.0}
    for round_idx in range(2):
        r = client.post(f"/study/{study_id}/suggest")
        assert r.status_code == 200, r.text
        body = r.json()
        params = body["parameters"]
        trial_id = body["trial_id"]
        assert int(params["FastSmaPeriod"]) in legal_fast, params
        assert params["BbStdDev"] in legal_std, params
        print(f"[3.{round_idx}] suggest trial_id={trial_id} params={params}")

        # tell with mock objective value (later round better, simulate learning)
        tell_payload = {"trial_id": trial_id, "value": 100.0 + round_idx * 50.0}
        r = client.post(f"/study/{study_id}/tell", json=tell_payload)
        assert r.status_code == 200, r.text
        assert r.json()["state"] == "completed"
        print(f"[3.{round_idx}] tell completed, value={tell_payload['value']}")

    # 4) error path — suggest on unknown study_id returns 404
    r = client.post("/study/nonexistent-id/suggest")
    assert r.status_code == 404, r.text
    print("[4] unknown study_id correctly 404")

    # 5) cleanup: delete study
    r = client.delete(f"/study/{study_id}")
    assert r.status_code == 200, r.text
    print(f"[5] study deleted — id={study_id[:8]}…")

    print("\n✅ SMOKE TEST PASSED — Sidecar VCP-1 protocol works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
