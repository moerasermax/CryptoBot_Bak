# 膠囊：TASK_S70_DASHBOARD_PNL_CORRECTION

> **建立日期**：2026-04-27（工程師代寫，使用者授權選項 B 單次例外）
> **位階**：取代已撤銷的 `TASK_S70_VOIDED_FALSE_ALARM.md` 與 `TASK_S70_A_VOIDED_FALSE_ALARM.md`
> **依據**：S70 誤判事件診斷收斂，工程師對話內 §1-§4 紀錄為原文資料源

---

## 1. 動機與背景 (Context)

使用者觀察到 Dashboard「TODAY P&L」卡片顯示與真實虧損方向不符。經工程師依交易所明細手算驗證：

- 台灣時間 04-27 00:00 ~ 06:01 真實淨損益：**−1,998.51 USDT**（手算，依使用者貼出 18 筆已平倉明細）
- Dashboard 卡片顯示偏向正數或數字偏差顯著（待使用者貼 SQL 雙重驗證結果）

S70 主膠囊原描述（資料斷鏈、LimitPrice 異常）已實證為**誤判**，真因不在資料層，**在 Dashboard 顯示計算路徑**。

違反 IRON ⑤ 風控透明化精神 — 使用者讀到誤導性金額狀態屬金融系統「靜默殺手」級風險。

## 2. 根因 (Root Cause)

**檔案**：`CryptoBot/src/CryptoBot.ConsoleApp/Services/DashboardStatsService.cs`

### Bug #1 — 時區錯位（line 42）

```csharp
var dayStart = DateTime.UtcNow.Date;
```

`DateTime.UtcNow.Date` 把「今日」定義為 UTC 00:00 ~ 24:00，等同台灣時間 08:00 ~ 隔日 08:00。使用者眼中的「今日」（台灣 00:00 起）與此窗口錯位，多吃 8~16 小時。

### Bug #2 — 語意混算（line 53）

```csharp
TodayPnL: realizedToday + unrealized,
```

欄位命名為「TodayPnL」但加總邏輯為「今日已實現 + 當前所有開倉浮動」。當前開倉浮動（`Position.UnrealizedPnL`，`Position.cs:82-92`）不分今日昨日，全部 OpenPositions 加總進來。語意命名與實際內容嚴重不符。

### 不在範圍內（已實證無 bug）

| 元件 | 實證結果 |
|---|---|
| `Position.Close` 公式（`Position.cs:319-325`）| Long/Short 方向計算正確 |
| `Position.UnrealizedPnL` 公式（`Position.cs:82-92`）| 計算正確 |
| `OrderRepository.AddAsync` / `UpdateAsync` | 無 bug |
| `NullablePriceConverter` | 邏輯正確 |
| `OrderConfiguration.LimitPrice` 對應 | 配置正確 |
| WS user-data 訂單事件解析 | 與交易所明細數值對齊 |

## 3. 修法範圍 (Scope)

**只動以下檔案**：

| 檔案 | 變更性質 |
|---|---|
| `CryptoBot.ConsoleApp/Services/DashboardStatsService.cs` | 計算邏輯改寫（時區 + 拆分）|
| `CryptoBot.Application/Realtime/DashboardStatsUpdate.cs` | DTO 增刪欄位 |
| `CryptoBot.ConsoleApp/Components/Pages/Dashboard.razor` | UI 卡片分區顯示 |
| `CryptoBot.ConsoleApp/Api/DashboardEndpoints.cs` | 若 endpoint 直接序列化 DTO 則跟進 |
| `CryptoBot.Application/Realtime/DashboardPushService`（若存在）| SignalR 推送 payload 對齊 |
| `CryptoBot.ConsoleApp/appsettings.json` | 新增 `Display:LocalTimeZone` 配置鍵 |
| `tests/CryptoBot.ConsoleApp.Tests/...` 或對應測試專案 | 補跨日界單元測試 |

**禁止動**：`Position.cs`、`Order.cs`、`OrderRepository.cs`、`NullablePriceConverter.cs`、`OrderConfiguration.cs`（皆已實證正確，動之即引入新 bug）。

