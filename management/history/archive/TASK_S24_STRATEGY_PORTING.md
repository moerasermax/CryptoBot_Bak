# 任務膠囊：S24 策略實戰化 (Strategy Porting)

## 🎯 任務目標
1. **策略移植**：將 `TrendFollowing` 與 `MeanReversion` 策略邏輯正式收斂至 `IStrategy` 實作。
2. **UI 補完**：為上述策略開發專屬的 Blazor 參數表單。
3. **系統掛載**：完成策略在 `StrategyCatalog` 與 `OptimizationOrchestrator` 的註冊。
4. **效能驗證**：撰寫單元測試並執行 `/lab` 優化掃描。

## 🛠️ 技術上下文 (Full Picture)
- **憲章位階**：嚴格遵守 §2 策略插槽協議 (SOP)。
- **核心介面**：`IStrategy`、`StrategyParameterFormBase`。
- **後端註冊點**：`OptimizationOrchestrator.ResolveStrategy`。
- **前端註冊點**：`StrategyCatalog.cs`。

## 📋 實作清單
### T1. 趨勢跟蹤策略 (Trend Following)
- [ ] **邏輯校對**：檢查 `TrendFollowingStrategy.cs`，確保其使用 `TechnicalIndicators.cs` 並符合純函數要求。
- [ ] **UI 表單**：建立 `TrendFollowingParameterForm.razor`。
    - 參數：Fast EMA (5..50), Slow EMA (20..200), RSI Period (7..28), RSI Midline (40..60)。
- [ ] **註冊**：於 Catalog 與 Orchestrator 註冊。

### T2. 均值回歸策略 (Mean Reversion)
- [ ] **代碼實作**：建立 `MeanReversionStrategy.cs`。
    - 邏輯：BB 觸軌 + RSI 超買超賣。
- [ ] **UI 表單**：建立 `MeanReversionParameterForm.razor`。
    - 參數：BB Period (10..50), BB StdDev (1.5..3.0), RSI Period (7..28), Oversold (20..40), Overbought (60..80)。
- [ ] **註冊**：於 Catalog 與 Orchestrator 註冊。

### T3. 質量保證 (QA)
- [ ] **單元測試**：在 `CryptoBot.Application.Tests` 補齊這兩個策略的指標訊號測試。
- [ ] **整合測試**：利用 `/lab` 驗證 `ETH-USDT 15m` 週期下，5 Bps 滑價對策略盈虧比的磨損影響。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-UI]**：`/lab` 頁面的 Pills 列正確出現新策略，且點擊後動態組件切換正常。
- **[VCP-Functional]**：新策略在回測後能產出合理的 Leaderboard 排行。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
