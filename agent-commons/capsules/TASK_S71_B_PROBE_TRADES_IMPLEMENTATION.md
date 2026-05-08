# TASK_S71_B_PROBE_TRADES_IMPLEMENTATION

> **Status**: PENDING-ASSESSMENT
> **Priority**: CRITICAL (Evidence Collection)
> **Goal**: 實作 DiagnosticTool 之 `probe-trades` 命令，解決 S71 中「缺乏交易所實證交易紀錄」的技術斷點。

---

## 1. 需求描述 (PRD)
目前系統在對帳時發現 +1,902 的損益偏差，但 `DiagnosticTool` 僅能查掛單 (sync-orders)，無法查歷史成交。
需要新增一個工具命令，直接調用 `IExchangeClient.GetTradeHistoryAsync` 來獲取真實數據。

## 2. 技術規格 (Spec)
- **命令名稱**: `probe-trades` (別名: `trades`, `history`)
- **語法**: `probe-trades <Symbol> [DaysAgo/Date]`
- **核心邏輯**:
  1. 取得 `IExchangeClient` 實例。
  2. 呼叫 `GetTradeHistoryAsync(symbol, startTime)`。
  3. **表格化輸出**:
     - 欄位: Time (Local), Side, Qty, Price, Commission, RealizedPnL, OrderId, TradeId。
  4. **聚合計算**: 若查詢結果包含多筆成交，需在末尾輸出的「加權平均價」與「總手續費」。
- **安全約束**: 
  - 遵循 `IRON ⑩` (UTF-8 BOM)。
  - 遵循 `IRON ⑫` (寫真單原則)，輸出必須包含 Exchange 的原始 ID。

## 3. 驗收檢核點 (VCP)
- [ ] 執行 `probe-trades LINK-USDT` 不報錯且能列印表格。
- [ ] 驗證輸出時間是否正確轉換為 `Asia/Taipei`（對齊 Dashboard 語意）。
- [ ] 總量計算邏輯經人工校對正確。

## 4. 評估請求 (For Engineer)
請工程師評估：
1. `IExchangeClient.GetTradeHistoryAsync` 在當前 BingX SDK (v3.10.0) 下的穩定性。
2. 實作此命令預計耗費的 Turn 數與風險點。