## 4. 修法方案 (Strategy) — 採方案 C

### Bug #1 修法：時區可配置

```csharp
// appsettings.json 加：
// "Display": { "LocalTimeZone": "Asia/Taipei" }
//
// DashboardStatsService.cs 改寫 dayStart 段落：
var tzId = _config["Display:LocalTimeZone"] ?? "Asia/Taipei";
var localTz = TimeZoneInfo.FindSystemTimeZoneById(tzId);
var nowLocal = TimeZoneInfo.ConvertTimeFromUtc(DateTime.UtcNow, localTz);
var dayStartLocal = nowLocal.Date;
var dayStartUtc = TimeZoneInfo.ConvertTimeToUtc(dayStartLocal, localTz);
// 用 dayStartUtc 查 DB
```

時區做成可配置，避免硬編碼台灣時區（未來海外使用者擴展不再撞同類雷）。

### Bug #2 修法：DTO 拆分

```csharp
// DashboardStatsUpdate.cs（舊→新）：
public sealed record DashboardStatsUpdate(
    DateTime Timestamp,
    decimal TotalEquity,
    decimal TodayRealizedPnL,    // 新：今日已實現（依本地時區界定「今日」）
    decimal OpenUnrealizedPnL,   // 新：當前所有開倉浮動（不限今日）
    int ActiveStrategyCount);

// DashboardStatsService.cs 對應變更：
return new DashboardStatsUpdate(
    Timestamp: DateTime.UtcNow,
    TotalEquity: quoteBalance + unrealized,
    TodayRealizedPnL: realizedToday,
    OpenUnrealizedPnL: unrealized,
    ActiveStrategyCount: running.Count);
```

UI 卡片分區顯示兩個獨立數字，不再合併。

### IRON 守則對齊

- IRON ⑤ 風控透明化：兩個獨立欄位 + 明確命名 = 使用者一眼看懂自己「今日落袋多少」「當前帳面浮多少」
- IRON ⑦ Domain 純粹性：時區邏輯放在 ConsoleApp（顯示層），不污染 Domain；`Position` / `Order` 不需動

## 5. 驗收計畫 (VCP)

### 5.1 前置檢查（Pre-flight）

📖 唯讀。Demo 雙保險：本驗收**不下任何真單**，亦不接 BingX REST/WS。

```
sqlite3 D:\WorkSpace\CryptoBot\CryptoBot\src\CryptoBot.ConsoleApp\cryptobot.db ".tables"
```

**期望錨點**：列出含 `Positions` 表，且工程師交付當下 `Mode=Demo`。

### 5.2 測試情境

#### 情境 1：手算對帳（SQL vs DTO）　📖 唯讀

**目的**：確認 `TodayRealizedPnL` 與 SQL 加總（依台灣時區）完全一致。

```
sqlite3 D:\WorkSpace\CryptoBot\CryptoBot\src\CryptoBot.ConsoleApp\cryptobot.db "SELECT '今日已實現' AS K, ROUND(SUM(RealizedPnL),2) AS V, COUNT(*) AS N FROM Positions WHERE ClosedAt >= datetime('now','+8 hours','start of day','-8 hours') AND ClosedAt IS NOT NULL UNION ALL SELECT '當前開倉浮動標記','見Dashboard卡片', COUNT(*) FROM Positions WHERE ClosedAt IS NULL;"
```

**期望錨點**：
- 第一行 `V` 應與 Dashboard `TodayRealizedPnL` 卡片數字**完全一致**（誤差 < 0.01）
- 第二行 N 對應當前開倉持倉數

**失敗解讀表**：

| 觀察到 | 代表 | 修法 |
|---|---|---|
| SQL `V` 與 Dashboard 卡片差距 > 0.01 | 時區轉換或邊界條件錯 | 查 `dayStartUtc` 計算 |
| 第一行 N=0 但使用者今日有交易 | 時區窗口錯，把今日交易排除掉了 | 查時區方向（+8 vs −8） |
| Dashboard 仍顯示舊 `TodayPnL` 欄位 | DTO 變更未同步推送或 UI 未跟進 | 查 DashboardPushService 與 Razor |

