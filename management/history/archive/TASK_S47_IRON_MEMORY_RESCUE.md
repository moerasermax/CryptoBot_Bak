# 任務膠囊：[S47-FINAL] 實驗室網格參數「鋼鐵記憶」修復

## 🎯 任務目標
徹底解決實驗室 (Lab) 切換頁面後參數消失的 Bug。確保使用者設定的每一組 Min/Max/Step 在頁面跳轉、策略切換、甚至 ngrok 斷線重連後都能 100% 恢復。

## 📋 實作清單

### T1. 狀態容器強化 (LabStateContainer.cs)
- [ ] **快取結構**：建立一個 `private readonly Dictionary<string, List<ParameterRangeDto>> _gridCache`。
- [ ] **存取方法**：實作 `SaveGridSettings(string strategyKey, List<ParameterRangeDto> ranges)` 與 `TryLoadGridSettings(string strategyKey)`。

### T2. 表單基底連動 (StrategyParameterFormBase.cs)
- [ ] **統一 Hook**：在 `NotifyChangedAsync` 觸發時，自動將當前表單的所有欄位狀態打包送進 `LabStateContainer` 的快取中。

### T3. 策略表單回填邏輯 (B46 / SMA / Trend / MeanReversion)
- [ ] **OnInitialized 覆寫**：
    - 每個表單元件啟動時，先檢查 `LabStateContainer` 是否有該策略的快取。
    - **如果有，立即覆寫本地變數 (如 _rsiPeriodMin = cachedValue)**。
    - 確保 `@bind` 綁定的就是這些被恢復的變數。

### T4. 市場參數記憶 (BacktestLab.razor)
- [ ] 除了網格參數，**Symbol (幣種)** 與 **Interval (週期)** 也要存進 `LabStateContainer`。
- [ ] 換頁回來後，Symbol 下拉選單應停留在上次選中的位置。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Steel-Memory]**：
    1. 在 Lab 選擇 SOL-15m。
    2. 修改 RSI Period 為 9 ~ 21，Step 3。
    3. 點擊導航列去 Dashboard。
    4. 點擊導航列回 Lab。
    5. **驗證**：Symbol 仍是 SOL，RSI 網格仍是 9/21/3。

## 📤 交付要求
- 完成後回報「實驗室失憶症已痊癒」。
- **請附上 B46 表單中讀取快取並回填變數的代碼片段。**
