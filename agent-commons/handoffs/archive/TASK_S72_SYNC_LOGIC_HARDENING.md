# TASK_S72_SYNC_LOGIC_HARDENING

> **Status**: COMPLETED
> **Owner**: Engineer (Claude Code)
> **Priority**: CRITICAL (Data Integrity)
> **Goal**: 修正同步邏輯漏洞，清理幽靈損益 (+1,902)，處理殭屍 Partial 單，落實實證對帳。

---

## 1. 根因分析 (Root Cause)
- **事件**: 2026-05-04 系統啟動對帳時，`AccountSynchronizer` 偵測到本地 LINK-USDT 空單在交易所已消失。
- **錯誤行為**: 同步器未查詢歷史成交紀錄，直接以當前市價 (~9.301) 虛擬平倉。
- **結果**: 產生了 +1,902.6 的虛假獲利，且無對應 Order 紀錄。
- **併發症**: 發現存在殭屍 `PartiallyFilled` 訂單，導致對帳邏輯需進一步加固。

## 2. 待修復之技術問題 (Technical Gaps)

### 2.1 幽靈數據清理 (Data Cleanup)
- **SQL 修正**: 針對 ID `99A3E51D-257E-4F42-B856-40B572F5C506`：
    - `RealizedPnL` 設為 `"0"` (因無成交 Order 可證實損益，採取歸零止損)。
    - `ClosedAt` 修正為真實成交 UTC 時間：`2026-04-27 01:03:02` (依 IM §S70 規範)。
- **審計痕跡**: 執行 SQL 的同時，必須於 `Institutional_Memory.md` 新增 §S72 條目，記錄此次數據修正的根因與 SQL。

### 2.2 同步邏輯加固 (AccountSynchronizer Refactoring)
- **禁止盲猜價格**: 移除對帳時使用 `GetCurrentPrice` 關閉部位的邏輯。
- **實證對帳流程**:
    1. 若部位消失，必須嘗試透過 `GetTradeHistoryAsync` 尋找成交證據。
    2. 若找到證據，依證據結算。
    3. 若查無證據（如 phantom 案例），採用「隱式約定」：設 `IsClosed=1` 且 `RealizedPnL="0"`，並在 Log 中標註為 `Unaccounted`。本次**不執行** schema 變更 (PositionStatus)，維持最小衝擊。
- **殭屍單處理 (Zombie Order Cleanup)**:
    - `ReconcileAsync` 升級為週期性任務 (若尚未實現)。
    - 實作 `RefreshOrderStatusAsync`，針對長時間停留在 `PartiallyFilled` 且交易所已無效的訂單，強制於本地結案或補殺，防止占用風控額度。

### 2.3 通知與廣播 (Reporting)
- **雙軌通知**: 發生對帳自動補正時，必須同時執行：
    - `IRealtimeBroadcaster` 廣播 `[CRITICAL_SYNC]` 事件。
    - `ILogger` 輸出 `LogLevel.Error` 包含詳細補正資訊。
    - (Discord 通知因目前 Disabled，留待未來擴充)

## 3. 預期產出
1. **修復 SQL 與 IM §S72 更新**: 提供完成修正後的 Institutional Memory 內容。
2. **重構說明**: 說明 `AccountSynchronizer` 如何從「盲猜」轉向「實證」。
3. **殭屍單處理方案**: 說明如何解決 PartiallyFilled 的滯留問題。

## 4. 驗收檢核點 (VCP)
- [ ] 存取 `/api/dashboard/stats` 或執行 SQL 指令，確認 `TodayRealizedPnL` 已排除該筆 +1,902。
- [ ] 代碼自查：確認 `GetCurrentPrice` 已不被用於對帳平倉路徑。
- [ ] 模擬對帳：提供 log 證明同步器在查無歷史成交時，會正確發出 `[CRITICAL_SYNC]` 並將損益歸零。

## 5. 紀律要求
- 遵循 IRON ⑫ (UTF-8 BOM) 規範。
- 嚴禁靜默修改資料庫。
