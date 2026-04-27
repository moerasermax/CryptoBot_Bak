# 暫存堆疊 (Draft Context)

## 最新進度 (Current Progress)
- **[存檔與交接]**：已執行 Checkpoint 儲存，生成 `HANDOFF_22.md` (Milestone 10 S69 Hotfixes) 並已 Commit 到 `main` 分支。

## 工程師交付後的改進清單 — 待 PM 裁決開膠囊（2026-04-26 由 ClaudeCode 提交）

### 🔴 高優先（可合併為一張 `TASK_S69_HOTFIX_CLOSE_SIGNAL_POLISH`，純強化、不擴功能）

1. **`StrategyExecutor.cs` L378-461 縮排錯位**
   - 症狀：原 `if (qty.Value <= 0) { ... }` 與 risk-check 區塊內容仍為 12-space 縮排，但邏輯上現已被包進 `else { ... }` 內，應為 16-space。
   - 影響：編譯與行為皆正確，但下個工程師讀到會誤判作用域。屬技術債型醜陋。
   - 修法：純格式化，無語意變動。

2. **`[CLOSE] No open <Side> position` 缺通知雙軌**
   - 症狀：`[SIZE]` / `[RISK]` 都走「`_notifications.NotifyAsync` + `_broadcaster.BroadcastStrategyEvaluationFailedAsync`」雙軌，但本次新增的 `[CLOSE]` 只接廣播半邊。
   - 影響：違反 IRON §⑤ 風控透明化「不靜默失敗」精神對稱性 — Discord toast 收不到平倉異常。
   - 修法：補一段 `_notifications.NotifyAsync("Close skipped", ..., NotificationLevel.Warning, ...)`。

3. **多筆同向 open positions 邊界**
   - 症狀：`openPositions.FirstOrDefault(p => p.Side == targetSide)` 只取第一筆。
   - 影響：當前 `MaxConcurrentPositions=1` 無感；若未來放寬到 N>1，平倉訊號只關一筆殘留。
   - 修法（最低成本）：發現 >1 筆同向部位時 log 一條 warning，**不改行為**、**不擴功能**，純為未來警示。

### 🟡 中優先（應另開獨立膠囊）

4. **`HandleSignalAsync` 分流邏輯零測試覆蓋**
   - 症狀：本次 Application.Tests 190/190 全綠是因為**沒有測試覆蓋這層**，不是因為測試證明分流正確。
   - 建議補測（覆蓋 4 條分支）：
     - `OpenLong + qty=0` → `[SIZE]` 分支
     - `OpenLong + risk reject` → `[RISK]` 分支
     - `CloseLong + 有對應 Long 部位` → 用 `Position.Quantity` 下單，跳過 `RiskManager.CheckBeforeOpenAsync`
     - `CloseLong + 無對應部位` → `[CLOSE]` 分支
     - `CloseShort` 對稱補一輪
   - 影響：缺測下次重構若把分流改壞，CI 不會抓到。

5. **NTP-skew 對 close 路徑不擋（觀察項待裁決）**
   - 來源：S69-HOTFIX_CLOSE_SIGNAL_RISK 交付摘要已標註，仍未開膠囊。
   - 風險：若 OS 時鐘偏差 >1000ms，平倉單會撞 BingX 簽章驗證 → 例外 → `_consecutiveErrors++` → 累積 5 次自動停機。
   - 修法選項：
     - A. 接受現狀（S66-E pre-flight 已開機校時，殘留風險低）。
     - B. 抽 `IPreflightCheck` 給 open/close 共用，把 `ClockSkewRejectThresholdMs` 從 `RiskManager` 內搬出。

### 🟢 低優先（制度面提醒）

6. **本檔（`DRAFT_CONTEXT.md`）滾動義務**
   - 症狀：本 session 已關兩張 hotfix（ASYNC_DISPOSE / CLOSE_SIGNAL_RISK），但本檔在中途未即時更新。
   - 對照：DISCIPLINE §6.4「即時性與只增不刪」要求每完成一原子步驟立即更新。
   - 責任：PM 維護義務，工程師此處僅提示。

7. **ConsoleApp 鎖檔連續撞**
   - 症狀：本 session 兩張膠囊驗收都撞 `MSB3027 ... apphost.exe ... 鎖定`。
   - 修法：建議下版 DISCIPLINE §7 驗收計畫範本把 `tasklist /FI "IMAGENAME eq CryptoBot.ConsoleApp.exe"` 列入強制 Pre-flight 項。

8. **工程師交付前應先驗 DiagnosticTool 指令存在**
   - 症狀：S69-HOTFIX_CLOSE_SIGNAL_RISK 情境 3 補強版列出 `s66a_check-order` / `s61_sync-orders` 等指令，**提交前才用 grep 確認存在**。雖事後驗證 OK，但流程上仍是「先寫後驗」的偷懶模式。
   - 修法：寫驗收計畫前先 `dotnet run --project ../CryptoBot.DiagnosticTool -- help` 看一次完整指令清單，不靠記憶。
   - 建議：本條補進 `Institutional_Memory.md` L8「預防」段落。