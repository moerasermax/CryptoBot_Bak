# 任務膠囊：[S32] 槓桿動態化與爆倉模擬系統

## 🎯 任務目標
在回測引擎中引入真實的槓桿模擬與爆倉 (Liquidation) 邏輯。讓使用者能自由調整槓桿倍率，並在回測報告中準確反映出高槓桿帶來的破產風險。

## 🛠️ 技術上下文 (Full Picture)
- **核心邏輯**：爆倉發生於「浮動虧損 >= 初始保證金 * (1 - 維持保證金率)」。在回測中，我們簡化為「權益 (Equity) <= 0」時即觸發爆倉。
- **影響範圍**：`BacktestSimulator` (保證金管理)、`BacktestEngine` (狀態中斷)、`BacktestReport` (標註爆倉結果)。

## 📋 實作清單
### T1. 引擎層：爆倉邏輯實作 (Infrastructure)
- [ ] **權益監控**：在 `BacktestSimulator` 的每次 `OnPriceUpdate` (逐根 K 線) 巡檢中，計算當前浮動損益後的 `TotalEquity`。
- [ ] **觸發爆倉**：若 `TotalEquity <= 0`：
    - 將 `TotalEquity` 強制歸零。
    - 拋出或回傳一個特定的 `LiquidationException` 或狀態碼。
    - 立即中止該次回測流程，不再處理後續 K 線。
- [ ] **手續費考量**：確保開倉與平倉手續費已正確扣除，這會加速爆倉的發生。

### T2. 報告層：爆倉狀態標註 (Application)
- [ ] **DTO 擴展**：在 `BacktestReport` 增加 `IsLiquidated` (bool) 欄位。
- [ ] **排行榜優化**：在 `OptimizationOrchestrator` 中，若某組參數發生爆倉，其 `NetPnL` 應固定為 `-100%`，並在排行榜中排在最後。

### T3. UI 層：槓桿調節與顯示 (ConsoleApp / Lab)
- [ ] **UI 欄位**：在 `/lab` 的全局參數區塊增加「槓桿 (Leverage)」輸入框 (1x - 100x)。
- [ ] **爆倉視覺化**：在 Leaderboard 列表與 Equity Curve 圖表中，若發生爆倉，背景應顯示為紅色或標註 `[LIQUIDATED]` 字樣。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Liquidation]**：設定 100x 槓桿跑一個波動劇烈的時段，確認回測報告顯示 `IsLiquidated: true` 且最終餘額為 0。
- **[VCP-Accuracy]**：確認 1x 槓桿的回測結果與舊版本（無爆倉邏輯）保持一致（除非虧損 100%）。
- **[VCP-UI]**：在 Lab 頁面調整槓桿，確認 `OptimizationRequest` 已帶上正確的倍率。

## 📤 交付要求
- 完成後回報「槓桿與爆倉模擬系統已就緒」。
- **必須附上 BacktestSimulator 核心爆倉判斷的代碼片段。**
