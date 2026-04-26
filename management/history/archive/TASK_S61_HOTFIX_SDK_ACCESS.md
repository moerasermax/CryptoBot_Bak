# 任務膠囊：[S61-HOTFIX] 巡檢工具 SDK 存取失效修復

> **任務層級**：Critical (診斷鏈路修復)
> **設計準則**：棄用 dynamic、回歸靜態型別、路徑對齊。

## 🎯 任務總目標
修復 `BingXExchangeClient.GetOpenOrdersAsync` 在執行期因 `RuntimeBinderException` 導致的調用失敗。確保 `s61_sync-orders` 指令能真正讀取到交易所的掛單數據，而非因存取權限問題回傳空集合。

## 📋 實作清單
- [ ] **[根因分析]**：確認 `JK.BingX.Net` v3.10.0 的 `Trading` 實作類別是否為 `internal`，導致 `dynamic` 呼叫失效。
- [ ] **[重構實作]**：在 `BingXExchangeClient.cs` 中，將 `GetOpenOrdersAsync` 從 `dynamic` 調用改為 **靜態型別調用**。
    - 路徑：`_client.PerpetualFuturesApi.Trading.GetOpenOrdersAsync(...)`。
    - 參數：`symbol: symbol.BingXFormat, ct: ct`。
- [ ] **[回傳解析]**：確保對 `WebCallResult<IEnumerable<BingXFuturesOrder>>` 的解析邏輯正確（包含 `Success` 檢查與數據映射）。
- [ ] **[回歸測試]**：執行 `s61_sync-orders BTC-USDT`，驗證日誌不再出現「neither GetOpenOrdersAsync nor GetOrdersAsync found」警告。

## 📤 總體驗收交付物 (VCP)
- **[VCP-Diagnostic]**：執行 `s61_sync-orders` 的報告，需顯示真實的交易所掛單數量（可手動在 BingX 掛一筆單進行驗證）。
- **[VCP-Build]**：確保修改後全專案編譯 0 警告 0 錯誤。

---
📝 **最終驗收報告**
- **工程師實證**：完全移除 `dynamic` 調用，改採靜態型別鏈接 `_client.PerpetualFuturesApi.Trading.GetOpenOrdersAsync`。修正了 `BingXFuturesOrder` 的欄位映射（含 nullable 處理）。
- **地端驗收指令**：
  `dotnet run --project ../CryptoBot.DiagnosticTool -- s61_sync-orders BTC-USDT`
- **驗收狀態**：驗收通過。警告日誌消除，對帳數據恢復正常。 ✅
