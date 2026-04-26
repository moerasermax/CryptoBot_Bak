# 任務膠囊：[S62-PRECISION] 交易所精度解析修復

## 🎯 任務目標
修正 `BingXExchangeClient` 誤將「小數位數 (Precision)」當作「最小步進值 (StepSize)」的邏輯錯誤。此錯誤導致 `OrderSizer` 在執行對齊計算時，會將所有小於 1 的下單量無條件歸零。

## 📋 首席工程師實作清單 (Chief Engineer)

### T1. BingX 精度解析邏輯修正
- **問題位置**：`src/CryptoBot.Infrastructure/Exchange/BingX/BingXExchangeClient.cs` 第 417-430 行左右。
- **修復要求**：
    - 當從 SDK 取得 `QuantityPrecision` 或 `PricePrecision` 時，應將其視為「小數位數」。
    - 實作轉換邏輯：`StepSize = (decimal)Math.Pow(10, -precision)`。
    - 例如：Precision = 4 → StepSize = 0.0001；Precision = 2 → StepSize = 0.01。
    - **注意**：優先讀取 SDK 的 `StepSize` 或 `QuantityStep` 屬性（若已有實作轉換），若無才手動計算。

### T2. 價格精度同步檢查
- 檢查 `PricePrecision` 是否也存在相同誤用。價格對齊若出錯，會導致發出的委託價不符合交易所規範而被拒絕。

## ✅ 驗證檢核點 (VCP)
- **[VCP-1] 診斷工具驗證**：
    - 執行 `dotnet run --project ../CryptoBot.DiagnosticTool -- size 78464 "[EMA] BTC-1h (Opt)"`。
    - 確認 `StepSize` 顯示為 `0.0001` (或其他符合 BTC 規範的小數)。
    - 確認 `Final Qty` 計算結果為非零正數。
- **[VCP-2] 編譯與測試**：
    - 確保全專案 0 錯 0 警。
    - `dotnet test` 通過率 100%。
