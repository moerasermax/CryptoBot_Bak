# 任務膠囊：[S32-S35-REVISED] 實戰精確度與業界標準化升級 (修正版)

## 🎯 任務目標
1. **連線偵錯 (S27-DEBUG)**：必須解決使用者手機連入 403 的問題。
2. **術語統整 (S35)**：將策略名稱對齊業界術語 (SMA/EMA/Bollinger/Hybrid)。
3. **易用性強化 (S33/34)**：實作 Top 10 幣種下拉選單與「全市場橫掃」按鈕。
4. **引擎完善 (S32)**：確保爆倉邏輯穩定運作。

## 📋 實作清單

### T0. [最高優先] 連線診斷強化 (Infrastructure)
- [ ] **IpWhitelistMiddleware.cs**：在 `InvokeAsync` 開頭加入這行：
    `_logger.LogWarning("🛡 Whitelist Check: Client={Ip}, XFF={Xff}, AllowedCount={Count}", remote, context.Request.Headers["X-Forwarded-For"].ToString(), allowed.Count);`
- [ ] **目標**：確保使用者在終端機能直接看到被攔截的真實 IP 字串。

### T1. [遺漏補齊] 業界術語大一統 (Domain/Lab)
- [ ] **StrategyCatalog.cs**：將 `DisplayName` 更新為：
    - `sma` -> **SMA Crossover**
    - `trend` -> **EMA Trend Following**
    - `mean-reversion` -> **Bollinger Reversion**
    - `rsi-bb` -> **B46 Hybrid Model**
- [ ] **同步更新**：確保 AI Advisor 的 Prompt 描述也使用這些新名稱。

### T2. [遺漏補齊] 幣種下拉化 (ConsoleApp/Lab)
- [ ] **BacktestLab.razor**：
    - 將 `Symbol` 改為 **Dropdown選單**。
    - 內建清單：`BTC-USDT`, `ETH-USDT`, `SOL-USDT`, `BNB-USDT`, `XRP-USDT`, `DOGE-USDT`, `ADA-USDT`, `AVAX-USDT`, `DOT-USDT`, `LINK-USDT`。
    - 保留一個「手動輸入」選項。

### T3. [遺漏補齊] 「橫掃市場」分析按鈕 (S34)
- [ ] **AiAdvisorPanel.razor**：增加一個「🚀 掃描 Top 10 市場機會」按鈕。
- [ ] **邏輯**：點擊後產出包含這 10 個幣種最新技術狀態的分析 Prompt 供使用者複製。

### T4. [完善] 槓桿與爆倉模擬 (Application)
- [ ] 延續上一輪 T1/T2/T3 實作，確保 `IsLiquidated` 邏輯與排行榜紅底顯示無誤。

## ✅ 驗證檢核點 (VCP)
- **[VCP-NGROK]**：使用者再次連線時，終端機能清楚顯示 Client IP（黃字 Log）。
- **[VCP-Naming]**：確認全系統策略名稱 100% 統一為業界術語。
- **[VCP-Dropdown]**：確認 Symbol 選單可正常切換且不影響回測啟動。

## 📤 交付要求
- 完成後回報「全市場實戰升級修正版已就緒」。
- **請附上 IpWhitelistMiddleware 更新後的 `InvokeAsync` 代碼片段。**
