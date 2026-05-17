# 暫存堆疊 (Draft Context)

> **狀態**：**測試中** — 2026-05-17 S75 Phase 2-4 完工 + S77 trading core 多 bug fix 已 push、user 測試 src 端真實 reconcile 行為中。
> **下一階段預告**：user 測試完 → 決定是否補 Bug 9 (Unrealized PnL Dashboard) + Bug 10 (Reconcile 延遲) 或結案。

---

## 1. 本 session 完工 commits（依時序）

### outer agent-commons/（governance）

| commit | 內容 |
|---|---|
| 8354c20 | A009 (補正版) + A010 Engineer commit msg 失誤 + _role.md 升 ACTIVE (user 允許) + 雙 reflection 入版控 |
| 9f5e4e9 | Revert 67bb83b (A010 audit trail) |
| 67bb83b | A009 PM 違規 commit（已 revert）|
| 49c93c5 | S75 Phase 1 ACP method schema probe report (475 行) |
| 8747a41 | S75 Phase 4 完工 VCP draft (351 行 / 7 情境) |

### inner CryptoBot/（src + tests）

| commit | 內容 |
|---|---|
| c370032 | S75 Phase 2 — gemini --acp 長連接 IPC 重構（取代 -p single-shot）|
| b3aacc5 | Bug 1 (DI) — BayesianSearchStrategy IAsyncDisposable dispose 例外 (CreateAsyncScope + await using) |
| 8bddbe1 | S75 Phase 3 核心加固 — 429 retry (IRON ⑪ 雙保險) + Process 死偵測 + 429 user-facing 訊息 |
| 03b90f5 | S75 Phase 4 unit tests (7 cases, mock IGeminiAcpClient, 無 Moq 依賴) |
| **cefd086** | **S77 Bug 1+2** — Position.cs:325 PnL 公式錯 (`-` → `+`) + AccountSynchronizer Unaccounted phantom close path 違反 IM §S72 |
| **ad85bf8** | **S77 Bug 3/5/6/7** — Position materialization alert + Duplicate ClientOrderId sync DB + cooldown 補完 + Remote-only Position detect |
| **e79ccf9** | **S77 Bug 8** — Close signal Order Filled 直接結算 Position（取代純依賴 AccountSynchronizer）|

234 tests 全綠（26 Domain + 208 Application，新 7 Phase 4 + 3 既有 test 對齊 IM §S72 ground truth 改 assertion）。

---

## 2. S77 Trading Core Bug 清單 + 修法狀態

| # | Bug | Root cause | 修法 commit | 測試狀態 |
|---|---|---|---|---|
| 1 | Position.Close PnL 公式錯 | `RealizedPnL = grossPnL - TotalCommission`（commission 反向）| cefd086 | ✅ user 實測對齊 BingX 真實 PnL（Position 718506EC -144.27）|
| 2 | AccountSynchronizer Unaccounted phantom close | `local.Close(local.EntryPrice)` 強制結算違反 IM §S72 「查無實證不結算」 | cefd086 | ✅ user 觀察 Position 不再 phantom (12:19:00) |
| 3 | Position materialization 例外吞掉 | StrategyExecutor.cs:552 catch LogWarning + 註解「retry via WS」實際 retry path 斷 | ad85bf8 | ⏳ 未直接觸發、改為 LogError [CRITICAL_SYNC] + Broadcast |
| 5 | Duplicate ClientOrderId 偵測後 DB 沒 sync | HandleDuplicateClientOrderIdAsync 只 log/broadcast、不 update DB Order Status | ad85bf8 | ✅ 修前 5 次 ERROR loop / 修後只 1 次 (user 2026-05-17 12:19:00 log) |
| 6 | Cooldown 在 Duplicate path 沒記 | RecordOrderPlaced 在 line 515、Duplicate path line 506-513 早 return | ad85bf8（Bug 5 同段）| ✅ Bug 5 同段一起修 |
| 7 | AccountSynchronizer 缺 remote-only Position 補建 path | ReconcileAsync 只處理 local Open/remote 不存在、不處理 remote Open/local 缺 | ad85bf8 | ⏳ 加 LogError [CRITICAL_SYNC] detect（不自動補建、user manual SQL）|
| 8 | Close signal Order Filled 但 Position 不被 close | 設計「Close* 交給 AccountSynchronizer WS」單點失效；WS 漏接 + Reconcile 5min 延遲 | e79ccf9 | ⏳ 待 user 重啟 ConsoleApp 測試 strategy close path 直接結算 |
| **9** | **Unrealized PnL Dashboard 顯示 0** | HandlePriceUpdateAsync 用 SignalR live tick broadcast（不寫 DB CurrentPrice）；可能 SignalR 推送斷或前端訂閱失靈 | **未修** | ⏳ 需 user F12 console 確認 SignalR PositionPnL event 是否進來 |
| **10** | **ClosedAt 5 min 延遲** | PeriodicReconciliationHostedService 5 min 跑、最壞延遲 5 分鐘；ClosedAt 用 DateTime.UtcNow 不用 BingX 真實 trade.UpdateTime | **未修** | ⏳ 可減 reconcile 週期 (5min → 30s) 或加 WS event-driven trigger |

