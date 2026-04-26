# CryptoBot 專案交接文件 #12 (Checkpoint: milestone-06-diagnostic-evolution)

> **版本**：Milestone 06 (Diagnostic Evolution & Precision Fix)
> **日期**：2026-04-24
> **狀態**：診斷工具專案化 · 精度解析 Bug 根除 · 憲章 v2.3 正式生效

---

## 📌 里程碑概述 (Milestone Summary)

本階段是 CryptoBot 穩定性演進的轉折點。我們不再滿足於「看見日誌」，而是實作了「自主診斷」。透過建立獨立的 `DiagnosticTool` 指令集，我們成功抓出了隱藏在執行層深處的精度解析 Bug，並將「可觀測性優先」正式立法進入憲章。

---

## 🚀 核心升級與修復戰果 (Key Achievements)

### 1. 🛠️ 診斷工具體系 (DiagnosticTool - S59 / S59-ADD)
- **架構重構**：將 `CryptoBot.DiagnosticTool` 打造為具備 Command 模式的可擴展 CLI 工具。
- **環境透視 (env)**：可即時顯示 API 模式、真實 VST/USDT 餘額與連線存活性。
- **策略清單 (strategies)**：實作 `T2_strategies` 指令，列出 DB 中所有策略的詳細配置與運行狀態。
- **下單量模擬 (size)**：實作 `S59_size` 指令，模擬完整計算鏈，並能自動對齊交易所規則，明確指出「歸零」的物理根因。

### 2. 🎯 精度解析修復 (Precision Fix - S62)
- **根因根除**：修正了 `BingXExchangeClient` 誤將「小數位數」當作「步進值」的邏輯。
- **精度轉換**：實作了 `PrecisionToStep` 轉換邏輯（$10^{-n}$），確保 BTC 等高精度幣種的 `StepSize` 正確解析為 `0.0001`。
- **價格對齊**：同步修正了 `TickSize` 解析，徹底解決了潛在的限價單拒單風險。

### 3. 📢 執行層顯性化 (S59 T1)
- **拒單透明化**：當 `OrderSizer` 因為資金不足或精度對齊導致數量歸零時，Dashboard 會立即顯示 `[SIZE]` 琥珀金警告，不再靜默失敗。

### 4. 📜 企業級雙 AI 憲章 v2.3 (Charter Evolution)
- **可觀測性優先 (§0.3)**：確立「先診斷、後修復」的 Bug 排除 SOP。
- **指令進化協議 (§10)**：規範了診斷指令的「任務編號 + 動作」命名規範（如 `s60_check-kline`），確保工具隨專案演進而積累知識。

---

## 📈 技術指標
- **測試通過率**：114 / 114 (100%)。
- **診斷覆蓋**：已涵蓋 Balance, Rules, Sizing, RiskCheck。
- **穩定性**：解決了 BTC 在特定價格下計算歸零的邊界案例。

---

## ⚠️ 待解議題 (Backlog)
- **[S31-DEMO]** 模擬盤巡檢 T2：驗證成交後的數據閉環。
- **[S60]** K 線數據斷層診斷（待辦）。
- **[S61]** 訂單同步狀態監控（待辦）。

---
_「看得見的 Bug 不是威脅，看不見的邏輯黑盒才是。」_
