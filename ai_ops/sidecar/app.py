"""
CryptoBot [S69] Bayesian Optimization Sidecar — FastAPI + Optuna

C# 端的 BayesianSearchStrategy (Phase 2) 透過 HTTP 與本服務溝通：
1. POST /study/create — 建立 Optuna study，回傳 study_id
2. POST /study/{study_id}/suggest — 由 TPE sampler 推薦下一組參數
3. POST /study/{study_id}/tell — 回報該 trial 的目標值（NetPnL），讓 sampler 學習

啟動：
    cd ai_ops/sidecar
    pip install -r requirements.txt
    uvicorn app:app --host 127.0.0.1 --port 5301

Smoke test：
    curl -X POST http://127.0.0.1:5301/healthz
    curl -X POST http://127.0.0.1:5301/study/create -H "Content-Type: application/json" \
         -d '{"parameters":[{"name":"FastSmaPeriod","min":5,"max":20,"step":1}]}'

設計決策：
- in-memory study store — sidecar 進程生命週期 = study 生命週期。C# 端負責每次 optimize
  job 開頭 create、結束讓 study 隨進程關閉自然回收。Optuna 雖支援 SQLite 持久化，但
  本場景 study 是「一次性」工具，引入 DB 反而增加部署複雜度與 IRON §② 風險面。
- direction='maximize' 預設 — 對齊 StrategyOptimizer.RunAsync 排序鍵 (NetPnL desc)。
- TPESampler 為 Optuna 預設貝氏推薦演算法；非 GP 派 (避免額外科學計算依賴)，足以擊敗 Random。
- trial 物件存放於 _trials_by_study：study.ask() 之後不能直接拿 trial.number 反查 Trial 物件，
  必須我們自己存。tell 完即從快取移除避免無限增長。
"""
from __future__ import annotations

import uuid
from typing import Literal

import optuna
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Optuna 預設每 ask/tell 都吐 INFO log；高頻優化下噪音過大，調到 WARNING 即可。
optuna.logging.set_verbosity(optuna.logging.WARNING)

app = FastAPI(title="CryptoBot Bayesian Optimizer Sidecar", version="0.1.0")

# study_id → (Study, {trial_number: Trial}) — Trial 物件需自存以便 tell 階段反查。
_studies: dict[str, tuple[optuna.Study, dict[int, optuna.trial.Trial]]] = {}


class ParameterSpec(BaseModel):
    name: str
    min: float
    max: float
    # gt=0 與 C# 端 ParameterRange.Enumerate 的「Step must be positive」契約一致。
    step: float = Field(gt=0)


class StudyCreateRequest(BaseModel):
    study_name: str | None = None
    direction: Literal["maximize", "minimize"] = "maximize"
    parameters: list[ParameterSpec]


class StudyCreateResponse(BaseModel):
    study_id: str


class SuggestResponse(BaseModel):
    trial_id: int
    parameters: dict[str, float]


class TellRequest(BaseModel):
    trial_id: int
    value: float


class TellResponse(BaseModel):
    state: Literal["completed", "pruned", "failed"]


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {"status": "ok", "studies": len(_studies)}


@app.post("/study/create", response_model=StudyCreateResponse)
def study_create(req: StudyCreateRequest) -> StudyCreateResponse:
    if not req.parameters:
        raise HTTPException(status_code=400, detail="parameters must not be empty")

    study_id = str(uuid.uuid4())
    study = optuna.create_study(
        study_name=req.study_name or study_id,
        direction=req.direction,
        sampler=optuna.samplers.TPESampler(),
    )
    # 把參數規格 attach 到 study 自身（user_attrs），後續 suggest 端不必另存映射。
    study.set_user_attr("parameters", [p.model_dump() for p in req.parameters])
    _studies[study_id] = (study, {})
    return StudyCreateResponse(study_id=study_id)


@app.post("/study/{study_id}/suggest", response_model=SuggestResponse)
def study_suggest(study_id: str) -> SuggestResponse:
    entry = _studies.get(study_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"study {study_id} not found")
    study, trials = entry
    specs = study.user_attrs["parameters"]

    trial = study.ask()
    suggested: dict[str, float] = {}
    for spec in specs:
        name, lo, hi, step = spec["name"], spec["min"], spec["max"], spec["step"]
        # 整數步進 + 整數邊界 → suggest_int（與 C# 端 SMA period 等整數參數對齊）；
        # 其餘走 suggest_float (含 step) 維持與 ParameterRange.Enumerate 同樣的離散合法點集合。
        if step.is_integer() and lo.is_integer() and hi.is_integer():
            value: float = float(trial.suggest_int(name, int(lo), int(hi), step=int(step)))
        else:
            value = float(trial.suggest_float(name, lo, hi, step=step))
        suggested[name] = value

    trials[trial.number] = trial
    return SuggestResponse(trial_id=trial.number, parameters=suggested)


@app.post("/study/{study_id}/tell", response_model=TellResponse)
def study_tell(study_id: str, req: TellRequest) -> TellResponse:
    entry = _studies.get(study_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"study {study_id} not found")
    study, trials = entry
    trial = trials.pop(req.trial_id, None)
    if trial is None:
        raise HTTPException(
            status_code=404,
            detail=f"trial {req.trial_id} not found in study {study_id}",
        )

    study.tell(trial, req.value)
    return TellResponse(state="completed")


@app.delete("/study/{study_id}")
def study_delete(study_id: str) -> dict[str, str]:
    if _studies.pop(study_id, None) is None:
        raise HTTPException(status_code=404, detail=f"study {study_id} not found")
    return {"status": "deleted"}
