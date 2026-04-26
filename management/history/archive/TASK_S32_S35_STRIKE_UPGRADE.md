# 任務膠囊：[S32-35] 業界標準化與全市場實戰掃描升級

## 🎯 任務目標
1. **精確度升級 (S32)**：在回測中引入真實槓桿與爆倉 (Liquidation) 邏輯。
2. **易用性升級 (S33/35)**：將幣種改為 Top 10 下拉選單，並將策略名稱對齊業界術語。
3. **獲利能力升級 (S34)**：實作「全市場橫掃」按鈕，產出 AI 市場機會報告。
4. **連線診斷 (S27)**：強化 IP 白名單 Log 以解決使用者 403 攔截問題。

## 📋 實作清單

### T0. 連線診斷強化 (Infrastructure)
- [ ] **IpWhitelistMiddleware.cs**：加入 `_logger.LogInformation("🛡 Whitelist Check: Client={Ip}, XFF={Xff}, AllowedCount={Count}")`。

### T1. 槓桿與爆倉模擬 (Domain/Application)
- [ ] **Domain**：新增 `LiquidationException`。
- [ ] **BacktestEngine.cs**：在 K 線主迴圈加入 `TotalEquity <= 0` 判定，觸發時強制歸零餘額並中斷回測。
- [ ] **BacktestReport.cs**：增加 `IsLiquidated` 屬性。

### T2. 業界術語與幣種下拉化 (ConsoleApp/Lab)
- [ ] **StrategyCatalog.cs**：更新 `DisplayName` 為業界術語：
    - `sma` -> **SMA Crossover**
    - `trend` -> **EMA Trend Following**
    - `mean-reversion` -> **Bollinger Reversion**
    - `rsi-bb` -> **B46 Hybrid Model**
- [ ] **BacktestLab.razor**：
    - 將 `Symbol` 改為 **Dropdown (Top 10 USDT 幣種)** + 支援手動輸入。
    - 增加「槓桿 (Leverage)」輸入框 (1x - 100x)。

### T3. 「市場橫掃」按鈕實作 (S34)
- [ ] **AiAdvisorPanel.razor**：增加一個「🚀 掃描 Top 10 市場機會」按鈕。
- [ ] **後端邏輯**：點擊後彙整這 10 個幣種的最新指標數據，生成一段給 AI 分析市場多/空機會的深度 Prompt。

## ✅ 驗證檢核點 (VCP)
- **[VCP-NGROK]**：使用者再次連線時，終端機能清楚顯示 Client IP，以便修正白名單。
- **[VCP-Liquidation]**：設定 100x 槓桿跑回測，確認報告顯示 `IsLiquidated: true` 且餘額為 0。
- **[VCP-Naming]**：確認實驗室標籤、AI 建議、實盤設定中的策略名稱 100% 統一。
- **[VCP-Sweep]**：點擊「橫掃市場」後，成功產出包含 10 個幣種技術狀態的分析 Prompt。

## 📤 交付要求
- 完成後回報「業界標準化與實戰掃描系統已就緒」。
- **必須附上 BacktestEngine 中爆倉判定邏輯的代碼片段。**
