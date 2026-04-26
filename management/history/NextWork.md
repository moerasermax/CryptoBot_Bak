# CryptoBot 開發任務清單 (NextWork) — Phase 5: 數據驅動與實戰試車

> **當前狀態**：Milestone 09 (Operations Resilience) 完成。
> **目標**：進入小額實盤測試 (S31-LIVE)。

---

## 🚀 執行中任務 (Active - 最高優先)

### [S69] 貝氏優化引擎 — FastAPI Sidecar 整合 🧠
- [ ] **Phase 1: Python Sidecar**：實作基於 Optuna 的 FastAPI 服務。
- [ ] **Phase 2: C# 整合**：實作 `BayesianSearchStrategy` 與非同步搜尋模型。

---

## ⏳ 待處理或延後項目 (Pending / Backlog)

### [S31-LIVE] 小額實盤試車 (GO LIVE!) 💰
- [ ] **等待使用者授權**：目前維持模擬盤，實務單測試延後執行。


---

## ✅ 已驗證項目 (Committed to Feature)
- [x] **[S68] 環境清理 — 停用種子策略機制**：已關閉 Seed 並清理 DB (Commit: 67f958e, feature branch)。 (2026-04-26)
- [x] **[S67] 優化器架構升級 — 可插拔搜尋演算法**：驗收通過並已存檔 (Commit: a4241cf, feature branch)。 (2026-04-26)
- [x] **[S66-E] 啟動期時鐘漂移 Pre-flight Check**：ASCII Banner 與 `AbortIfSkewExceedsMs` 攔截機制。 ✅ (2026-04-25)
- [x] **[S66-D] NTP 時鐘漂移防護**：NtpDriftMonitor 與 RiskManager 1000ms 熔斷防線。 ✅ (2026-04-25)
- [x] **[S66-C] 結構化日誌與 Trace ID**：全鏈路日誌透傳與 `BeginScope` 決策資產化。 ✅ (2026-04-25)
- [x] **[S66-B] 交易所狀態對帳 (Reconciliation)**：實作背景巡檢服務，解決 SQLite Guid 大小寫陷阱。 ✅ (2026-04-25)
- [x] **[S66-A-T0-EVIDENCE] 冪等防禦：errorCode 雙保險 🛡️**：實測 RawErrorCode = 101400。 ✅ (2026-04-25)
- [x] **[S66-A] 執行層冪等下單規約與防護 v1.1**：實作決定性 ID 生成。 ✅ (2026-04-25)
- [x] **[S64] 系統精煉與制度記憶持久化**：移除死碼，建立 `Institutional_Memory.md` 技術避坑指南 ✅。
- [x] **[S61-HOTFIX] 巡檢工具 SDK 存取失效修復** ✅。
- [x] **[S60] K 線數據校驗** ✅。
- [x] **[S61] 訂單狀態同步檢測** ✅。
- [x] **[S63-UX] 診斷工具中文亂碼修復** ✅。
- [x] **[S63-MTF] 多週期交易引擎升級與驗證計畫** ✅。
- [x] **[S63-HOTFIX] K 線時間軸壓縮修復** ✅。
- [x] **[S31-DEMO] 模擬盤連線與 VST 帳戶巡檢** ✅。
- [x] **[S62-PRECISION] 交易所精度解析修復** ✅。
- [x] **[S59-ADD] 診斷工具擴張與強化** ✅。
- [x] **[S59] 信號執行脫節修復** ✅。

---

## 🚀 即將開始的衝刺任務 (Up Next)

### [S29] 移動端 UI 與響應式優化 📱
- [ ] **卡片式佈局**：優化手機瀏覽器上的 Dashboard 歷史表與日誌顯示。

---

## ⚠️ 憲章紀律提醒 (憲章 v1.4)
1. **[VCP-Diagnostic]**：PM 必須先透過 DiagnosticTool 進行驗收，並將 Log 回寫膠囊。
2. **[Workflow-Pipeline]**：任務遵循「膠囊 -> 驗收 -> 暫存 -> 存檔」閉環。
3. **[Iron-L2]**：K 線 CloseTime 必須動態推算，嚴禁 UtcNow 污染。
4. **[Iron-L3]**：含中文之 .cs 檔必須補上 UTF-8 BOM。
