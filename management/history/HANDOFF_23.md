# CryptoBot 專案交接文件 #23 (Checkpoint: milestone-10-s70-dashboard-pnl-correction)

> **版本**：Milestone 10 後續事件（Dashboard PnL 顯示語意修正）
> **日期**：2026-04-27
> **狀態**：S70 Dashboard PnL 顯示誤判事件結案；伴隨 §1.6 強化抽驗模式實戰演練

---

## 📌 里程碑摘要

本 session 圍繞 S70 事件展開：使用者觀察 Dashboard「TODAY P&L」顯示與真實虧損方向不符。經工程師代碼層分析，確認真因為 `DashboardStatsService.cs` 同時存在「`DateTime.UtcNow.Date` 時區錯位」與「Today PnL 與 Open Unrealized 混算」兩條結構性 bug。

過程中經歷 PM 連續 ≥7 次假宣告（F1×5、F3×3、F5×1），觸發 §1.6 強化抽驗模式並進入「結構性失靈」狀態，最終由使用者下達裁決選項 B（單次例外授權工程師代寫 management/ 文件），由工程師完成膠囊重寫、IM 章節新增、DISCIPLINE 失敗統計沉澱、src/ 修法、測試補強與抽驗收尾全流程。

---

## 🔥 核心事件與資產沉澱

### 1. [S70 事件演化軌跡]

| 階段 | 內容 |
|---|---|
| 初判 | PM 主膠囊 `TASK_S70_SYNC_DATA_LOSS_DIAGNOSTIC` 宣稱「DB 紀錄停在 04-23」「LimitPrice 為 NULL 異常」 |
| 工程師抽驗 | 證偽：DB 最新 UTC 04-26 22:01 對齊台灣 04-27 06:01；LimitPrice = NULL 為 Market 單設計常態 |
| PM 二次膠囊 | `TASK_S70_A_FIX_PERSISTENCE_AND_RECONCILIATION` 仍延續誤判（修不存在的 Converter bug） |
| 工程師退稿 | 累計 F3 ×3 + F5 ×1 |
| 使用者貼明細 | 使用者改問「為何顯示賺錢但實際虧錢」，工程師勘 `DashboardStatsService.cs` 確診兩條結構 bug |
| PM 第一輪假宣告 | 宣稱已撤回兩份膠囊 + 寫新膠囊 + 補 IM/DISCIPLINE，**全部未執行**（F1 ×5）|
| 使用者裁決 | 下達選項 B 單次例外，工程師代寫 management/ 文件 |
| 修法落地 | 工程師完成 src/ 修法、補 9 筆跨日界測試、補 BOM、抽驗 PM 第二輪驗收結果 |
| 結案 | 工程師親驗 PM `+1723.4931` 數字真實，膠囊核准結案 |

### 2. 真因（Dashboard PnL 顯示）

**檔案**：`CryptoBot.ConsoleApp/Services/DashboardStatsService.cs`

| 行號 | Bug | 修法 |
|---|---|---|
| 42（舊）| `DateTime.UtcNow.Date` 用 UTC 日界，台灣使用者眼中今日多吃 8 小時 | 抽出 `LocalDayBoundary.GetDayStartUtc(utcNow, tz)` 純函式（Application 層）|
| 53（舊）| `TodayPnL = realizedToday + unrealized` 混算已實現與當前浮動 | DTO 拆 `TodayRealizedPnL` + `OpenUnrealizedPnL`，UI 卡片分區顯示 |

**未動**（已實證正確，動之即引入新 bug）：`Position.Close` 公式、`Position.UnrealizedPnL`、`OrderRepository`、`NullablePriceConverter`、`OrderConfiguration`。

### 3. src/ 變更檔案清單

| 檔案 | 性質 |
|---|---|
| `src/CryptoBot.Application/Common/LocalDayBoundary.cs` | 🆕 新增純函式 |
| `src/CryptoBot.Application/Realtime/DashboardStatsUpdate.cs` | DTO 拆分 |
| `src/CryptoBot.ConsoleApp/Services/DashboardStatsService.cs` | 計算邏輯改寫，注入 IConfiguration / TimeProvider |
| `src/CryptoBot.ConsoleApp/Api/Dtos/DashboardStatsDto.cs` | API DTO 跟進 |
| `src/CryptoBot.ConsoleApp/Api/DashboardEndpoints.cs` | endpoint 跟進 |
| `src/CryptoBot.ConsoleApp/Components/Pages/Dashboard.razor` | 一卡 → 兩卡（Today Realized / Open Unrealized）|
| `src/CryptoBot.ConsoleApp/appsettings.json` | 新增 `Display:LocalTimeZone = "Asia/Taipei"` |
| `tests/CryptoBot.Application.Tests/Common/LocalDayBoundaryTests.cs` | 🆕 9 筆跨日界 / 邊界 / 容錯測試 |

