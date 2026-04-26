# 任務膠囊：S28 實盤資金安全鎖 (Safety Breaker)

## 🎯 任務目標
1. **日損失主動熔斷**：當日虧損達到門檻時，自動停止所有運行中的策略並發送警報。
2. **緊急停機按鈕 (Kill Switch)**：在 Dashboard 實作一鍵全平倉並停機的緊急功能。
3. **Discord 通訊落地**：實作真實的 Discord Webhook 通知服務。

## 🛠️ 技術上下文 (Full Picture)
- **熔斷核心**：`RiskManager.cs` 已有日損計算邏輯，需在 `StrategyRuntimeHostedService` 或同步器中觸發。
- **通知服務**：介面定義在 `IMarketDataStream.cs` (應考慮搬遷至獨立檔案)，實作位於 `Infrastructure/Notifications/`。
- **UI 位置**：建議在 `GlobalStatusBar.razor` 或 Dashboard 側邊欄。

## 📋 實作清單
### T1. 主動熔斷機制 (Risk Control)
- [ ] **監控擴充**：在 `StrategyRuntimeHostedService` 增加背景監控，每分鐘呼叫 `RiskManager.IsDailyLossLimitReachedAsync`。
- [ ] **熔斷動作**：若觸發熔斷：
    - 呼叫 `StopAllAsync("Daily loss limit reached")` 停止所有策略。
    - 呼叫通知服務發送 `Critical` 級別警報。
- [ ] **重啟限制**：當熔斷發生後，UI 應禁止手動重啟策略，直到跨日或由管理員重設熔斷標記。

### T2. 緊急停機 (Emergency Kill Switch)
- [ ] **API 實作**：在 `StrategyEndpoints.cs` 新增 `POST /api/strategies/kill-switch`：
    - 此端點應執行：1. 撤銷所有委託、2. 以市價平掉所有現有倉位、3. 停止所有策略。
- [ ] **UI 實作**：在 Dashboard 頂端實作紅色 `🚨 EMERGENCY KILL SWITCH` 按鈕，點擊時需彈出二次確認。

### T3. Discord 通知落地 (Infrastructure)
- [ ] **實作類**：建立 `DiscordNotificationService.cs` (Infrastructure)。
    - 使用 `HttpClient` 發送 POST 請求至 Discord Webhook URL。
    - 格式化訊息：使用 Embeds (綠色=買入, 紅色=賣出, 紫色=熔斷)。
- [ ] **配置整合**：讀取 `appsettings.json` 中的 `Discord:WebhookUrl`。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-Safety]**：手動在資料庫製造一筆今日大額虧損紀錄，啟動系統後確認策略會自動轉為 `Stopped` 且 UI 顯示熔斷警告。
- **[VCP-Discord]**：手動觸發一次成交或錯誤，確認 Discord 頻道收到精美格式化後的通知。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
