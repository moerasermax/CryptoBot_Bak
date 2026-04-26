# 任務膠囊：[S59-ADD] 診斷工具架構擴張與強化

## 🎯 任務目標
將 `CryptoBot.DiagnosticTool` 從單一腳本重構為具備高擴展性的 CLI 架構，並新增策略查詢指令，以及強化下單量計算的交易所物理限制提示，以支援 PM 更精準的巡檢需求。

## 📋 首席工程師實作清單 (Chief Engineer)

### T1. 診斷架構重構 (Architecture)
- [ ] 將 `Program.cs` 中龐大的 `switch` 分支拆分為獨立的 Command 類別（例如實作一個簡單的 `IDiagnosticCommand` 介面或使用 `System.CommandLine` 等輕量模式）。
- [ ] 確保未來新增診斷指令（如 K 線校驗、訂單同步等）只需新增類別，無需大幅修改進入點。

### T2. 新增指令：`strategies` (Strategy List)
- [ ] 實作 `strategies` 指令，從資料庫讀取並列表顯示所有策略。
- [ ] **輸出欄位要求**：
    - 策略名稱 (Name)
    - 模型類型 (StrategyType)
    - 交易對與週期 (Symbol @ Interval)
    - 運行狀態 (Running/Stopped)
    - 關鍵配置 (Leverage, RiskPerTrade%, MaxConcurrentPositions)

### T3. 強化指令：`size` (Exchange Limits)
- [ ] 在 `size` 模擬計算鏈的最後，嘗試透過 `IExchangeClient` 或靜態配置獲取該幣種在交易所的「最小下單量 (MinQty / StepSize)」。
- [ ] 若 `Final Qty` 為 0，請明確標示是否因為「低於交易所最小下單限制」導致，讓 PM 一目了然。

## ✅ 驗證檢核點 (VCP)
- **[VCP-1]**：PM 執行 `dotnet run --project ../CryptoBot.DiagnosticTool -- strategies` 能成功印出表格化的策略清單。
- **[VCP-2]**：PM 執行 `size` 指令時，輸出包含交易所的 MinQty 提示。

---
**授權人**：Gemini (PM)
**日期**：2026-04-24
