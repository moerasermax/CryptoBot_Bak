# 任務膠囊：[S45-S48] 策略同步修補與 AI Prompt 智慧化 (修正版)

## 🎯 任務目標
1. **修復同步 Bug (S45)**：確保「套用」後，Dashboard 的策略名稱、幣種、時區立即更新。
2. **修復記憶 Bug (S47)**：確保實驗室的網格參數在頁面切換後能 100% 恢復。
3. **優化 AI 指令 (S48)**：讓產出的 Prompt 具備模型感知能力，並引導 AI 直接給出數值。

## 📋 實作清單

### T1. Dashboard 資訊即時跳轉 (Api/SignalR)
- [ ] **LabEndpoints.cs**：在 `/apply` 邏輯結尾，確保呼叫了能觸發 UI 更新的廣播機制（如 `_controller.NotifyStrategyUpdated`）。
- [ ] **Dashboard.razor**：確認已訂閱相關事件，當策略屬性（名稱、幣種）變更時，卡片元件應自動 Refresh。

### T2. 實驗室參數深度持久化 (ConsoleApp/Lab)
- [ ] **LabStateContainer.cs**：確認 `GridSettingsCache` 是否正確儲存了 Min/Max/Step 三個維度。
- [ ] **BacktestLab.razor**：
    - 在策略 Tab 切換後，必須強制從 Cache 讀取資料。
    - 確保在 `OnMarketChangedAsync` 觸發時，不會意外清空緩存的網格設定。

### T3. AI Prompt 智慧化升級 (S48)
- [ ] **AiAdvisorPanel.razor**：
    - 修改 Prompt 生成邏輯，在開頭加入：`"【當前決策模型】：[DisplayName]"`。
    - 加入明確指令：`"請針對該模型的所有參數提供具體的優化參考值（包含 Min, Max, Step），以便我直接輸入回測系統。"`
    - 將產出的 Prompt 區塊字體調大，增加可讀性。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Realtime-Sync]**：在 Lab 套用 SOL 參數後，切回 Dashboard，卡片標題必須「瞬間」變成 SOL，不准手動重新整理。
- **[VCP-Solid-Memory]**：在 Lab 設定一組參數 -> 點去 Dashboard -> 點去 Settings -> 點回 Lab，所有數值必須完全正確。
- **[VCP-Smart-Prompt]**：點擊複製 Prompt，貼上給 AI 後，AI 應能認出目前在用哪種模型。

## 📤 交付要求
- 完成後回報「全系統同步與智慧 Prompt 已修正就緒」。
- **請附上 BuildAdvicePrompt 中加入模型名稱的代碼片段。**
