# 任務膠囊：S22-UI 實驗室功能解放 (Lab Upgrade)

## 🎯 任務目標
1. **解鎖 Orchestrator**：將寫死的 `BTC-USDT`、`1h`、`InitialBalance` 等參數改為動態接收。
2. **UI 參數化**：在 `/lab` 頁面實作標的、週期、滑價、初始資金的控制項。
3. **打通全鏈路**：確保從 UI 輸入到後端成交模擬皆能正確使用新參數。

## 🛠️ 技術上下文 (Full Picture)
- **後端位置**：`CryptoBot.ConsoleApp/Services/OptimizationOrchestrator.cs`。
- **前端位置**：`CryptoBot.ConsoleApp/Components/Pages/BacktestLab.razor`。
- **基礎設施**：`BacktestSimulator` 已經具備滑價能力，只需將 Bps 參數傳入即可。

## 📋 實作清單
### T1. 後端 DTO 與邏輯重構
- [ ] 修改 `OptimizationRequest` 記錄，新增以下欄位：
    - `string Symbol`
    - `KlineInterval Interval`
    - `decimal SlippageBps`
    - `decimal InitialBalance`
- [ ] 修改 `OptimizationOrchestrator.cs`：
    - 移除 `BtcUsdt`、`Interval`、`InitialBalance` 等 `const/static` 欄位。
    - 更新 `RunAsync` 與 `RunOneBacktestAsync`，全面改用請求中的動態值。
    - 更新 `EmptyReport` 與 `BroadcastCompletedAsync` 的預設值。

### T2. 前端 UI 組件開發
- [ ] 在 `BacktestLab.razor` 的 **Window** 區塊中新增以下輸入項：
    - **Symbol**：文字輸入框（預設 "BTC-USDT"）。
    - **Interval**：下拉選單（繫結 `KlineInterval` Enum，排除 Month 等長週期）。
    - **Slippage**：數值輸入框（Bps，預設 5）。
    - **Initial Balance**：數值輸入框（USDT，預設 10,000）。
- [ ] 修改 `StrategyParameterFormBase` 及其子類別（如 `SmaParameterForm.razor`）：
    - 調整 `BuildRequest` 方法簽章，以便將 UI 上的全局參數包裝進 `OptimizationRequest`。

### T3. 安全與防錯
- [ ] 驗證：若使用者輸入的 Symbol 格式不正確，應在 UI 阻斷發送並顯示錯誤。
- [ ] 驗證：滑價數值必須為正數。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-UI]**：啟動後確認 `/lab` 頁面顯示新控制項，且預設值正確。
- **[VCP-Functional]**：手動跑一次 `ETH-USDT` 15m 的優化掃描，確認 Leaderboard 能正常產出且資料正確。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
