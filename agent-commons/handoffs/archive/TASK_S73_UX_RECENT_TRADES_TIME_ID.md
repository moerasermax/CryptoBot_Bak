# TASK_S73_UX_RECENT_TRADES_TIME_ID

> **Status**: COMPLETED
> **Owner**: Engineer (Claude Code)
> **Priority**: NORMAL (UX Improvement)
> **Goal**: 在 Dashboard 的 "Recent Trades" 面板補上【日期時間】與【交易序號 (Trade ID)】，提升運維觀察力。

---

## 1. 需求分析 (Requirement)
- **現狀**: 目前 "Recent Trades" 僅顯示 `HH:mm:ss`，且缺乏交易所訂單編號，難以快速與交易所後台對帳。
- **目標**: 
    1. 將時間格式改為 `MM/dd HH:mm:ss`。
    2. 新增一欄顯示 `ExchangeOrderId` (交易序號)。

## 2. 實作清單 (Implementation)

### 2.1 DTO 與 API 調整
- [ ] **DTO 修改**: 在 `CryptoBot.ConsoleApp.Api.Dtos.DashboardStatsDto.cs` 的 `RecentTradeDto` 增加 `string? ExchangeOrderId` 欄位。
- [ ] **API 映射**: 修改 `CryptoBot.ConsoleApp.Api.DashboardEndpoints.cs`，在 `/api/dashboard/stats` 路由中將 `Order.ExchangeOrderId` 映射至 DTO。

### 2.2 即時推播調整
- [ ] **Payload 修改**: 在 `CryptoBot.Application.Realtime.TradeFilledUpdate.cs` 增加 `string? ExchangeOrderId`。
- [ ] **發送端修改**: 修改 `CryptoBot.Application.Strategies.StrategyExecutor.cs` 的 `HandleSignalAsync`，在廣播 `TradeFilledUpdate` 時帶入 `order.ExchangeOrderId`。

### 2.3 UI 調整
- [ ] **Snapshot 映射**: 修改 `CryptoBot.ConsoleApp.Components.Pages.Dashboard.razor` 的 `RefreshSnapshotAsync` 方法，補上 `ExchangeOrderId` 的映射邏輯。
- [ ] **表格更新**:
    - 在 `<thead>` 補上 `<th>Trade ID</th>`。
    - 在 `<tbody>` 顯示 `t.ExchangeOrderId`，並加上 `title` 屬性以利滑鼠懸停查看完整 ID。
    - 將 `Time` 欄位的格式由 `HH:mm:ss` 改為 `MM/dd HH:mm:ss`。

## 3. 預期產出
- [ ] Dashboard "Recent Trades" 表格出現 "Trade ID" 欄位。
- [ ] 時間顯示包含月/日。
- [ ] 系統編譯通過且無警告。

## 4. 驗收檢核點 (VCP)
- [ ] **UI 檢查**: 開啟 Dashboard 頁面，確認 "Recent Trades" 標題下方的表格已有新欄位且格式正確。
- [ ] **即時性檢查**: 觸發一筆模擬交易（或等待訊號），確認新成交的訂單在 UI 自動刷新後能正確顯示其 `ExchangeOrderId`。

## 5. 紀律要求
- 遵循 IRON ⑩ (UTF-8 BOM) 規範。
- 遵循 DISCIPLINE §1.1：本任務由 Engineer 執行代碼修改。
