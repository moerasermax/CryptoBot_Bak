# 任務膠囊：S27 多策略並發實盤部署與外網安全 (Live Deployment)

## 🎯 任務目標
1. **外網安全防護 (IP Whitelisting)**：允許系統綁定外部 IP 並實作 IP 白名單機制，阻擋非授權來源的訪問。
2. **連線健康度檢測 (HealthCheck)**：實作與交易所 REST/WS 之間的 Latency 檢測，並在 UI (StatusBar) 呈現即時連線品質。
3. **熱插拔與並發強化**：驗證並優化 `StrategyRuntimeHostedService` 在多策略同時運行 (Demo 環境) 下的資源調度與停啟穩定性。

## 🛠️ 技術上下文 (Full Picture)
- **進入點**：`CryptoBot.ConsoleApp/Program.cs` 負責 Web Host 的配置與 Middleware 管線。
- **配置檔**：`appsettings.json` 需新增 `Security:AllowedIPs` 陣列。
- **連線狀態**：可透過 `IExchangeClient` 或獨立的 HealthCheck 服務定期 Ping 交易所 API。

## 📋 實作清單
### T1. 基礎設施安全：IP 白名單 (Security)
- [ ] **配置擴充**：在 `appsettings.json` 新增 `"Security": { "AllowedIPs": [ "127.0.0.1", "::1" ] }`。
- [ ] **中介軟體實作**：建立 `IpWhitelistMiddleware.cs`，讀取配置並攔截 HTTP 請求。若來源 IP 不在白名單內，直接回傳 `403 Forbidden` 並記錄 Warning Log。
- [ ] **管線註冊**：在 `Program.cs` 註冊該 Middleware（必須在 StaticFiles 與 Routing 之前攔截）。
- [ ] **綁定開放**：在 `appsettings.json` 新增 `"Kestrel": { "Endpoints": { "Http": { "Url": "http://0.0.0.0:5000" } } }` 以允許外網連入。

### T2. 交易所連線心跳 (HealthCheck)
- [ ] **後端實作**：在 `BingXExchangeClient` 實作極輕量的 Ping/Time 端點呼叫，測量 RTT (延遲毫秒)。
- [ ] **定期採集**：透過 `BackgroundService` 或整合進現有的 `AccountSynchronizer`，每 10-15 秒採集一次延遲。
- [ ] **UI 呈現**：透過 `DashboardEventBus` 廣播，並在 `GlobalStatusBar.razor` 顯示綠/黃/紅燈與 Latency (ms)。若 WS 斷線，應顯示對應的異常狀態。

### T3. 多策略並發驗證 (Concurrency)
- [ ] **壓力測試**：建立一個 [VCP-Concurrency] 的整合測試，模擬 5 個不同參數的策略同時啟動與停止，驗證 `IStrategyRuntimeController` 的 `_mutateLock` 是否能防範 Race Condition，且不會造成死鎖。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-Security]**：本地以 `127.0.0.1` 訪問能通過，但修改白名單移除本機 IP 後，訪問立即得到 403。
- **[VCP-Network]**：UI 的 StatusBar 能看見實際的交易所 Latency 數字在跳動。
- **[VCP-Concurrency]**：新增的多策略並發測試通過。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
