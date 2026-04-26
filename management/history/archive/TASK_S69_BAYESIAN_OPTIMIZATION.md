# 任務膠囊：[S69] 貝氏優化引擎 — FastAPI Sidecar 整合 🧠

## 1. 任務目標 (Goal)
導入業界標配的 **貝氏優化 (Bayesian Optimization)** 以解決 Grid/Random 搜尋的盲目性。
採用 **輕量化 Python FastAPI Sidecar** 模式封裝 `Optuna` 庫。C# 執行回測，Python 提供搜尋建議，雙向透過 HTTP 通訊。

## 2. 實作清單 (Implementation List)

### 階段一：[Python Sidecar] - 輕量化大腦
- [ ] **[Setup]** 建立 `ai_ops/sidecar` 目錄，初始化 `requirements.txt` (fastapi, uvicorn, optuna)。
- [ ] **[Execution]** 實作 FastAPI 服務：提供 `study/create`, `suggest`, `tell` 端點。

### 階段二：[C# Integration] - 核心適配
- [ ] **[Execution]** `SearchMethod.cs` 補上 `Bayesian` 選項。
- [ ] **[Execution]** 實作 `BayesianSearchStrategy`：透過 HTTP 與 Sidecar 溝通。
- [ ] **[Execution]** 調整 `StrategyOptimizer`：優化器需支援貝氏優化的「邊跑邊建議」非同步模型。

### 階段三：[UI & Error Handling] - 實驗室升級
- [ ] **[UI]** `BacktestLab.razor` 增加 `Bayesian` 下拉選項。
- [ ] **[Verification]** 狀態偵測：若 Python Sidecar 未啟動，顯示「AI 引擎離線」提示。

## 3. 驗收檢核點 (VCP)
- **VCP-1 (API)**: Python Sidecar 能正確回傳建議參數。
- **VCP-2 (Convergence)**: 貝氏優化的收斂速度應顯著優於純隨機搜尋。
- **VCP-3 (UI)**: UI 能動態切換並顯示貝氏優化專用欄位。

## 4. 交付要求 (Deliverables)
- [ ] 完整 Python Sidecar 原始碼。
- [ ] C# 整合代碼與 UI 更新紀錄。

---
## 5. 驗證反饋紀錄 (History)
- 2026-04-26: 由 PM 基於 UI 功能斷層與輕量化擴充需求正式立項。
