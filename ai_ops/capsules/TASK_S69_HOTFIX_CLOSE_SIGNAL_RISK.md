# 任務膠囊：S69 平倉訊號風控攔截修復 (Hotfix)

## 📌 1. 背景與動機
使用者在實盤觀察到，當策略發出平倉訊號 (`CloseLong`，如 BB 中軌回歸) 時，會被 `RiskManager` 攔截，錯誤訊息為：
> `[RISK] Strategy [Bollinger] LINK-30m (Opt) already has 1 open positions (max 1)`

**根因分析**：
在 `src/CryptoBot.Application/Strategies/StrategyExecutor.cs` 的 `HandleSignalAsync` 中，並未區分訊號類型，一律將所有訊號送入 `OrderSizer.ComputeAsync` 與 `RiskManager.CheckBeforeOpenAsync()`。
然而 `CheckBeforeOpenAsync` 顧名思義是**開倉前**檢查，其內部會檢查當前持倉數是否已達 `MaxConcurrentPositions` (預設為 1)。對於 `CloseLong/CloseShort` 平倉訊號，由於系統目前**正持有** 1 個倉位，因此必然會因為 `Count >= Max` 而被 `RiskManager` 拒絕，導致永遠無法平倉！

## 🎯 2. 實作清單
- [ ] 修改 `CryptoBot/src/CryptoBot.Application/Strategies/StrategyExecutor.cs` (約 L316 `HandleSignalAsync`)。
- [ ] 將處理流程依據 `signal.Type` 進行分流：
  - **Open 訊號 (`OpenLong` / `OpenShort`)**：維持現有邏輯，走 `OrderSizer` 與 `RiskManager.CheckBeforeOpenAsync`。
  - **Close 訊號 (`CloseLong` / `CloseShort`)**：
    - 跳過 `OrderSizer` 與 `RiskManager` 檢查。
    - 透過 `positionRepo.GetByStrategyIdAsync` 取得當前未平倉部位。
    - 找出對應方向的部位 (CloseLong 找 Long，CloseShort 找 Short)。若找不到則 log 警告並 return。
    - 將 `qty` 設為該現有部位的 `Quantity`。
- [ ] 確保修改後不會產生編譯警告或變數未宣告錯誤 (如 `isOpenSignal` 變數重複定義)。

## 🔬 3. 驗證檢核點 (VCP)

### VCP-1: 編譯品質 (IRON §3.1)
- **指令**: `dotnet build CryptoBot/CryptoBot.sln`
- **期望輸出**: 0 警告 / 0 錯誤。

### VCP-2: 測試通過率
- **指令**: `dotnet test CryptoBot/CryptoBot.sln`
- **期望輸出**: 100% Pass。

## 📨 4. 交付要求 (致工程師)
請工程師（ClaudeCode）接手此膠囊，修改 `StrategyExecutor.cs` 後確保通過編譯與單元測試。請在回覆中附上 `🧪 PM 驗收測試計畫`，以便我執行確認綠燈。