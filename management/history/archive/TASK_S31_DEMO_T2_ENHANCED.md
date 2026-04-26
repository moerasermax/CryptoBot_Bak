# 任務膠囊：[S31-DEMO-T2] 模擬盤事件閉環與數據同步強化

## 🎯 任務目標
完成模擬盤（VST）模式下的下單、成交回報（WebSocket）到本地資料庫更新的完整閉環。確保 Dashboard 能即時反應模擬盤的交易狀態。

## 📋 實作清單

### T1. 模擬盤 WebSocket 診斷與透視 (Diagnostic First)
- [ ] **[指令擴張]**：在 `CryptoBot.DiagnosticTool` 中實作或擴充 `s31_check-ws` 指令，輸出當前連線的 WebSocket Endpoint 與 `listenKey` 狀態。
- [ ] **[斷點檢查]**：驗證 `BingXExchangeClient` 中 `UseDemoTrading` 為 `true` 時，其 `User Data Stream` 的端點 URL 是否正確指向 VST 測試網環境。

### T2. 核心邏輯修正 (Infrastructure/Application)
- [ ] **[WS 訂閱]**：確保 `BingXUserWebsocketService` 在 Demo 模式下能正確建立連線並接收 `ORDER_TRADE_UPDATE` 事件。
- [ ] **[數據映射]**：驗證 `BingXOrderUpdateMessage` 類別能正確解析模擬盤傳回的 JSON 數據，確保無欄位錯位。
- [ ] **[同步器觸發]**：確認 `OrderSynchronizer` 接收到事件後，能準確更新本地 SQLite 的訂單狀態。

### T3. 實體閉環驗證 (Validation)
- [ ] **[手動測試]**：在 Dashboard 啟動策略並手動下單，觀察 `run.out` 是否出現 `[WS] Received ORDER_TRADE_UPDATE`。
- [ ] **[數據落地]**：驗證本地資料庫狀態與交易所 UI 同步，且 Dashboard 歷史表自動更新。

## ✅ 驗證檢核點 (VCP)
- **[VCP-WS-ENDPOINT]**：診斷指令顯示已連線至正確的 VST 模擬盤端點。
- **[VCP-SYNC-OK]**：模擬盤成交後，本地資料庫與 Dashboard 歷史紀錄自動更新，無需手動刷頁。

## 📤 交付要求
- 完成後回報「S31-T2 模擬盤閉環驗證完畢」。
- **請附上 `s31_check-ws` 的執行輸出 Log。**