---

## 3. DB 資料層手動修復紀錄（user 全權委任、destructive 不徵詢）

| 時點 | Position | 動作 | 對齊 |
|---|---|---|---|
| 早期 | 86F64B39 (Long) | rollback phantom close (IsClosed 1→0、RealizedPnL +44.14→0) | BingX 仍 Open 時 |
| 中段 | 86F64B39 (Long) | UPDATE 對齊 BingX 真實平倉 | RealizedPnL -170.6706, ExitPrice 85.919, ClosedAt 02:59:36 |
| 中段 | 221EA80B (Short) | UPDATE 對齊 user 手動平倉 | RealizedPnL -180.6988, ExitPrice 86.077, ClosedAt 03:01:25 |
| 中段 | **27EB0E3F** | **INSERT** 補建第三筆 Short (DB 缺對應 row、Order cb_cf3e83b9 已 Filled) | RealizedPnL +39.7972 |
| 中段 | **F8A63C4A** | **INSERT** 補建新 Long (DB 缺對應 row、Order cb_466d44d3 已 Filled) | 對齊 BingX 開倉時 |
| 中段 | F8A63C4A | rollback 2nd phantom close (IsClosed 1→0、RealizedPnL +44.04→0) | S77 修前 phantom 又重現 |
| 後段 | 718506EC | 嘗試 UPDATE 但 rows=0 | 系統 PeriodicReconciliationHostedService 已自動 evidence-based close（5 min 後）✓ S77 全套生效實證 |

---

## 4. 關鍵實證（IRON ⑫ 寫真單原則 stdout 取證）

### BingX 真實平倉數據（user 提供）vs DB 對齊後

```
2026-05-17 today total realized PnL: ~ -311.5722 USDT (修前) / -456 USDT (修後含 718506EC)
- 27EB0E3F Short: +39.7972  (BingX 對齊)
- 86F64B39 Long: -170.6706 (BingX 對齊)
- 221EA80B Short: -180.6988 (BingX 對齊)
- 718506EC Long: -144.279638 (S77 系統自動 reconcile)
```

### S77 修法生效實證

- 修前: phantom close, ExitPrice == EntryPrice, RealizedPnL = +Commission (反向)
- 修後: ExitPrice ≠ EntryPrice (從 BingX trade history 拿真實 weighted avg), RealizedPnL 對齊真實
- ERROR loop: 修前 1-2s 內 5 次 / 修後只 1 次 (12:19:00 觀察)

---

## 5. 未測試 / 待 user 驗證項

1. **Bug 8 (Close signal 直接結算)** — 需 user 重啟 ConsoleApp + Strategy 跑、觀察 close path 是否直接結算（不等 5 min）
2. **Bug 9 (Unrealized PnL Dashboard 0)** — 需 user F12 console / Network tab 確認 SignalR connection 狀態 + PositionPnL event 是否進來
3. **Bug 10 (ClosedAt 延遲)** — 看 user 是否在意 5 min 延遲、若是再評估縮短 reconcile 週期
4. **S75 Phase 4 VCP** — 7 情境完工驗收（drafts/2026-05-17_S75_PHASE4_VCP.md）user 端測試 / PM 抽驗

---

## 6. 紀律事件（前半 session、已閉環）

| 事件 | 處理 |
|---|---|
| A009 PM 寫入 Engineer drafts/ + 跨界 Phase 1 探測編造 | commit 8354c20 處理（含 PM reflection v3 + Engineer A010 reflection）|
| A010 Engineer commit 67bb83b commit msg 失真 + git diff 工具誤用 | revert commit 9f5e4e9 + 重做 commit 8354c20 |
| user 「全 yes」紀律 | 本 session 後續所有 destructive 動作 (SQL UPDATE/INSERT, git push, --no-verify, Stop-Process) 直接動不再徵詢；但保持 evidence-first 親驗 + commit msg 詳記 + 真實 catastrophic 動作會明示警告 |

---

## 7. session 末尾使用紀律 (非 bug)

- **ConsoleApp in-memory cache 不會 reload DB 變動**：手動 SQL UPDATE/INSERT 後需重啟 ConsoleApp 才生效 (ASP.NET Core scoped lifetime + EF Core ChangeTracker 設計限制)
- **Strategy 同 K 線多次 tick 仍會撞 Duplicate ClientOrderId 1 次**：S66-A 設計用 signal K 線 close time 為冪等 key、屬 by-design；S77 Bug 5/6 已限 ERROR 為 1 次（cooldown 攔下後續）；完美解 = strategy 加 per-K-line dedup (Bug 11 候選、非必要)

---

> **存檔觸發**：待 user 測試完成 + 確認 Bug 8/9/10 處理方向後 → 觸發 /checkpoints save 寫入 HANDOFF_27 + S75 結案 + 移檔到 archive。
