# 任務膠囊：[S42] 決策心跳與評估狀態透明化

## 🎯 任務目標
解決使用者在 Dashboard 觀察時的「盲目感」，透過視覺化的心跳與時間戳，證明策略評估邏輯正持續運行。

## 📋 實作清單

### T1. 核心狀態追蹤 (Application/Realtime)
- [ ] **StrategyState 更新**：在 `StrategyRuntimeState` 中增加 `LastEvaluatedAtUtc` 屬性。
- [ ] **觸發記錄**：在 `StrategyExecutor` 每次執行完 `AnalyzeAsync` 後，更新該時間戳並透過 `DashboardEventBus` 廣播。

### T2. Dashboard 視覺回饋 (ConsoleApp/UI)
- [ ] **心跳標籤**：在策略卡片（Active Strategy Card）中加入一列：
    `Last Evaluated: [14:05:01] (15s ago)`。
- [ ] **呼吸燈動畫**：
    - 在 `Running` 狀態旁加入一個 `.heartbeat-dot` CSS 組件。
    - 每當收到新的評估事件，執行一個 1 秒的亮綠色閃爍動畫。

### T3. WebSocket 價格連動 (UI)
- [ ] 確保卡片上的 `Current Price` 與 `Unrealized PnL` 是隨行情即時跳動的（由 WebSocket 驅動），而非等一分鐘才動一次。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Pulse]**：使用者啟動策略後，能看到「Last Evaluated」時間每分鐘準時跳動一次。
- **[VCP-Live]**：即使沒有成交，只要市場價格有變動，卡片上的價格與盈虧數字必須持續跳動。

## 📤 交付要求
- 完成後回報「決策心跳監控已上線」。
- **請附上 Heartbeat 動畫的 CSS 代碼片段。**