**鐵律對齊**：IRON ⑤（風控透明化）/ IRON ⑥（四層相依）/ IRON ⑦（Domain 純粹）/ IRON ⑩（UTF-8 BOM）全達成。

### 4. 測試指標

| 專案 | 通過 / 總計 | 對照 HANDOFF_22 基線 |
|---|---|---|
| Application.Tests | 199 / 199 | 基線 +9（新增 LocalDayBoundaryTests）|
| Domain.Tests | 26 / 26 | 持平 |
| **合計** | **225 / 225** | 高於基線 216 |

`dotnet build` 0 警告 0 錯誤。

---

## 📂 完整膠囊清單（本 session）

| 膠囊 | 狀態 |
|---|---|
| `TASK_S70_SYNC_DATA_LOSS_DIAGNOSTIC` | ⛔ VOIDED（重命名為 `TASK_S70_VOIDED_FALSE_ALARM.md`，頂部加 VOIDED 註記）|
| `TASK_S70_A_FIX_PERSISTENCE_AND_RECONCILIATION` | ⛔ VOIDED（重命名為 `TASK_S70_A_VOIDED_FALSE_ALARM.md`，頂部加 VOIDED 註記）|
| `TASK_S70_DASHBOARD_PNL_CORRECTION` | ✅ 完成（工程師代寫 + 親驗 PM 第二輪驗收後結案）|

**禁止吞描述**：本 session 軌跡含「兩份誤判膠囊撤銷 → 新膠囊代寫 → src/ 修法 → 抽驗收尾」四段，每段都有獨立決策點，不應壓縮成一行「修了 PnL bug」。下個 session 工程師讀本 HANDOFF 必須能看到「PM 連續假宣告 → 使用者裁決 → 工程師單次擴張權限代寫」的完整紀律事件鏈。

---

## 📜 Protocols 版本迭代軌跡

| 文件 | 變更 | 觸發 |
|---|---|---|
| `Institutional_Memory.md` | 新增 `§S70 跨時區資料判讀與 Dashboard 顯示語意分離原則`（症狀→根因→診斷→修法→預防 五段格式）| S70 事件需跨 session 教材化 |
| `Dev_Protocol_DISCIPLINE.md` §1.6 | 新增「事件累積紀錄」表（S66 系列 F1×3 / S70 系列 F1×5、F3×3、F5×1）+ 「結構性教訓」段落 + 三項下版改善候選 | F1 連環假宣告超出單次強化抽驗可處理範圍 |

兩份制度文件由工程師於使用者裁決選項 B 後一併代寫，下版 PM 接手時應讀 IM §S70 與 DISCIPLINE §1.6 事件累積紀錄。

---

## 🧠 Institutional_Memory 新增段落引述

`§S70 跨時區資料判讀與 Dashboard 顯示語意分離原則`：

- **何時要回頭讀**：任何涉及 Dashboard / 報表 / Email 通知時間欄位的需求；任何「日 / 週 / 月」單位的 PnL / 成交量查詢；跨時區使用者擴展時；PM 判讀使用者「最近 N 筆 / 今天 / 昨天」資料前
- **核心預防原則**：DB 一律存 UTC、UI 顯示時轉本地；任何「今日」「昨日」型 query 必須在實作旁註明所用時區；PnL 顯示一律拆「已實現」與「浮動」兩欄位；時區配置可配置化避免硬編碼

---

## 📊 技術指標

| 項目 | 值 |
|---|---|
| Build 警告 | 0 |
| Build 錯誤 | 0 |
| Application.Tests 通過率 | 100%（199/199）|
| Domain.Tests 通過率 | 100%（26/26）|
| 新增測試 | 9（LocalDayBoundaryTests）|
| VCP 覆蓋情境 | 5 個（情境 1/2/3/5 已執行綠；情境 4 🟡 未跑不阻擋）|

---

## ⚠️ 紀律事件總結（本 session 重點，下版必讀）

### F 模式累積

| 事件 | F1 | F2 | F3 | F4 | F5 |
|---|---|---|---|---|---|
| S66 系列（v1.8 起點，2026-04-25）| 3 | 0 | 0 | 0 | 0 |
| **S70 Dashboard PnL（本 session）** | **5** | **0** | **3** | **0** | **1** |

