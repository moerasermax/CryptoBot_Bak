# 任務膠囊：S22 核心技術開發 v2.0 (修正版)

## 🎯 任務目標
1. **金鑰管理健壯化**：確立資料庫唯一權威性，補齊領域模型與 Provider 測試。
2. **滑價機制校對**：維持 Infrastructure 層實作，補齊精準度模擬測試。
3. **最佳化記憶持久化**：實作 `StrategyOptimizationSettings` 實體與倉儲。

## 🛠️ 技術上下文 (Full Picture)
- **架構校正**：滑價邏輯嚴禁進入 `Application/Backtesting/BacktestEngine.cs`。它屬於交易所模擬器 (`Infrastructure`) 的職責。
- **單位統一**：全專案統一使用 `Bps` (Basis Points) 作為滑價單位。
- **測試標記**：新撰寫的測試必須加上 `[Trait("Category", "S22")]`。

## 📋 實作清單
### T1. 金鑰管理健壯化 (Security & Robustness)
- [ ] **移除 Fallback**：修改 `TryApplyDbCredentialsAtStartup` 相關邏輯，將 `appsettings.json` 的金鑰僅視為引導 (Bootstrap) 用，啟動後一律以 `IExchangeCredentialProvider` 為準。
- [ ] **領域模型測試**：在 `CryptoBot.Domain.Tests` 補齊 `ExchangeAccount` 測試（Activate 空金鑰被拒、UpdateCredentials 空字串保留原值）。
- [ ] **同步事件測試**：補齊 `DbExchangeCredentialProvider` 測試，驗證 `CredentialsChanged` 事件的同步性。

### T2. 滑價機制驗證 (Backtesting Precision)
- [ ] **文件化防錯**：在 `BacktestOptions.SlippageBps` 補上 XML 註解，警告開發者滑價已在 `BacktestSimulator` 處理，避免二次套用。
- [ ] **精準度測試**：在 `CryptoBot.Application.Tests` 補齊滑價測試，驗證 `Buy` 成交價高於 Close、`Sell` 成交價低於 Close，且誤差符合 Bps 計算。

### T3. 最佳化設定實體 (Strategy Optimization)
- [ ] **實體實作**：新增 `StrategyOptimizationSettings.cs` (Domain)，主鍵為 `(StrategyId, Symbol, KlineInterval)`。
- [ ] **倉儲實作**：新增 `IStrategyOptimizationSettingsRepository` 與 EF 實作。
- [ ] **Migration**：產出 `StrategyOptimizationSettings` 對應的資料庫遷移。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-Test]**：`dotnet test --filter Category=S22` 全部 PASS。
- **[VCP-Charter]**：驗證 `BacktestEngine` 仍保持純淨，無滑價計算邏輯。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