#### 情境 2：跨日界單元測試（mock TimeProvider）　📖 唯讀

**目的**：驗證日界邊界條件（00:00:00 起算 / 23:59:59 不算）。

工程師應在測試專案內加：
- `nowLocal = 2026-04-27 00:00:01` → 04-26 23:59:59 已平倉的不應計入
- `nowLocal = 2026-04-26 23:59:59` → 04-27 00:00:01 已平倉的不應計入
- `nowLocal = 2026-04-27 12:00:00` → 04-27 00:00:00 ~ 12:00:00 之間已平倉應**全部計入**

**期望錨點**：xunit 對應測試 case 全綠，`dotnet test` 100% pass。

#### 情境 3：DTO 欄位獨立性　📖 唯讀

**目的**：驗證新 DTO 兩欄位不再合併。

```
curl http://localhost:5000/api/dashboard/stats   (或工程師交付當下的實際路徑)
```

**期望錨點**：JSON payload 含 `todayRealizedPnL` 與 `openUnrealizedPnL` 兩個獨立鍵；**不應**再有 `todayPnL` 合併欄位。

**失敗解讀表**：

| 觀察到 | 代表 |
|---|---|
| 仍有 `todayPnL` 鍵 | DTO 改寫未完整或 endpoint 序列化未跟進 |
| 兩鍵存在但數值相加等於舊 `todayPnL` | DTO 結構對但 UI 仍合併顯示 → 查 Razor |

#### 情境 4：UI 視覺檢核　📖 唯讀

**目的**：人眼確認分區顯示正確。

操作步驟：
1. 啟動 Dashboard（`dotnet run --project CryptoBot.ConsoleApp`）
2. 瀏覽 `https://localhost:5xxx/`（實際 port 看 launchSettings）
3. 觀察 PnL 卡片區塊

**期望錨點**：
- 卡片**顯式分為兩格**或兩行：「今日已實現 PnL」與「當前未實現浮動」
- 兩數字獨立，互不合併
- 數字符號（正/負）方向直觀

**失敗解讀表**：

| 觀察到 | 代表 |
|---|---|
| 卡片仍只一格 | Dashboard.razor 未跟進 DTO 變更 |
| 兩格但數字方向錯（例：明明 −1998 顯示 +1998）| 序列化或 Razor 取錯欄位 |

#### 情境 5：時區可配置驗證 🟡（可選）　📖 唯讀

**目的**：驗證 `Display:LocalTimeZone` 改為 `UTC` 後行為退回原 UTC 日界。

操作：暫改 `appsettings.json` 為 `"LocalTimeZone": "UTC"`，重啟，觀察 `TodayRealizedPnL` 變回 UTC 日界結果。測試後改回 `Asia/Taipei`。

**期望錨點**：兩種配置下 `TodayRealizedPnL` 數字差異對應 8 小時窗口差。

### 5.3 整體驗收判定

| 結果組合 | 結論 | 動作 |
|---|---|---|
| 情境 1-4 全綠 | 可關膠囊 | PM 標註結案，工程師更新 NextWork.md |
| 情境 1 紅但 2-4 綠 | 計算邏輯有微偏 | 退稿，工程師修 dayStartUtc |
| 情境 2 紅 | 邊界條件錯 | 退稿，工程師修 `>=` / `<` 條件 |
| 情境 3 紅 | DTO / 推送鏈未對齊 | 退稿，工程師補 endpoint / Razor |
| 情境 4 紅 | UI 未跟進 | 退稿，工程師補 Razor |

## 6. 權責邊界 (Role)

