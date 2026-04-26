# CryptoBot 專案交接文件 #22 (Checkpoint: milestone-10-s69-hotfixes)

> **版本**：Milestone 10 (Bayesian Optimization & Safety Resilience - Hotfixes)
> **日期**：2026-04-26
> **狀態**：修復 IAsyncDisposable 釋放漏洞與平倉訊號風控攔截。

---

## 📌 里程碑摘要 (Milestone Summary)

本階段重點在於實盤試車期間的兩大關鍵漏洞修補 (S69 Hotfixes)。首先排除了 `BayesianSearchStrategy` 資源釋放時的警告，維持 0 警告編譯基線。接著，解決了在實盤 (Demo) 環境中，策略平倉訊號 (`CloseLong` / `CloseShort`) 錯誤地被 `RiskManager` 的單位倉位上限 (`MaxConcurrentPositions`) 攔截的問題。修復後，系統已能正確於 `StrategyExecutor` 對平倉與開倉進行分流。

---

## 🔥 核心事件與資產沉澱 (Key Achievements)

### 1. [S69-HOTFIX] IAsyncDisposable 釋放漏洞修復
- **根因**：`BayesianSearchStrategy` 僅實作了 `IAsyncDisposable`，而在 `OptimizationOrchestrator` 內未使用 `CreateAsyncScope` 進行非同步釋放，導致 DI 容器發出警告。
- **處理**：工程師接手後，使用 `CreateAsyncScope()` 與 `await using` 安全地處置了 IAdaptiveSearchStrategy，警告徹底排除。

### 2. [S69-HOTFIX2] 平倉訊號風控攔截修復
- **根因**：`StrategyExecutor` 中所有訊號均送往 `RiskManager.CheckBeforeOpenAsync`，導致本應是減少持倉的 `Close` 訊號卻被「單一策略最大持倉數(1)」的規定攔截。
- **處理**：於 `HandleSignalAsync` 中引入分流機制：
  - 開倉訊號 (`isOpenSignal`)：維持原路由，走 `OrderSizer` 與 `RiskManager`。
  - 平倉訊號 (`isCloseSignal`)：繞過上述檢查，直接透過 `positionRepo` 取得該方向的未平倉持倉，將 `qty` 設為現有持有量並送出反向平倉訂單。
- **實證狀態**：PM 端已透過 `DiagnosticTool` 端對端完成預檢，並且 VCP-1 (Build) 與 VCP-2 (Test) 均綠燈 (216項全數通過)。
- **留存追蹤**：已登記於 `NextWork.md`，將透過實盤持續觀察 BingX 訂單狀態以作為最終 VCP-3 驗證。

---

### 3. Protocols 與制度迭代
- 本次透過工程師更新了 `Dev_Protocol_DISCIPLINE.md` v1.11 (增強 PM 自查表)。
- 並且於 `Institutional_Memory.md` (L6 & L7) 新增了關於 S67/S68 的架構決策紀錄。

---

### 4. 任務狀態摘要 (Capsule Status)
- `TASK_S69_HOTFIX_ASYNC_DISPOSE` — 已完成 ✅
- `TASK_S69_HOTFIX_CLOSE_SIGNAL_RISK` — 邏輯已完成，待實機終驗 🟡
- `TASK_S69_BAYESIAN_OPTIMIZATION` — **執行中 (Phase 1)** 🚀

---

## 📈 技術指標
- **代碼庫狀態**：全修復已合入 `main`。
- **建置與測試**：0 警告 / 0 錯誤，216 項測試全數通過。
- **時鐘偏差**：+51ms (🌱 SAFE)。

---

## ⚠️ 下一階段預告 (Up Next)
- **[S69-HOTFIX2] 終驗**：使用者於實盤 (Demo) 回報平倉實測結果。
- **[S69-Python]**：啟動 `ai_ops/sidecar` 專案，實作 Optuna FastAPI 服務。
- **[S29]**：準備啟動移動端 UI 與響應式優化。