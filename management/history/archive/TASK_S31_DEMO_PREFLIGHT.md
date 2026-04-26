# 任務膠囊：[S31-DEMO-PREFLIGHT] 模擬盤連線與 VST 帳戶巡檢

## 🎯 任務目標
確保系統在 `UseDemoTrading = true` 模式下能完美對接 BingX 的 VST (模擬金) 帳戶，並驗證資產讀取、下單流程與事件推播的完整性。

## 📋 實作清單

### T1. VST 帳戶 API 校對 (Infrastructure)
- [ ] **餘額獲取驗證**：確保 `GetFuturesBalanceAsync` 在 Demo 模式下，正確呼叫 BingX 模擬盤接口並回傳 VST 餘額。
- [ ] **持倉獲取驗證**：確認 `GetOpenPositionsAsync` 能讀取到模擬盤中現有的未平倉位。

### T2. 下單與事件閉環 (Exchange/Realtime)
- [ ] **WebSocket 訂閱檢查**：確認模擬盤的 `listenKey` 獲取與 `User Data Stream` 訂閱流程無誤。
- [ ] **成交回報連動**：驗證當模擬盤成交時，`OnExchangeOrderUpdate` 能正確觸發 Dashboard 的成交動畫與「交易歷史表」的即時更新。

### T3. 安全防線驗證 (Risk Management)
- [ ] **熔斷器巡檢**：確認 `SafetyBreakerMonitor` 在 Demo 環境下依然能正確讀取已實現損益，並在達到日損限額時觸發熔斷。

## ✅ 驗證檢核點 (VCP)
- **[VCP-VST-Balance]**：Dashboard 顯示的餘額與 BingX 網頁端/App 的 VST 模擬金餘額一致。
- **[VCP-Order-Flow]**：在 Dashboard 手動啟動一個策略，確認掛單能成功出現在 BingX 模擬盤交易界面。
- **[VCP-History-Sync]**：模擬成交平倉後，Dashboard 的「交易歷史表」應自動增加一列正確的紀錄。

## 📤 交付要求
- 完成後回報「模擬盤連線檢查完畢，VST 帳戶已就緒」。
- **請附上成功獲取 VST 餘額的 Log 片段作為證明。**