- PM (Gemini)：撰寫膠囊、執行驗收計畫、回貼終端機原文供工程師判讀。**不修 src/**。
- 工程師 (ClaudeCode)：執行 src/ 修改、補測試、依 §7 提交完整驗收計畫予 PM。

## 7. 連動 IM 與 DISCIPLINE 更新

本膠囊執行時應一併讀：
- `Institutional_Memory.md §S70` — 跨時區資料判讀與 Dashboard 顯示語意分離原則
- `Dev_Protocol_DISCIPLINE.md §1.6` — S70 事件抽驗紀錄（F1×5、F3×3、F5×1）

---

## 歷史紀錄區（驗收回寫）

### 2026-04-27 — PM 第一輪驗收 + 工程師抽驗

**PM 回貼摘要**（依 PM 端終端機摘要，非 stdout 原文）：

| 情境 | 結果 | 關鍵實證 |
|---|---|---|
| Pre-flight | ✅ | TradingMode=Demo、LocalTimeZone=Asia/Taipei、Positions table count=42 |
| 1 建置 + 全測 | ✅ | dotnet build 0 警告 0 錯誤；Application.Tests 199/199；Domain.Tests 26/26 |
| 2 手算對帳 | ✅ | API `todayRealizedPnL = 1723.493088`，SQL `1723.4931`，誤差 < 0.0001；當前未平倉 0（API = SQL）|
| 3 UI 視覺檢核 | ✅ | 拆為四卡，註腳更新為 `since local 00:00` / `Mark-to-market of all open positions` |
| 5 跨日界單元測試 | ✅ | LocalDayBoundary 9 筆全綠 |
| 4（可選）時區可配置 | 🟡 未跑 | 不阻擋驗收 |

**工程師獨立抽驗紀錄**（依 §1.6 強化抽驗模式不可放棄抽驗權）：

| 抽驗項 | 工程師驗證手段 | 結果 |
|---|---|---|
| PM 報的 1723.4931 真實性 | 工程師親跑 `sqlite3 cryptobot.db "SELECT ROUND(SUM(RealizedPnL),4), COUNT(*) FROM Positions WHERE ClosedAt IS NOT NULL AND ClosedAt >= '2026-04-26 16:00:00'"` → 結果 `1723.4931 / 22` | ✅ 對齊 |
| Razor 四卡拆分 | 工程師親跑 `grep -c "Today Realized\|Open Unrealized\|since local 00:00\|Mark-to-market" Dashboard.razor` → 結果 4 | ✅ 對齊 |
| 全測試 225/225 | 工程師於修法當下親跑 `dotnet test` × 2 專案 | ✅ 一致 |
| BOM 已加 | 工程師親跑 `head -c 3 *.cs \| xxd -p` → 6 份新/改檔皆 `efbbbf` | ✅ IRON ⑩ 達成 |

**信任邊界揭示**（§1.6 透明標示）：

- PM 未提供情境 1 / 2 / 5 的 stdout 原文（僅給摘要結論與關鍵數字）。工程師依 §1.6 親跑可驗手段（sqlite3 / grep / dotnet test）做獨立抽驗，**所有可驗項目對齊**，故採信本輪 PM 摘要。
- PM 端 ConsoleApp 與 curl 結果工程師無法跨 session 重現，採信 PM 報的 `todayRealizedPnL = 1723.493088` 與 sqlite3 親驗值對齊作為間接證據。

**工程師交付偏差自首**：

- 本膠囊原 §5.2 範例 SQL `datetime('now','start of day','-8 hours')` 在 UTC+8 主機上算出「**昨天**台灣 00:00」差一整天。經工程師親驗後修正為 `datetime('now','+8 hours','start of day','-8 hours')`。本偏差未影響 PM 驗收結果（PM 改用固定 UTC 時間字串 `'2026-04-26 16:00:00'` 跑，因此對得上 +1723.49）。
- 已同步在膠囊全文以 Edit replace_all 修正所有出現位置。

### 結案判定

- 工程師結案：✅ **可關膠囊**
- 鐵律對齊：IRON ⑤（風控透明化 — 卡片分區語意明確）/ IRON ⑥（四層相依 — 純函式放 Application）/ IRON ⑦（Domain 純粹 — 未動）/ IRON ⑩（UTF-8 BOM — 已驗）皆達成
- 連動更新：`Institutional_Memory.md §S70` 與 `Dev_Protocol_DISCIPLINE.md §1.6` 已於修法前同步完成

