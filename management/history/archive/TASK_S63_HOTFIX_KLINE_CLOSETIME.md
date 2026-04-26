# 任務膠囊：[S63-HOTFIX] K 線時間軸壓縮修復 (Kline CloseTime Fix)

> **任務層級**：Hotfix (高優先級)
> **觸發原因**：S63 Phase 1 診斷工具 (`s63_check-mtf`) 發現 15m 與 1H 的 K 線產生 `MISALIGNED` 錯誤，且「進行中尾根」的防堵機制完全失效。

## 🎯 任務目標
修正 `BingXExchangeClient.cs` 中解析 K 線時，將所有週期的 `CloseTime` 錯誤寫死為 `AddSeconds(1)` 的重大潛在 Bug。恢復時間軸的精準度，以支撐多週期對齊與防未來函數 (`TrimInProgressTail`) 的核心機制。

## 📋 實作清單 (Chief Engineer)

### T1. 動態計算 K 線跨度
- **問題位置**：`src/CryptoBot.Infrastructure/Exchange/BingX/BingXExchangeClient.cs` 的 `GetKlinesAsync` 方法內。
- **錯誤代碼**：`var closeTime = openTime.AddSeconds(1);`
- **修復要求**：
  - 根據傳入的 `interval` (型別為 `Domain.Enums.KlineInterval`)，使用 `switch` 語句動態推算正確的 `TimeSpan`。
  - 例如：`FifteenMinutes` -> `TimeSpan.FromMinutes(15)`；`OneHour` -> `TimeSpan.FromHours(1)`。
  - 將推算出的時間跨度加上 `openTime`，作為正確的 `closeTime`。

### T2. 回歸與閉環測試
- **影響範圍確認**：這項改動會影響所有策略看到的最末根時間。由於原先只加 1 秒，現在恢復正常長度，請確認原本的單元測試是否因為依賴「1 秒收盤」而失敗。
- **測試修復**：若有單元測試（如 Mock 資料）因此亮紅燈，請同步修正測試用的 K 線生成輔助函數。

## ✅ 驗證檢核點 (VCP)
- **[VCP-1] 診斷綠燈**：再次執行 `dotnet run --project ../CryptoBot.DiagnosticTool -- s63_check-mtf BTC-USDT`，終端機輸出中不可再出現 `MISALIGNED`。
- **[VCP-2] 進行中判斷**：診斷輸出中，最新一根未收盤的 K 線必須正確顯示 `in-progress? True`，且標記為 `[IN PROGRESS — DO NOT use for signals]`。
- **[VCP-3] 測試全綠**：確保全專案的 126 個單元測試依然保持 100% 通過。

## 📤 交付要求
- 附上修正後執行 `s63_check-mtf` 顯示 `Alignment sanity -> OK` 的終端機截圖與 Log。
