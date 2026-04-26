# 任務膠囊：[S27-NGROK] 外部存取隧道與安全性加固

## 🎯 任務目標
使用 ngrok 建立安全隧道，使外部網路（公司/手機）能安全存取地端的 CryptoBot Lab，並確保系統的 IP 白名單機制能正確處理代理請求。

## 🛠️ 技術細節 (Technical Context)
- **Host**：目前的 Kestrel 綁定在 `http://*:5000`。
- **Middleware**：`IpWhitelistMiddleware` 會攔截非白名單 IP。
- **ngrok 特性**：流量會經過 ngrok 代理，地端看到的 `RemoteIpAddress` 可能是 `127.0.0.1` 或 ngrok 的內部 IP，需透過 `X-Forwarded-For` 取得真實客戶端 IP。

## 📋 實作清單

### T1. 基礎設施配置 (Infrastructure/Web)
- [ ] **ForwardedHeaders 配置**：
    - 在 `Program.cs` 中加入 `app.UseForwardedHeaders()`。
    - 配置 `ForwardedHeadersOptions`，設定 `ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto`。
    - 信任所有代理（`KnownNetworks.Clear()` 和 `KnownProxies.Clear()`），因為 ngrok 的 IP 是動態的。

### T2. 安全性與白名單調整 (Middleware)
- [ ] **IP 辨識修正**：
    - 確保 `IpWhitelistMiddleware` 讀取的是經過 `UseForwardedHeaders` 處理後的 `context.Connection.RemoteIpAddress`。
    - **[重要]**：在開發環境中，確保 `127.0.0.1` 依然在白名單內，以防止 ngrok 轉發被攔截。

### T3. 連線驗證與部署指引 (Documentation)
- [ ] **建立啟動腳本**：建立一個 `scripts/start-ngrok.ps1`，指令範例：`ngrok http 5000`。
- [ ] **更新 SETUP.md**：加入 ngrok 安裝與啟動指引。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Headers]**：在 Log 中印出 `context.Connection.RemoteIpAddress`，確認透過 ngrok 存取時，顯示的是外部 IP（而非 127.0.0.1）。
- **[VCP-Whitelist]**：將手機 IP 加入白名單後，確認能透過 ngrok URL 順利開啟 Dashboard；若移除則應回傳 403。
- **[VCP-Security]**：確認 ngrok 提供的是 HTTPS 連線。

## 📤 交付要求
- 完成後回報「ngrok 安全存取隧道已就緒」。
- **請附上 Program.cs 中 ForwardedHeaders 的配置代碼片段。**
