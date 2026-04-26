# 任務膠囊：[S45] 策略熱轉型與自動命名系統

## 🎯 任務目標
解決實驗室套用參數後，Dashboard 顯示名稱與模型類型未同步更新的問題。確保使用者套用優化結果後，目標策略能立即「轉型」為對應的模型並自動改名。

## 📋 實作清單

### T1. 轉型邏輯實作 (Api/Infrastructure)
- [ ] **LabEndpoints.cs**：
    - 修改 `/api/lab/apply/{strategyId}` 邏輯。
    - 取得實驗室當前所選的模型 Key (如 `bollinger`)。
    - 在更新 Config 時，同步更新目標策略的 `StrategyType`。
- [ ] **自動改名**：
    - 根據規則 `[模型名] 幣種-週期 (Optimized)` 重新生成 `Strategy.Name`。
    - 範例：`[B46 Hybrid] SOL-15m (Optimized)`。

### T2. 背景執行緒重載 (Application)
- [ ] 確保 `IStrategyRuntimeController` 在 Stop -> Start 循環後，能根據新的 `StrategyType` 正確載入對應的大腦邏輯，而非殘留舊邏輯。

### T3. Dashboard 連動 (UI)
- [ ] 確保套用成功後，Dashboard 的卡片名稱與模型標籤立即跳轉，無需手動刷新。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Morph]**：在 Lab 選擇 `SMA` 策略優化並套用，確認 Dashboard 原本的策略卡片，模型標籤從 `SMA` 變成了 `Bollinger` (或其他選定模型)。
- **[VCP-Rename]**：確認卡片標題已自動包含新的模型名稱，證明套用確實生效。

## 📤 交付要求
- 完成後回報「策略熱轉型與自動命名系統已就緒」。
- **請附上 LabEndpoints 更新名稱生成邏輯的代碼片段。**
