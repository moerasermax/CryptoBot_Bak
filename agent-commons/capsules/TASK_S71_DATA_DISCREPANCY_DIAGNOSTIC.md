# TASK_S71_DATA_DISCREPANCY_DIAGNOSTIC

> **Status**: ACTIVE
> **Owner**: Engineer (Claude Code)
> **Priority**: CRITICAL (Integrity Risk)
> **Goal**: 診斷並修正 Dashboard 顯示與實體交易脫節之問題（Phantom Profit +1,902）。

---

## 1. 症狀描述
- **Dashboard 顯示**: `Today Realized P&L: +1,902.6478`。
- **使用者宣稱**: 自 2026-04-27 後未進行任何交易。
- **PM 初探 (SQLite)**: 
    - 執行 SQL 確認 `Positions` 表中確實存在一筆 `LINK-USDT`。
    - `RealizedPnL`: 1902.647794。
    - `ClosedAt`: 被標記為 `2026-05-04 07:36:53` (台北時間今日上午)。
    - 此單據的存在與使用者記憶發生嚴重衝突。

## 2. 待修復之技術問題 (Technical Gaps)

### 2.1 DiagnosticTool 資料庫路徑修復 (CRITICAL)
- **問題**: 執行 `dotnet run --project .../CryptoBot.DiagnosticTool probe-bingx` 時回報 `no such table: ExchangeAccounts`。
- **真因**: 診斷工具未正確指向主資料庫 `CryptoBot/cryptobot.db`。由於根目錄的空 db 已被清理，現在必須確保工具能自動定位到正確的 db 檔案。
- **要求**: 修正診斷工具的資料庫加載邏輯。

### 2.2 交易紀錄對帳 (Reconciliation)
- **要求**: 修復工具後，抓取 BingX 交易所 (Demo 模式) 過去 24 小時與 2026-04-27 至今的所有成交紀錄。
- **比對目標**: 確認這筆 `LINK-USDT` 是否真實存在於交易所。
  - **Case A: 交易所存在**: 需查明為何系統在「無人下單」的情況下平倉（是否為策略自動執行？或是時鐘漂移誤發？）。
  - **Case B: 交易所不存在**: 需查明資料庫為何會憑空產生一筆今日平倉紀錄（幽靈資料）。

## 3. 預期產出
1. **修復報告**: 說明 DiagnosticTool 的路徑修復方案。
2. **對帳 Log**: 提供 `probe-bingx` 的輸出，證明交易所端是否存在該筆交易。
3. **數據清理計畫**: 若證實為幽靈資料，提出不影響系統完整性的清理 SQL。

## 4. 驗收檢核點 (VCP)
- [ ] `probe-bingx` 成功連線並印出正確的 Account 資訊。
- [ ] 提供交易所端 2026-05-04 當日的 Trade History。

## 5. 紀律要求
- 嚴禁靜默刪除 DB 紀錄。
- 必須遵循 IRON ⑫ (UTF-8 BOM) 規範。
- 必須依據 DISCIPLINE §7 提供驗收測試計畫。
