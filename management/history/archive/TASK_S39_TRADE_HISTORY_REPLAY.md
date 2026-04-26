# 任務膠囊：[S39] 全方位交易歷史與 AI 複盤系統

## 🎯 任務目標
建立完整的交易紀錄追蹤機制，讓每一筆「開倉 -> 平倉」的過程都具備完整的時間、價格與參數快照，並顯示於 Dashboard，作為後續 AI 分析與策略複盤的依據。

## 📋 實作清單

### T1. 持久化層強化 (Infrastructure/Domain)
- [ ] **Position 實體更新**：確保 `Position` 表包含以下欄位：
    - `EntryPrice`, `EntryTimeUtc`
    - `ExitPrice`, `ExitTimeUtc`
    - `RealizedPnL`, `TotalCommission`
    - `ParametersSnapshot` (string/JSON)：儲存該筆交易發生時，策略所使用的參數值。
- [ ] **結算邏輯**：在 `Position.Close()` 時，必須確保上述數據 100% 寫入 SQLite。

### T2. Dashboard 歷史面板 (ConsoleApp/Pages)
- [ ] **UI 組件**：在 `Dashboard.razor` 下方新增 `TradeHistoryTable`。
- [ ] **功能要求**：
    - 顯示最近 50 筆已平倉紀錄。
    - 清楚標註該交易是屬於哪一個「業界術語模型」。
    - 盈虧以 紅/綠 色彩區分。

### T3. AI 複盤接口 (Api/UI)
- [ ] **數據導出**：在歷史列表增加「複製複盤數據」按鈕。
- [ ] **內容**：生成一段 Prompt，包含：「我是 CryptoBot。這是一筆交易紀錄：[數據]。請分析該策略在此時段的表現，並與 [其他模型名稱] 進行對比建議。」

## ✅ 驗證檢核點 (VCP)
- **[VCP-DB]**：手動在模擬盤完成一次成交，使用 SQLite 工具確認 `ParametersSnapshot` 欄位有正確存入。
- **[VCP-History]**：Dashboard 歷史列表能正確顯示該筆成交紀錄，且時間與價格準確。
- **[VCP-JSON]**：點擊複製後，輸出的數據能被 Gemini 讀懂並進行回饋。

## 📤 交付要求
- 完成後回報「全方位交易歷史與複盤系統已就緒」。
- **請附上 TradeHistoryTable 的 Razor 代碼片段。**
