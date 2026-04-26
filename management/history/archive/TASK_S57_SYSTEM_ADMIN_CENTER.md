# 任務膠囊：[S57-ADMIN] 系統管理與數據深挖中心

## 🎯 任務目標
建立一個全方位的後台管理頁面 `/admin`，實作「動態 IP 白名單管理」、「深度交易歷史回溯（含參數快照）」與「資料庫健康檢查」功能。

## 📋 首席工程師實作清單 (Chief Engineer)

### T1. 安全防禦模組 (IP Whitelist Management)
- [ ] **後端 Service**：建立 `IpWhitelistService`，負責讀取並寫回 `appsettings.json`，確保 UI 的修改在重啟後依然有效。
- [ ] **UI 介面**：顯示當前請求者的「真實 IP」（由 `X-Forwarded-For` 解析），提供「一鍵加入白名單」功能。
- [ ] **管理列表**：顯示目前所有白名單 IP，支援即時刪除。

### T2. 深度交易回溯模組 (Deep Insight)
- [ ] **數據來源**：從 `IPositionRepository` 讀取歷史持倉。
- [ ] **參數還原**：解析 `Position.ParametersSnapshot` (JSON)，將其轉化為易讀的清單（例如：`Rsi=14, Bb=2.0, Strategy=B46`）。
- [ ] **視覺化**：表格需明確區分「開倉時的模型」與「當時鎖定的網格參數」，讓使用者能精準複盤。

### T3. 資料庫與系統診斷 (DB Health)
- [ ] **統計資訊**：顯示 `cryptobot.db` 的文件大小、總交易筆數、總日誌筆數。
- [ ] **維護動作**：實作一個 `Vacuum` 按鈕，調用 SQLite 的 VACUUM 指令優化數據庫碎片。

### T4. 導航與視覺 (UI/UX)
- [ ] **路由註冊**：新增 `SystemAdmin.razor` 頁面，路由定為 `/admin`。
- [ ] **風格一致性**：沿用 S56 的琥珀金 (Risk) 與玻璃擬態 (Glass-form) 樣式。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Admin-Whitelist]**：在 UI 新增一個 IP 後，手動檢查 `appsettings.json` 是否同步更新。
- **[VCP-Admin-Snapshot]**：查看一筆舊交易，確認能完整顯示其 `StrategyType` 與當初下單時的網格 `Parameters`。
- **[VCP-Admin-DB]**：確認能正確顯示資料庫檔案大小（KB/MB）。
