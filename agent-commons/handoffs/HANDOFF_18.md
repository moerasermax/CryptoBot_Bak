# CryptoBot 專案交接文件 #18 (Checkpoint: milestone-09-complete)

> **版本**：Milestone 09 (Full Operations Resilience Complete)
> **日期**：2026-04-25
> **狀態**：運維韌性全系列 (S66 A-D) 完工 · 協作協議 v1.8 升級 · 實盤防線鎖死

---

## 📌 里程碑概述 (Milestone Summary)

本階段完成了本專案最重要的技術基礎建設：**運維韌性全系列 (S66)**。我們透過六張核心膠囊解決了冪等、對帳、追蹤與時鐘同步四大痛點。此外，本階段正式完成了 **DISCIPLINE 協作協議從 v1.2 到 v1.8 的重大迭代**，確立了「PM 驗收義務」與「實證先行」的最高憲章紀律。

---

## 🚀 核心升級與戰果 (Key Achievements)

### 1. 🛡️ 運維韌性六張膠囊 (S66 A-D)

- `TASK_S66A_IDEMPOTENT_ORDERING` — 實作決定性 ClientOrderId 與本地 DB Unique 索引。
- `TASK_S66A_T0_EVIDENCE` — 透過 T0 探針確診 BingX errorCode=101400，完成雙保險升級。
- `TASK_S66B_RECONCILIATION` — 部署 `OrderReconciliationService` 背景巡檢孤兒/殭屍單。
- `TASK_S66B_HOTFIX_PERSISTENCE` — **三輪誤診後**實證根因為 SQLite Guid 大小寫衝突（詳見 Institutional_Memory §S66-B-Hotfix）。
- `TASK_S66C_TRACING` — 引入 `Order.TraceId` 並透過 `BeginScope` 實現全鏈路日誌透傳。
- `TASK_S66D_NTP_DRIFT` — 實作 `NtpDriftMonitor` 與 RiskManager 1000ms 漂移攔截。

### 2. 📋 紀律與流程優化
- **手冊 v1.1**：正式將 `/checkpoints save` 與 **本地 Git Commit** 強制掛鉤，確保資產版本化。
- **實證優先**：落實「診斷工具先行、數據說話、禁止描述性括號」之鐵律。

### 3. 協作協議迭代（DISCIPLINE v1.2 → v1.8）

| 版號 | 條款 |
|---|---|
| v1.3 | §7「工程師完工交付規範 — PM 驗收測試計畫」首版 |
| v1.4-1.5 | 由 PM 主導擴增 §6「雙 AI 協作實戰流水線」、§5.2 條款迭代 |
| v1.6 | §7 條款 0「Directive Header」（致 PM 執行指令必置頂）|
| v1.7 | §5.2 條款 4「驗收測試計畫接手義務」（PM 收到 directive 必須執行）|
| v1.8 | §5.1 HANDOFF 內容規範（必含完整膠囊清單、protocols 軌跡、Institutional_Memory 引述、禁止未經實證括號）|

---

### 4. Institutional_Memory 新增段落（未來必讀）

- **§S66-A · BingX ClientOrderId 冪等回應契約**
  - **核心實證**：確診 `errorCode=101400`, `message="clientOrderID unique check failed"`。
  - **未來讀機**：升級 `JK.BingX.Net` SDK 時必跑 `probe-bingx` 健檢。

- **§S66-B-Hotfix · SQLite Guid 大小寫陷阱**
  - **根因**：EF Core 預設 Guid 為 UPPERCASE，而 SQLite TEXT 比對大小寫敏感。
  - **未來讀機**：手動 `sqlite3 INSERT` 前；遇到「rows=0 + DbUpdateConcurrencyException」時作為首位檢查項。

- **§S66-C · 全鏈路 Trace ID 與層級決策**
  - **技術深度**：採用 `_logger.BeginScope` 注入 12 位短 Hash（落實 IRON ⑥ 層級隔離；不洩漏 Serilog 直接型別至 Application 層）。
  - **未來讀機**：當膠囊要求將具體日誌庫型別跨進 Application/Domain 時。

- **§S66-D · NTP 時鐘漂移與簽章失效**
  - **核心算法**：實作「包夾測量法 (Round-trip Mid-point)」以抵消網路延遲，確保偏差計算精確。
  - **防線鎖定**：±1000ms 為 Reject 臨界點，強制 RiskManager 熔斷，防止簽章過期導致的下單連環炸。
---

## 📈 技術指標
- **測試通過率**：179/179 (100%)。
- **時鐘偏差**：實測 -947ms（落入 WARNING 區間，距 reject 線 1000ms 僅 53ms 邊界，待使用者校時）。
- **實盤準備度**：**🕒 進度 100% (Milestone 09 Ready)**。

---

## ⚠️ 下一階段預告 (Up Next)
- **[S31-LIVE] 實盤試車**：執行真實 USDT 帳戶的 5-10 USDT 首筆成交驗證。
- **[S29] UI 優化**：提升移動端 Dashboard 日誌與歷史表的呈現效果。

---
_「韌性不是不跌倒，而是在跌倒前就已經準備好了緩衝墊。」_
