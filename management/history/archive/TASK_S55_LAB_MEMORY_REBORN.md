# 任務膠囊：[S55-FINAL] 實驗室狀態記憶終極方案 — 領取式持久化 (SOP v1.1)

## 🎯 任務目標
徹底根除實驗室 (Lab) 換頁、換策略後參數丟失的 Bug。透過將持久化責任下放到「表單組件」自身（領取式記憶），迴避 Blazor DynamicComponent 的生命週期時序衝突。

## 📋 首席工程師實作清單 (Chief Engineer ClaudeCode)

### T1. 表單基底能力強化 (`ConsoleApp/Lab/StrategyParameterFormBase.cs`)
- [ ] **注入狀態艙**：使用 `[Inject] protected LabStateContainer State { get; set; } = default!;`。
- [ ] **新增識別參數**：新增 `[Parameter] public string StrategyKey { get; set; } = default!;`。

### T2. 各策略表單自癒實作 (`Components/Lab/`)
- [ ] **目標表單**：B46, Sma, Pa, Trend, Mean。
- [ ] **OnInitializedAsync 重構**：
    - 邏輯：在組件初始化時，立即呼叫 `State.TryGetGridSettings(StrategyKey)`。
    - 行動：若快取不為空，調用 `ApplyGridParametersAsync(cached)` 覆寫本地變數。
    - 關鍵：這必須發生在表單第一次渲染前，確保 UI 綁定的是正確的快取值而非預設值。

### T3. 父頁面路徑清理 (`Components/Pages/BacktestLab.razor`)
- [ ] **DynamicComponent 傳遞**：
    - 在 `_formParameters` 字典中注入 `[nameof(StrategyParameterFormBase.StrategyKey)] = State.SelectedModel.Key`。
- [ ] **路徑刪除**：
    - 移除 `_pendingGridRestoreKey` 標記位。
    - 清理 `OnAfterRenderAsync` 中所有依賴 `_dynamicRef.Instance` 的存檔與恢復邏輯。
- [ ] **持久化優化**：
    - 在 `OnFormGridChanged` 中，加入防護機制，避免初始化時的 `NotifyChangedAsync` 誤將預設值寫回快取。

### T4. 診斷 Log 補強
- [ ] 在表單的 `OnInitializedAsync` 與 `ApplyGridParametersAsync` 加入 `_logger.LogDebug`（若有注入 Logger），印出恢復紀錄。

## ✅ 驗證檢核點 (VCP)
- **[VCP-1] 深度導航測試**：在 Lab 修改 ADA 參數 -> 點去 Dashboard -> 點回 Lab。
- **預期結果**：參數 100% 留存，UI 顯示為修改後的值。
- **[VCP-2] 策略切換測試**：在 SMA 修改參數 -> 切到 B46 -> 切回 SMA。
- **預期結果**：SMA 的自定義網格區間完好如初。
- **[VCP-3] 邏輯一致性**：確保 `BacktestLab.razor` 內不再包含手動操作子元件實例的時序邏輯。

## 📤 交付要求
- 完成後請 **首席工程師 ClaudeCode** 回報「實驗室領取式記憶系統已就緒」。
- **必須附上 B46 表單中 OnInitializedAsync 自領取快取的代碼片段供審核。**