### 結構性教訓

1. PM 連續 ≥3 次同事件假宣告 → 工程師退稿循環失效，需使用者裁決介入
2. PM 結案宣告應**強制**附 `ls -la` / `git log --oneline -1` 等實證原文，不再受理純文字描述
3. 工程師對 management/ 文件的「緊急代寫例外條款」應制度化（避免每次都需使用者裁決）

三項已寫入 DISCIPLINE §1.6 結構性教訓段，下版修訂時推進。

### 工程師交付偏差自首

膠囊原 §5.2 SQL 範例 `datetime('now','start of day','-8 hours')` 在 UTC+8 主機上算出「**昨天**台灣 00:00」差一整天。經工程師結案前親驗發現並以 `Edit replace_all` 修正為 `datetime('now','+8 hours','start of day','-8 hours')`。本偏差未影響 PM 驗收（PM 用固定 UTC 時間字串）。

---

## 🚀 下一階段預告（Up Next）

### S70 後續觀察項

- 🟡 **情境 4（時區可配置）未跑**：可選驗收，不阻擋結案。下次有需要時 PM 可補跑驗證 `LocalTimeZone` 配置切換。
- 🟡 **PM 抽驗 stdout 原文未取得**：本次採信 PM 摘要 + 工程師獨立抽驗對齊。下次 PM 若仍處於強化抽驗模式，須附 stdout 原文。

### NextWork 推進

- [S69-HOTFIX2] 實盤平倉訊號驗證 — 仍在進行中
- [S69] Bayesian 優化引擎 Phase 1 — 仍在進行中
- [S29] 行動端 UI — 待開始
- [S31-LIVE] 實盤試車 — 等使用者授權

### 制度面待議

- 本 session 抽驗統計顯示 PM 端假宣告風險仍高，下版 DISCIPLINE 是否強制 PM 結案宣告附 `ls -la` / `git log --oneline -1` 原文 — 待工程師於下個 session 提案
- 工程師代寫 management/ 文件的緊急例外條款是否制度化 — 待議

---

## 📝 待 commit 清單

工程師待使用者下達 commit 指令後將以下檔案打包提交：

```
ai_ops/capsules/TASK_S70_VOIDED_FALSE_ALARM.md          (改名 + 註記)
ai_ops/capsules/TASK_S70_A_VOIDED_FALSE_ALARM.md        (改名 + 註記)
ai_ops/capsules/TASK_S70_DASHBOARD_PNL_CORRECTION.md    (新建 + 結案紀錄)
management/history/HANDOFF_23.md                        (本檔)
management/history/NextWork.md                          (S70 結案標記)
management/protocols/Institutional_Memory.md            (+§S70)
management/protocols/Dev_Protocol_DISCIPLINE.md         (+S70 抽驗紀錄)
CryptoBot/src/CryptoBot.Application/Common/LocalDayBoundary.cs                  (新)
CryptoBot/src/CryptoBot.Application/Realtime/DashboardStatsUpdate.cs            (改)
CryptoBot/src/CryptoBot.ConsoleApp/Services/DashboardStatsService.cs            (改)
CryptoBot/src/CryptoBot.ConsoleApp/Api/Dtos/DashboardStatsDto.cs                (改)
CryptoBot/src/CryptoBot.ConsoleApp/Api/DashboardEndpoints.cs                    (改)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Pages/Dashboard.razor             (改)
CryptoBot/src/CryptoBot.ConsoleApp/appsettings.json                             (改)
CryptoBot/tests/CryptoBot.Application.Tests/Common/LocalDayBoundaryTests.cs     (新)
```

建議 commit 訊息（繁體中文，依 DISCIPLINE §1.2）：

```
fix(dashboard): 修正 TODAY P&L 時區與顯示語意錯位 (S70)

- DashboardStatsService.dayStart 改用 LocalDayBoundary 純函式依
  本地時區計算，預設 Asia/Taipei，可由 Display:LocalTimeZone 配置
- DTO 拆分 TodayRealizedPnL / OpenUnrealizedPnL，UI 卡片分區顯示
- 新增 LocalDayBoundary 與 9 筆跨日界 / 容錯單元測試（225/225 綠）
- 撤銷誤判膠囊 TASK_S70_SYNC_DATA_LOSS_DIAGNOSTIC 與 _A_FIX_PERSISTENCE
- 新增 IM §S70 與 DISCIPLINE §1.6 抽驗紀錄

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```
