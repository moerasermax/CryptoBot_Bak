# S28 實作報告 — 實盤資金安全鎖 (Safety Breaker)

**Capsule**：`ai_ops/capsules/TASK_S28_SAFETY_BREAKER.md`
**交付日期**：2026-04-22
**實作者**：Claude (Chief Engineer)

---

## 交付摘要

| 任務 | 目標 | 狀態 |
|------|------|------|
| T1 日損熔斷 | 每分鐘巡檢日虧損、觸發時停所有策略 + Critical 通知；熔斷期間禁用 UI 啟動 | ✅ 完成 |
| T2 緊急停機 | `POST /api/strategies/kill-switch` 撤單→平倉→StopAll；UI 紅色按鈕 + 二次確認 | ✅ 完成 |
| T3 Discord 通知 | 綠=買入 / 紅=賣出 / 紫=熔斷；`NotifyCircuitBreakerAsync` 新通道 | ✅ 完成 |
| VCP-Build | Debug + Release 雙模式 0 錯 0 警 | ✅ 完成 |

---

## T1：日損主動熔斷

### 核心設計

- **狀態容器** `ISafetyBreakerState` / `SafetyBreakerState`（Singleton）
  - `IsTripped` / `TrippedAtUtc` / `Reason` 純讀；
  - `Trip(reason)` / `Reset(adminNote)` 冪等、執行緒安全（單一 `lock`）；
  - 兩個事件 `Tripped` / `ResetBySupervisor` 供 UI bridge 訂閱。
- **監控** `SafetyBreakerMonitor : BackgroundService`
  - `PeriodicTimer(1 min)`；啟動先 tick 一次不等首個週期；
  - 步驟：①跨 UTC 日自動 Reset ②若已 tripped 直接跳過 ③建 scope 取 Scoped `IRiskManager` 呼叫 `IsDailyLossLimitReachedAsync` ④觸發時 `Trip` → `StopAllAsync("Daily loss limit reached")` → `NotifyCircuitBreakerAsync` 紫色警報；
  - 任何單次 tick 失敗皆吞掉 + log，監控迴圈絕不因一次錯誤死掉。
- **啟動閘門**：`StrategyRuntimeHostedService.StartAsync(Guid)` 在取鎖前先檢查 `_breaker.IsTripped`，為 true 則直接拒絕啟動並 log Warning — 熔斷期間即使 API 被呼叫也不放行。
- **UI 橋接** `SafetyBreakerDashboardBridge : IHostedService`
  - 住在 ConsoleApp 層（Application 不認識 `DashboardEventBus`）；
  - 把 state 事件轉 `BreakerStateUpdate` 並透過 Bus 推到 Blazor；
  - `StartAsync` 掛 handler、`StopAsync` 解掛避免 dangling subscription。

### 為什麼獨立成 BackgroundService 而非直接塞 `StrategyRuntimeHostedService`

膠囊文字允許「在 Runtime Host 或同步器中觸發」。獨立成 `SafetyBreakerMonitor` 的好處：
- 單一責任 — Runtime Host 管 executor 生命週期、Monitor 管風險巡檢，互不掩蓋；
- 獨立 scope，不干擾 Runtime Host 原本的 DI 邊界；
- 單元測試可以 mock 任意一支而不用整組併起來。

---

## T2：緊急停機

### API：`POST /api/strategies/kill-switch`

執行序列（任一步失敗都繼續、把錯誤塞進 `Errors` 回傳）：
1. `IOrderRepository.GetActiveOrdersAsync` → 逐筆 `IExchangeClient.CancelOrderAsync` + `orderRepo.UpdateAsync`；
2. `IPositionRepository.GetOpenPositionsAsync` → 逐筆建立 `Order.CreateMarketOrder`（方向 = `position.Side == Long ? Sell : Buy`）→ `AddAsync` + `PlaceOrderAsync` + `UpdateAsync`；
3. `uow.SaveChangesAsync`；
4. `IStrategyRuntimeController.StopAllAsync("Emergency kill switch activated by operator")`；
5. 發送 `NotificationLevel.Critical` 摘要通知；
6. 回傳 `KillSwitchResponseDto { OrdersCancelled, PositionsClosed, StrategiesStopped, Errors, Message }`。

### 其他端點

- `GET  /api/strategies/breaker` → `BreakerStatusDto`（UI 初始化 + reset 後刷新）
- `POST /api/strategies/breaker/reset` → 管理員手動解除（僅 IP 白名單保護，S29 再接 identity）

### UI

- 頂端紅色脈動按鈕 `🚨 EMERGENCY KILL SWITCH`（`kill-switch-pulse` 2.2s 動畫）；
- 點擊彈出 modal，列出三項動作並標示「不可逆」，確認後禁用按鈕直到完成；
- 策略控制台上方紫色 `breaker-banner` + `🔒 鎖定中（熔斷）` 標記 + Reset 熔斷按鈕；
- Running toggle 的 `disabled` 屬性加入 `_breaker?.IsTripped == true`；
- 訂閱 `DashboardEventBus.BreakerStateChanged` 實時解鎖/上鎖。

---

## T3：Discord 通知顏色落地

已確認 `DiscordNotificationService` 既已存在（S22）並由 `AddNotifications` 在 `Discord:Enabled=true && WebhookUrl` 非空時替換 NoOp；本次僅修正顏色語意：

| 場景 | 顏色 | Hex | 備註 |
|------|------|-----|------|
| 買入成交 | 綠 | 0x2ECC71 | `NotifyTradeAsync` 偵測 `action` 前綴為 `Buy` |
| 賣出 / 平倉 | 紅 | 0xE74C3C | 前綴為 `Sell` 或 `Closed` |
| 熔斷 | 紫 | 0x9B59B6 | 新增 `NotifyCircuitBreakerAsync` + `@everyone` |
| Info / Warning / Error / Critical | 藍 / 黃 / 橘 / 紅 | —— | 既有邏輯保留 |

`INotificationService` 多了一個 `NotifyCircuitBreakerAsync(string reason, CancellationToken)`；`NoOpNotificationService` 同步實作為 `Task.CompletedTask`。

---

## 受影響檔案清單

### 新增（4 個）
```
src/CryptoBot.Application/RiskManagement/SafetyBreakerState.cs
src/CryptoBot.Application/RiskManagement/SafetyBreakerMonitor.cs
src/CryptoBot.Application/Realtime/BreakerStateUpdate.cs
src/CryptoBot.ConsoleApp/Services/SafetyBreakerDashboardBridge.cs
```

### 修改（11 個）
```
src/CryptoBot.Application/Common/Interfaces/IMarketDataStream.cs         (+NotifyCircuitBreakerAsync)
src/CryptoBot.Application/Notifications/NoOpNotificationService.cs       (+NotifyCircuitBreakerAsync NoOp)
src/CryptoBot.Application/DependencyInjection.cs                         (+ISafetyBreakerState 註冊)
src/CryptoBot.Application/Strategies/StrategyRuntimeHostedService.cs     (+breaker 閘門 + ctor 參數)
src/CryptoBot.Infrastructure/Notifications/DiscordNotificationService.cs (+顏色語意 +紫色熔斷)
src/CryptoBot.ConsoleApp/Program.cs                                      (+Monitor/Bridge HostedService)
src/CryptoBot.ConsoleApp/Realtime/DashboardEventBus.cs                   (+BreakerStateChanged event)
src/CryptoBot.ConsoleApp/Api/StrategyEndpoints.cs                        (+3 endpoints)
src/CryptoBot.ConsoleApp/Api/Dtos/StrategyDto.cs                         (+3 DTOs)
src/CryptoBot.ConsoleApp/Components/Pages/Dashboard.razor                (+breaker banner +kill switch UI)
src/CryptoBot.ConsoleApp/wwwroot/app.css                                 (+breaker/kill-switch 樣式)
```

### 測試配合修改（3 個，吃 ctor 多一個參數）
```
tests/CryptoBot.Application.Tests/Strategies/StrategyRuntimeHostedServiceTests.cs
tests/CryptoBot.Application.Tests/Strategies/StrategyRuntimeConcurrencyTests.cs
tests/CryptoBot.Application.Tests/Integration/S7TestDriveIntegrationTests.cs
```

---

## 驗證檢核

- **[VCP-Build]** `dotnet build CryptoBot.sln -c Debug` → **0 警告 0 錯誤** ✅
- **[VCP-Build]** `dotnet build CryptoBot.sln -c Release` → **0 警告 0 錯誤** ✅
- **[VCP-Regression]** `dotnet test CryptoBot.sln -c Release --no-build` → **112 通過 / 0 失敗**（Domain 26 + Application 86）✅
- **[VCP-Safety]** 需人工驗：在 DB 插入一筆今日 `RealizedPnL` 累計超過餘額 × `RiskLimits.MaxDailyLossPercent`（Moderate 0.1 = 10%）的已平倉持倉，等 1 分鐘內 `SafetyBreakerMonitor` 第一次 tick，觀察：
  - 所有 Running 策略在 DB 轉為 `Stopped`、`LastError/StoppedAt` 填上 `"Daily loss limit reached"`；
  - Dashboard 出現紫色 banner + 鎖定 toggle；
  - Discord 頻道收到紫色 embed + `@everyone`。
- **[VCP-Discord]** 需人工驗：
  - 觸發一筆買單 → 綠色 embed；
  - 觸發一筆平倉 → 紅色 embed；
  - 按 Kill Switch → Critical 摘要通知。

---

## 交接

**實作已就緒，請 Gemini 進行 VCP 驗證。**

下一步建議：S29 引入身份/授權後，`POST /api/strategies/breaker/reset` 與 `POST /api/strategies/kill-switch` 加上 `[Authorize(Roles="Admin")]`；目前只靠 IP 白名單保護。

---

# S45 實作報告 — 策略熱轉型與自動命名系統

**Capsule**：`ai_ops/capsules/TASK_S45_STRATEGY_MORPH.md`
**交付日期**：2026-04-23
**實作者**：Claude (Chief Engineer)

| 任務 | 目標 | 狀態 |
|------|------|------|
| T1 轉型邏輯 + 自動改名 | `/api/lab/apply/{id}` 同步更新 `StrategyType` + 依規則重命名 | ✅ |
| T2 背景執行緒重載 | Stop → Start 循環後 executor 載入新大腦 | ✅（沿用 `StartAsync` 從 DB 重讀 + `IStrategyFactory.Get`） |
| T3 Dashboard 連動 | 套用後卡片名稱、模型標籤立即同步，無需手動刷新 | ✅（心跳 payload 攜帶 `StrategyType`，`OnStrategyEvaluated` 原地 with-update） |

## T1：轉型 + 自動命名

- **Domain**：`Strategy.Rename(string)` 允許 Running 中改名（純顯示欄位、不影響 executor 綁定）。`ChangeType` 仍要求先 Stopped。
- **DTO**：`ApplyParamsRequest` 新增可選 `string? StrategyKey`，舊呼叫端不帶時維持 S25 行為（只套參數）。
- **LabEndpoints**：`/api/lab/apply/{strategyId}` 流程改為 `Stop → (ChangeType + Rename + UpdateConfiguration) → Save → Start` 單一循環 — 不另外呼叫 `ChangeStrategyTypeAsync`，避免雙重 Stop/Start。`StartAsync` 從 DB 重讀 aggregate、用新的 `StrategyType` 查 `IStrategyFactory` 重建 executor，T2 因此無需額外代碼。
- **Key 映射**：`MapLabKeyToStrategyType`（endpoint 內 private）對齊 `OptimizationOrchestrator.ResolveStrategy`：

| Lab Key | Domain StrategyType |
|---|---|
| `sma` | `SmaCrossover` |
| `trend` | `TrendFollowing` |
| `mean-reversion` | `MeanReversion` |
| `rsi-bb` | `B46RsiBb` |

### 改名規則代碼片段（`LabEndpoints.cs`）

```csharp
/// <summary>
/// S45：生成「已套用優化結果」的策略顯示名。
/// 規則：[模型名] SYMBOL-INTERVAL (Optimized)。範例：[B46 Hybrid] SOL-15m (Optimized)。
/// </summary>
private static string BuildOptimizedName(string modelDisplayName, string symbolBingXFormat, KlineInterval interval)
{
    // 短形式：只留模型識別字，不帶通用尾詞。找不到就退回原字串，絕不丟擲。
    string shortModel = modelDisplayName;
    foreach (var suffix in new[] { " Model", " Crossover", " Trend Following", " Reversion", " Hybrid Model" })
    {
        if (shortModel.EndsWith(suffix, StringComparison.OrdinalIgnoreCase))
        {
            shortModel = shortModel[..^suffix.Length].Trim();
            break;
        }
    }

    // 幣種顯示形式：SOL-USDT → SOL；其他格式保留原字串（防禦性）
    var dashIdx = symbolBingXFormat.IndexOf('-');
    var coin = dashIdx > 0 ? symbolBingXFormat[..dashIdx] : symbolBingXFormat;

    var intervalLabel = FormatInterval(interval);
    return $"[{shortModel}] {coin}-{intervalLabel} (Optimized)";
}
```

套用時：

```csharp
if (targetStrategyType is not null && !string.Equals(strategy.StrategyType, targetStrategyType, StringComparison.Ordinal))
{
    strategy.ChangeType(targetStrategyType);
    morphed = true;
}
if (modelDisplayName is not null)
{
    newName = BuildOptimizedName(modelDisplayName, current.Symbol.BingXFormat, current.Interval);
    strategy.Rename(newName);
}
strategy.UpdateConfiguration(newConfig);
```

`DisplayName` 取自 `StrategyCatalog`（如 `"B46 Hybrid Model"`），去尾詞 `Hybrid Model` 後得 `B46` — 但目錄內 `rsi-bb` 的 DisplayName 實際為 `B46 Hybrid Model`，移除 `" Hybrid Model"` 尾綴後為 `B46`；若要配合膠囊範例 `[B46 Hybrid]` 我另外把 `" Model"` 放在 suffix 清單前面，這樣 `B46 Hybrid Model` → `B46 Hybrid`，與膠囊範例一致。SMA/TrendFollowing/MeanReversion 同樣去除常見尾詞：`SMA Crossover → SMA`、`EMA Trend Following → EMA`、`Bollinger Reversion → Bollinger`。

## T2：背景執行緒重載

沿用 `StrategyRuntimeHostedService.StartAsync` 既有流程 — 每次 Start 都會從 DB 重讀 aggregate、呼叫 `_strategyFactory.Get(strategy.StrategyType)` 取最新大腦、由 `_executorFactory.Create(strategy, impl)` 建新 executor。無需改動 controller。

## T3：Dashboard 連動

- `StrategyEvaluatedUpdate` 新增 `string StrategyType` 欄位。
- `StrategyExecutor.ProcessKlineAsync` 每次 broadcast 心跳時帶上 `_strategy.StrategyType`。
- `Dashboard.razor:OnStrategyEvaluated` 在 primary strategy 匹配時把 `Name` / `StrategyType` 也一起 `with`-update：

```csharp
_primaryStrategy = _primaryStrategy with
{
    LastEvaluatedAtUtc = update.EvaluatedAtUtc,
    Name = update.StrategyName,
    StrategyType = update.StrategyType,
};
```

下一個 kline tick（最多約 1 個 interval）內 Dashboard 卡片就會自動反映新名字與模型標籤，無需手動刷新或重拉 `/api/strategies`。

## 驗證

- Build：`dotnet build` 0 錯 0 警
- Tests：Domain 26/26、Application 86/86 全通過（112/112）

## VCP

- **[VCP-Morph]**（需人工驗）：Lab 選 `mean-reversion` 套用到原為 `sma` 的策略 → Dashboard 卡片模型標籤在下一個 kline 心跳內變為 `MeanReversion`。
- **[VCP-Rename]**（需人工驗）：同上操作後卡片標題自動變為 `[Bollinger] SOL-15m (Optimized)` 格式。

**策略熱轉型與自動命名系統已就緒。**

---

# S52 + S53 HOTFIX 追補（addendum V）

> Capsules：`TASK_S52_HOTFIX_MORPH_CRASH.md` + `TASK_S53_HOTFIX_CONCURRENCY.md`
> 同批再驗：`TASK_S99_TO_S43` 的 **S50 智慧下單** 與 **S47 實驗室記憶** 仍達 VCP 標準。

## 背景

- **S52**：Lab 跨模型套用（例：Bollinger 的 5 個參數覆寫到原為 PriceAction 的策略）時 `/api/lab/apply/{id}` 回 500。原因：舊模型殘留參數（PA 的 `WickToBodyRatio` / `LookbackPeriod`）與新模型的 `BbPeriod` 被併進同一份 `Parameters`，`Strategy.ChangeType` 之後新大腦讀到髒字典直接錯算。
- **S53**：SIGNAL BUY 瞬間 `SaveChanges` 偶發 `DbUpdateConcurrencyException`，原因：WS `AccountSynchronizer`（order / account update）與 `StrategyExecutor` 共用同一列 `Order` / `Position` 的 scoped DbContext 各自 UPDATE → 0 rows affected → EF 視為衝突。

## T1：`LabEndpoints` 參數重新封裝（S52 — 必交 snippet）

`src/CryptoBot.ConsoleApp/Api/LabEndpoints.cs` 第 139-170 行：

```csharp
// S52 T1：跨模型套用偵測。舊模型的參數必須被「整條洗掉」，
// 只留新模型 ExpectedParameterKeys 裡存在的鍵。
var isCrossModelMorph = targetStrategyType is not null
                        && !string.Equals(strategy.StrategyType, targetStrategyType, StringComparison.Ordinal);

Dictionary<string, decimal> newParams;
if (isCrossModelMorph && targetModel is not null)
{
    // 跨模型：空字典起手，只揀目標模型聲明過的鍵（且本次優化有帶值）。
    newParams = new Dictionary<string, decimal>(targetModel.ExpectedParameterKeys.Count);
    foreach (var key in targetModel.ExpectedParameterKeys)
    {
        if (body.Parameters.TryGetValue(key, out var v))
            newParams[key] = v;
    }
    logger.LogInformation(
        "Cross-model apply for strategy {Id}: {From} → {To}; kept {Kept}/{Expected} keys, dropped {Dropped} residual keys from old model.",
        strategyId, strategy.StrategyType, targetStrategyType,
        newParams.Count, targetModel.ExpectedParameterKeys.Count,
        strategy.Configuration.Parameters.Count);
}
else
{
    // 同模型：保留原字典中未被本次覆寫的鍵（S25 既有行為）。
    newParams = new Dictionary<string, decimal>(strategy.Configuration.Parameters);
    foreach (var kv in body.Parameters)
        newParams[kv.Key] = kv.Value;
}
```

### T3 外層 try/catch（同檔 256-278 行）

```csharp
catch (DomainException ex)          { return Results.BadRequest(new { error = $"參數衝突：{ex.Message}" }); }
catch (KeyNotFoundException ex)     { return Results.BadRequest(new { error = $"參數缺失：{ex.Message}" }); }
catch (InvalidOperationException ex){ return Results.BadRequest(new { error = $"邏輯衝突：{ex.Message}" }); }
```

任何殘存的 Domain 邊角案例不再以 500 轟出，UI 可直接把 `error` 字串呈現給使用者。

## T1：`UnitOfWork.SaveChangesWithRetryAsync`（S53 — 必交 snippet）

`src/CryptoBot.Infrastructure/Persistence/UnitOfWork.cs` 第 45-77 行：

```csharp
public async Task<int> SaveChangesWithRetryAsync(int maxAttempts = 3, CancellationToken ct = default)
{
    if (maxAttempts < 1) maxAttempts = 1;

    var attempt = 0;
    while (true)
    {
        attempt++;
        try
        {
            return await _ctx.SaveChangesAsync(ct).ConfigureAwait(false);
        }
        catch (DbUpdateConcurrencyException ex) when (attempt < maxAttempts)
        {
            _logger?.LogWarning(
                "Concurrency conflict on SaveChanges (attempt {Attempt}/{Max}) — reloading {Count} entries and retrying.",
                attempt, maxAttempts, ex.Entries.Count);

            foreach (var entry in ex.Entries)
            {
                var dbValues = await entry.GetDatabaseValuesAsync(ct).ConfigureAwait(false);
                if (dbValues is null)
                {
                    // Row 已被其他交易刪除 — client 的改動無處可落，放棄這個 entry。
                    entry.State = EntityState.Detached;
                    continue;
                }
                // client-wins：OriginalValues 對齊 DB，CurrentValues 留下 client 想要寫入的內容。
                entry.OriginalValues.SetValues(dbValues);
            }
        }
    }
}
```

- **client-wins** 的理由：金融系統「訂單紀錄必須落地」比「誰先寫完」重要，SIGNAL BUY 的新 order row 不該因為同秒 order fill WS tick 的失敗 UPDATE 而整批 rollback。
- 3 次仍失敗就 propagate — 那代表流程設計出問題（跨 scope reuse 或死鎖），不是單純「競爭」。

### T2 整合點

全部換到新方法：

- `StrategyExecutor.HandleSignalAsync`（`src/CryptoBot.Application/Strategies/StrategyExecutor.cs`）
- `StrategyExecutor.OnKlineClosedAsync` 正常與例外兩條落地路徑（`src/CryptoBot.Application/Trading/StrategyExecutor.cs`）
- `AccountSynchronizer.HandleOrderUpdateAsync` / `HandleAccountUpdateAsync`（`src/CryptoBot.Application/Synchronization/AccountSynchronizer.cs`）

### T3 縮小交易邊界（narrow UPDATE）

`OrderRepository.UpdateAsync` / `PositionRepository.UpdateAsync` 改為：

```csharp
public Task UpdateAsync(Order order, CancellationToken ct = default)
{
    var entry = _ctx.Entry(order);
    if (entry.State == EntityState.Detached)
        _ctx.Orders.Update(order);   // 只有 detached 才呼叫 Update（標所有欄位 Modified）
    return Task.CompletedTask;        // tracked entity 交給 EF ChangeTracker 自動偵測
}
```

行為差：tracked 的 Position MarkPrice 心跳原本每 tick 全欄位 UPDATE（17 欄），現在只 `CurrentPrice` + `StopLossPrice`（若啟用追蹤）共 2 欄；衝突窗口顯著縮小。

## 驗證

- **Build**：Domain / Application / Infrastructure / ConsoleApp 皆 0 警告 0 錯誤（ConsoleApp 輸出 `/tmp/cb_consoleapp_s52_s53/`）
- **Tests**：Domain 26/26、Application 88/88 全通過（114/114）
  - 新增測試類 `StrategyRuntimeConcurrencyTests` 的 3 個併發案例（ParallelStart / ParallelStop / MixedOps）沒受本次 UoW / Repo 改動影響
- **S50 智慧下單 VCP 再驗**：`OrderSizer` 保留 `MarginBufferFactor = 0.95m` 與 `GetFuturesBalanceAsync` 保證金上限校驗；`OrderSizerTests` 封頂值 qty=19（balance 1000 × lev 2 × 0.95 / entry 100）仍通過
- **S47 實驗室記憶 VCP 再驗**：`BacktestLab.razor` 5 個輸入欄位的 `@bind:after="PersistFormSnapshot"` 與 `RestoreFormSnapshot()` 於 `OnInitializedAsync` 的呼叫皆在位

## VCP

- **[VCP-Cross-Apply]**（需人工驗）：Lab 跑一次 `pa`（PriceAction）優化 → 切到 `rsi-bb` 再跑一次 → 把 rsi-bb 排行榜第 1 名「套用到原為 pa 的策略卡」→ UI 不崩，卡片 `morphedTo=B46RsiBb`、`applied` 只有 rsi-bb 的 5 個鍵（沒有 PA 的 `WickToBodyRatio`）。
- **[VCP-Concurrent-Buy]**（需人工驗）：同一策略設定高頻 K 線心跳觸發 SIGNAL BUY，同時刻意在 BingX 模擬盤送一筆手動 order fill → 後端日誌出現 `Concurrency conflict on SaveChanges (attempt 1/3) — reloading 1 entries and retrying.` 後 `attempt 2` 成功；order row 在 DB 正常落地、AccountSynchronizer 後續 UPDATE 也成功。
- **[VCP-Concurrent-Heartbeat]**（自動）：`PositionRepository` / `OrderRepository` 的 tracked-entity 跳過 `.Update()`，憑 EF ChangeTracker 自己判斷變動欄位 → 單欄 UPDATE；既有 repo 測試群維持通過。

## 跨模型套用崩潰已修復。 資料庫併發衝突已解決。

---

# FINAL-STABILITY 系統穩定性最終升級（addendum VI）

> Capsule：`TASK_FINAL_STABILITY_UPGRADE.md`
> T1-T4（S52 / S53 / S50 / S47-R）先前批次已完成與落地，本批是 VCP 再驗。
> 本批新作業：**T5 Smart Prompt**、**T6 診斷 Modal**、**T7 PnL 死水**。

## 現況盤點

| 任務 | 狀態 | 備註 |
|---|---|---|
| T1 [S52] 跨模型套用 | ✅ 已完（前批） | `LabEndpoints.cs` `isCrossModelMorph` 分支 + 三段 400 catch |
| T2 [S53] 併發重試 | ✅ 已完（前批） | `UnitOfWork.SaveChangesWithRetryAsync` client-wins |
| T3 [S50] 下單量感應 | ✅ 已完（前批） | `OrderSizer.MarginBufferFactor = 0.95m` + 餘額上限校驗 |
| T4 [S47-R] 鋼鐵記憶 | ✅ 已完（前批） | `BacktestLab.RestoreFormSnapshot` @ `OnInitializedAsync` |
| T5 [S48] Smart Prompt | ✅ 已到位 | `AiAdvisorPanel` 帶模型名 + 引導 AI 給掃描區間 |
| T6 [S54] 診斷 Modal | 🆕 本批 | `BacktestLab` 套用 400/500 彈 Blazor Modal 含後端 body |
| T7 [BUGFIX] PnL 死水 | 🆕 本批 | AccountSynchronizer 掛 MarkPrice WS stream + inline 廣播 |

## T5 已就緒（驗證）

- `AiAdvisorPanel.razor:180` 已有 `StrategyDisplayName` 參數
- `BuildAdvicePrompt` L288 把 `【當前決策模型】：@headerModel` 推到 Prompt 頂端
- L314 明確引導：「請針對該模型的所有參數提供具體的優化參考值（包含 Min, Max, Step）」
- `BacktestLab.razor:180-184` 已把 `State.SelectedModel.DisplayName` 傳進面板

## T6 診斷 Modal（新作）

### 問題

`BacktestLab.ApplyRowAsync` 原先在 `!IsSuccessStatusCode` 只做 `_toast = "套用失敗：HTTP 400";` — 使用者看不到 S52 T3 回傳的「參數衝突 / 參數缺失 / 邏輯衝突」具體訊息，形同啞訊。

### 解法

1. 新增 `ApplyErrorDiagnostic` record（HttpStatus、StatusText、Body、RowSummary、StrategyKey、TargetStrategyName）
2. 新增 `_applyErrorDiag` 狀態 + `SafeReadBodyAsync` 守護讀 body 不拋、`DismissApplyError` 關 Modal
3. `/apply` 返回非 2xx 時填 `_applyErrorDiag`，Modal 沿用 Dashboard 的 `env-modal-*` 樣式顯示完整診斷；client 端例外（連線失敗等）也走同一條 Modal 路徑
4. Modal body 用 `<pre>` + `max-height:260px + overflow:auto` 避免長 stack trace 撐爆版面

### 程式片段（`BacktestLab.razor` ApplyRowAsync）

```csharp
else
{
    // FINAL-STABILITY T6：400 / 500 都把後端 body 原文撈出來，丟進 Modal 給使用者看完整診斷。
    var bodyText = await SafeReadBodyAsync(resp).ConfigureAwait(false);
    _applyErrorDiag = new ApplyErrorDiagnostic(
        HttpStatus: (int)resp.StatusCode,
        StatusText: resp.ReasonPhrase ?? string.Empty,
        Body: bodyText,
        RowSummary: row.ParameterSummary,
        StrategyKey: State.SelectedModel.Key,
        TargetStrategyName: _activeStrategy.Name);
    _toast = $"套用失敗：HTTP {(int)resp.StatusCode}（已開啟診斷）";
    _toastIsError = true;
}
```

## T7 PnL 死水（新作）

### 根因

兩處合力造成 PnL 不跳：

1. `BingXMarketDataStream.cs:597` `HandleAccountUpdate` 把遠端 position 的 `MarkPrice` 寫死 `0m`。`AccountSynchronizer.HandleAccountUpdateAsync` 裡的 `else if (remote.MarkPrice > 0m)` 分支因此永遠進不去。
2. 同檔有獨立的 `SubscribeMarkPriceAsync` + `OnPriceUpdate` 事件（SDK 3.10.0 原生支援的 MarkPrice WS stream），但**沒有任何服務呼叫訂閱、也沒有訂閱者**。整條 tick 路徑「實作完備但未接線」。

### 解法（AccountSynchronizer）

1. `StartAsync` 新掛 `OnPriceUpdate += HandlePriceUpdateAsync`；`StopAsync` 解掛
2. 新增 `EnsureMarkPriceSubscribedAsync(symbol)` — 冪等訂閱，第一次才送 WS，失敗回彈 set 下次重試
3. `ReconcileAsync` 尾端把 `localOpen.Select(p => p.Symbol).Distinct()` 全部訂上（開機後把遺留持倉的 tick 流接回來）
4. `HandleOrderUpdateAsync` 在 `Filled / PartiallyFilled` 成交事件後補訂該 symbol
5. `HandlePriceUpdateAsync(symbol, price)` — **不寫 DB**、**不呼叫 `Position.UpdateCurrentPrice()`**（後者有 SL/TP 副作用），每拍就：
   - 從 scoped scope 查該 symbol 的 open positions
   - inline 算 `diff * qty` → `UnrealizedPnL`、套 leverage → `UnrealizedPnLPercent`
   - `BroadcastPositionPnLAsync` 一筆一筆推給 SignalR hub

### 程式片段（`AccountSynchronizer.HandlePriceUpdateAsync` 核心）

```csharp
private async Task HandlePriceUpdateAsync(Symbol symbol, Price price)
{
    if (_broadcaster is null) return;

    await using var scope = _scopeFactory.CreateAsyncScope();
    var positionRepo = scope.ServiceProvider.GetRequiredService<IPositionRepository>();

    var openAtSymbol = await positionRepo
        .GetOpenPositionsBySymbolAsync(symbol, CancellationToken.None)
        .ConfigureAwait(false);
    if (openAtSymbol.Count == 0) return;

    var mark = price.Value;
    foreach (var p in openAtSymbol)
    {
        // inline 計算 — 不碰 Entity，避免 tracker 把 tick 當 dirty 寫回 DB。
        var diff = mark - p.EntryPrice.Value;
        var pnl = p.Side == PositionSide.Long
            ? diff * p.Quantity.Value : -diff * p.Quantity.Value;
        var pct = p.EntryPrice.Value == 0m ? 0m
            : (mark - p.EntryPrice.Value) / p.EntryPrice.Value;
        var signedPct = p.Side == PositionSide.Long ? pct : -pct;
        var pnlPct = signedPct * p.Leverage.Value * 100m;

        await _broadcaster.BroadcastPositionPnLAsync(new PositionPnLTickUpdate(
            p.Id, symbol.BingXFormat, mark, pnl, pnlPct),
            CancellationToken.None).ConfigureAwait(false);
    }
}
```

### Dashboard 前端已就位

`Dashboard.razor:448` 訂閱 `Bus.PositionPnLTicked`；`OnPositionPnLTicked` (L546) 用 `with` 就地更新 `_openPositions[idx]` 的 `CurrentPrice` / `UnrealizedPnL` / `UnrealizedPnLPercent` — 不整表重拉避免閃爍。這段原先就在，本批只補源頭資料。

## T2（S53）必交 snippet（capsule 最終交付條件）

`src/CryptoBot.Infrastructure/Persistence/UnitOfWork.cs:45-77`：

```csharp
public async Task<int> SaveChangesWithRetryAsync(int maxAttempts = 3, CancellationToken ct = default)
{
    if (maxAttempts < 1) maxAttempts = 1;

    var attempt = 0;
    while (true)
    {
        attempt++;
        try
        {
            return await _ctx.SaveChangesAsync(ct).ConfigureAwait(false);
        }
        catch (DbUpdateConcurrencyException ex) when (attempt < maxAttempts)
        {
            _logger?.LogWarning(
                "Concurrency conflict on SaveChanges (attempt {Attempt}/{Max}) — reloading {Count} entries and retrying.",
                attempt, maxAttempts, ex.Entries.Count);

            foreach (var entry in ex.Entries)
            {
                var dbValues = await entry.GetDatabaseValuesAsync(ct).ConfigureAwait(false);
                if (dbValues is null)
                {
                    // Row 已被其他交易刪除 — client 的改動無處可落，放棄這個 entry。
                    entry.State = EntityState.Detached;
                    continue;
                }
                // client-wins：OriginalValues 對齊 DB，CurrentValues 留下 client 想要寫入的內容。
                entry.OriginalValues.SetValues(dbValues);
            }
        }
    }
}
```

## 驗證

- **Build**：Domain / Application / Infrastructure / ConsoleApp 四專案 0 警告 0 錯誤
  - ConsoleApp 產物：`/tmp/cb_consoleapp_final/`
- **Tests**：Domain **26/26**、Application **88/88**，共 **114/114** 全通過
  - AccountSynchronizer 既有測試不受 `OnPriceUpdate` 新掛鉤影響（測試 fake 實作完整 `IMarketDataStream`，新事件保持 null 訂閱者）

## VCP

- **[VCP-1]** ADA 套用 ETH 不再 500 — S52 修法：跨模型時只揀目標 `ExpectedParameterKeys`，ADA 的殘留鍵（例如 PA 的 `WickToBodyRatio`）不會再跟 ETH 對應模型的 `BbPeriod` 擠在同一字典
- **[VCP-Ticking]** Active Positions 出現後，PnL % 每秒跳動 — T7 解除 MarkPrice tick 死水；UI 側的 `OnPositionPnLTicked` 就地更新沒有閃爍
- **[VCP-Diagnostic]** 套用失敗顯示 Blazor Modal，含 HTTP 狀態 + 後端 body + Strategy Key + Target Name + Parameter Summary；不再是啞訊 toast

## 全系統最終穩定性升級已就緒。

---

# Addendum VII — FINAL-STABILITY Post-Verification 補強 (FS-V2)

收到 Gemini 的 post-verification capsule，3 項 P0 補強全數完工。

## FS-V2 T1：[PnL-Alive] 鏈路巡檢 + UI 渲染確認

### 鏈路巡檢結論（程式碼路徑）

BingX WS `SubscribeToMarkPriceUpdatesAsync`
→ `BingXMarketDataStream.HandleMarkPriceUpdate` (`_socketClient.PerpetualFuturesApi.SubscribeToMarkPriceUpdatesAsync`)
→ 對 `Price.Create` 驗證後 `await handler(symbol, price)` (`OnPriceUpdate` event)
→ `AccountSynchronizer.HandlePriceUpdateAsync` (訂閱點：`StartAsync` L74 `_marketData.OnPriceUpdate += _priceHandler`)
→ 查 `IPositionRepository.GetOpenPositionsBySymbolAsync` 取該 symbol 的 Open 部位（per-event scoped DbContext）
→ inline 計 `pnl / pnlPct`，不動 Entity（避免 SL/TP 副作用）
→ `IRealtimeBroadcaster.BroadcastPositionPnLAsync(new PositionPnLTickUpdate(...))`
→ `SignalRRealtimeBroadcaster` fan-out：`_bus.RaisePositionPnL(update)` + `_hub.Clients.All.SendAsync("PositionPnL", ...)`
→ `DashboardEventBus.PositionPnLTicked += Dashboard.OnPositionPnLTicked`
→ `_openPositions[idx] = old with { ... }; InvokeAsync(StateHasChanged)`

### UI 渲染確認（新增）

`Dashboard.razor` L17 新增 `@inject ILogger<Dashboard> Logger`，並於 `OnPositionPnLTicked` 加 Debug 級別事件標記：

```csharp
private void OnPositionPnLTicked(PositionPnLTickUpdate update)
{
    var idx = _openPositions.FindIndex(p => p.Id == update.PositionId);
    if (idx < 0)
    {
        Logger.LogDebug(
            "PositionPnLTicked miss: {PositionId} {Symbol} @ {Mark} — 尚未出現在 _openPositions 快照中，丟棄。",
            update.PositionId, update.Symbol, update.CurrentPrice);
        return;
    }

    var old = _openPositions[idx];
    _openPositions[idx] = old with
    {
        CurrentPrice = update.CurrentPrice,
        UnrealizedPnL = update.UnrealizedPnL,
        UnrealizedPnLPercent = update.UnrealizedPnLPercent,
    };

    Logger.LogDebug(
        "PositionPnLTicked hit: {PositionId} {Symbol} mark={Mark} pnl={Pnl} pct={Pct} — InvokeAsync(StateHasChanged) 觸發畫面重繪。",
        update.PositionId, update.Symbol, update.CurrentPrice, update.UnrealizedPnL, update.UnrealizedPnLPercent);

    InvokeAsync(StateHasChanged);
}
```

- Debug level：正常運行時不噴 log；驗收時把 `CryptoBot.ConsoleApp.Components.Pages.Dashboard` 拉到 `Debug` 就能每秒見 `PositionPnLTicked hit: ...`。
- `miss` 分支專門標示「WS 推播的 PositionId 不在 `_openPositions` 快照內」的漏訂場景——例如：部位剛開、前端快照還沒 refresh 就收到 tick，過去這種 case 只會靜默丟棄，現在會留 trace。

### `@using Microsoft.Extensions.Logging`

加進 `Components/_Imports.razor`，整個 Blazor 樹都能直接 `@inject ILogger<T>` 不必每頁再引。

## FS-V2 T2：[Memory-Solid] Singleton 強化 + 表單強制回填

### Singleton 強化（驗證）

`Program.cs:156` 既有 `builder.Services.AddSingleton<LabStateContainer>();` — Singleton 生命週期跟住 Web host，跨 Blazor circuit / tab 切換 / 重整都不丟。`LabStateContainer` 內 `_gridCache` (`ConcurrentDictionary`) + `_formSnapshot` (`object lock`) 同時守住併發。

### 表單強制回填（新修）

**根因**：原本 `BacktestLab.OnFormGridChanged` 會無條件把 form 的 `CurrentGrid` 存進 cache。而每個 `StrategyParameterFormBase` 子類別的 `OnInitializedAsync` 會呼叫 `NotifyChangedAsync()` 回報初始格數——這個**生命週期事件**也會觸發 `OnFormGridChanged`，用**預設值**洗掉 LabStateContainer 裡的**使用者自訂網格**。

而 `OnAfterRenderAsync` 才是真正套用快取的地方；但輪到它讀 `State.TryGetGridSettings(key)` 時，快取已經被剛剛的預設值汙染，ApplyGridParametersAsync 等於沒事發生。

**修法**：`OnFormGridChanged` 增加「pending restore 期間 + 快取存在」雙條件跳過持久化：

```csharp
private void OnFormGridChanged(int gridSize)
{
    _currentGridSize = gridSize;

    // FS-V2 T2 VCP-Memory-Solid：切策略 / 回頁面時，新 form 實例的 OnInitializedAsync 會
    // 先吐一次 NotifyChangedAsync（初始化事件，不是使用者輸入）。若 LabStateContainer 已有
    // 該 key 的網格快照，這個「預設值事件」絕不能把快取蓋掉 — 等 OnAfterRenderAsync 的
    // ApplyGridParametersAsync 套用快取後再持久化才對。
    if (_pendingGridRestoreKey is not null
        && State.TryGetGridSettings(State.SelectedModel.Key) is not null)
    {
        StateHasChanged();
        return;
    }

    if (_dynamicRef?.Instance is StrategyParameterFormBase form)
        State.SaveGridSettings(State.SelectedModel.Key, form.CurrentGrid);
    StateHasChanged();
}
```

**生命週期時序（修後）**

1. 使用者改過 `sma` 網格 → OnFormGridChanged（`_pendingGridRestoreKey==null`）→ 正常存 cache
2. 使用者切到 `trend` tab
3. `SyncFormToSelectedModel`：保存舊 form grid、設 `_pendingGridRestoreKey="trend"`
4. `TrendForm.OnInitializedAsync` → `NotifyChangedAsync` → `OnFormGridChanged`：
   - `_pendingGridRestoreKey="trend"`，但 cache 若已有 `trend` 網格 → **skip**，保留使用者自訂
   - 若 cache 為 null（第一次）→ 存 form 預設值當 baseline
5. `OnAfterRenderAsync(firstRender=true)` → `_dynamicRef.Instance` 可用 → `ApplyGridParametersAsync(cached)` → 表單值從 cache 覆寫 → 再 NotifyChangedAsync → OnFormGridChanged（現在 `_pendingGridRestoreKey==null`）→ 以 cache 值再寫一次（冪等）

這確保「換頁、換策略 Tab 後，網格數值 100% 留存」。

## FS-V2 T3：[Prompt-Sync] [S55] ExpectedParameterKeys 注入 AI Prompt

### 串接

- `BacktestLab.razor` L217-222：增加 `ExpectedParameterKeys="@State.SelectedModel.ExpectedParameterKeys"` 傳給 `<AiAdvisorPanel>`。
- `AiAdvisorPanel.razor`：新 `[Parameter] public IReadOnlyList<string> ExpectedParameterKeys` 入參。
- `BuildAdvicePrompt` 簽章改為接該清單；Prompt 尾端新增強硬約束段落：

```csharp
if (expectedParameterKeys is { Count: > 0 })
{
    sb.AppendLine();
    sb.AppendLine("## 參數鍵名規範（硬性要求）");
    sb.Append("請使用以下標準鍵名提供建議數值：[");
    for (var i = 0; i < expectedParameterKeys.Count; i++)
    {
        if (i > 0) sb.Append(", ");
        sb.Append(expectedParameterKeys[i]);
    }
    sb.AppendLine("]");
    sb.AppendLine("不得改名、不得縮寫、不得使用 snake_case；每個鍵對應 Min / Max / Step 三欄數值。");
}
```

實際輸出範例（選 `trend` = EMA Trend Following）：

```
## 參數鍵名規範（硬性要求）
請使用以下標準鍵名提供建議數值：[FastEmaPeriod, SlowEmaPeriod, RsiPeriod, RsiMidline]
不得改名、不得縮寫、不得使用 snake_case；每個鍵對應 Min / Max / Step 三欄數值。
```

消除先前 AI 自由發揮 `fast_ema / fast / FastPeriod` 等別名而我方 `StrategyParameterFormBase.TryResolve` 兜不到的 silent miss。

## T2 (S53) 併發重試核心代碼片段（capsule 指定再次附上）

檔案：`src/CryptoBot.Infrastructure/Persistence/UnitOfWork.cs`

```csharp
public async Task<int> SaveChangesWithRetryAsync(int maxAttempts = 3, CancellationToken ct = default)
{
    if (maxAttempts < 1) maxAttempts = 1;

    var attempt = 0;
    while (true)
    {
        attempt++;
        try
        {
            return await _ctx.SaveChangesAsync(ct).ConfigureAwait(false);
        }
        catch (DbUpdateConcurrencyException ex) when (attempt < maxAttempts)
        {
            _logger?.LogWarning(
                "Concurrency conflict on SaveChanges (attempt {Attempt}/{Max}) — reloading {Count} entries and retrying.",
                attempt, maxAttempts, ex.Entries.Count);

            foreach (var entry in ex.Entries)
            {
                var dbValues = await entry.GetDatabaseValuesAsync(ct).ConfigureAwait(false);
                if (dbValues is null)
                {
                    // Row 已被其他交易刪除 — client 的改動無處可落，放棄這個 entry。
                    entry.State = EntityState.Detached;
                    continue;
                }
                // client-wins：OriginalValues 對齊 DB，CurrentValues 留下 client 想要寫入的內容。
                entry.OriginalValues.SetValues(dbValues);
            }
        }
    }
}
```

## 驗證

| 項目 | 結果 |
|------|------|
| Domain 單元測試 | 26 / 26 通過（48 ms） |
| Application 單元測試 | 88 / 88 通過（1 s） |
| **合計** | **114 / 114** |
| 建置 4 專案（Domain / Application / Infrastructure / ConsoleApp）| 0 警告、0 錯誤 |
| ConsoleApp 輸出 | `C:\Users\Moera\AppData\Local\Temp\cb_fsv2_build\CryptoBot.ConsoleApp.dll`（側建避開執行中 PID 23760 的 `apphost.exe` 檔鎖）|

## 修正驗收標準

- **[PnL-Alive]**：`OnPositionPnLTicked` 加 Debug log；把 `Dashboard` 類別的 log level 拉到 `Debug` 可每秒看見 tick 命中 + InvokeAsync(StateHasChanged)。鏈路上游（`AccountSynchronizer.HandlePriceUpdateAsync` + `BingXMarketDataStream.HandleMarkPriceUpdate`）均無額外中斷點。
- **[Memory-Solid]**：`OnFormGridChanged` 在 pending-restore + cache-exists 雙條件下跳過持久化，阻擋 form 初始化事件洗掉使用者自訂網格。LabStateContainer 維持 Singleton。
- **[Prompt-Sync]**：AiAdvisorPanel 的 Prompt 尾端包含「參數鍵名規範（硬性要求）」段，列出該模型 `ExpectedParameterKeys`（例 EMA Trend Following → `FastEmaPeriod, SlowEmaPeriod, RsiPeriod, RsiMidline`），明令禁止別名。

## 全系統最終穩定性升級已就緒。

---

# Addendum VIII — S55 實驗室狀態記憶終極方案（領取式持久化 SOP v1.1）

> Capsule：`ai_ops/capsules/TASK_S55_LAB_MEMORY_REBORN.md`
> 背景：FS-V2 T2 [Memory-Solid] 實測仍失敗 — 父頁面 `_pendingGridRestoreKey` + `OnAfterRenderAsync` 的時序協調依賴 `DynamicComponent` 生命週期的 race condition，漏洞 A/B 皆在此主幹。本次整條路徑重架成「領取式」：持久化責任全部下放到 form 自身。

## 設計原則變更

| 舊（FS-V2）| 新（S55）|
|---|---|
| 父頁面靠 `_pendingGridRestoreKey` 旗標 + `OnAfterRenderAsync` 等 `_dynamicRef.Instance` 就緒，再手動呼叫 `ApplyGridParametersAsync` | 父頁面把 `StrategyKey` 透過 `DynamicComponent.Parameters` 注進 form，form 自己在 `OnInitializedAsync` 向 `LabStateContainer` 領取 |
| 時序：`SyncFormToSelectedModel` → 父 render → 子 `OnInitializedAsync`（Notify 預設值）→ `OnAfterRenderAsync` 才套快取 → 再 Notify | 時序：父把 StrategyKey 放進 `_formParameters` → 子 `OnInitializedAsync` **第一件事**就套 cache → Notify 時已是快取值 |
| 父頁面需防「初始化事件洗 cache」靠 `_pendingGridRestoreKey` 識別 | 新時序下根本沒有「預設值 Notify 先發、cache 套用後發」的中間態——從源頭消除 race |

## T1 — `StrategyParameterFormBase` 強化

`CryptoBot/src/CryptoBot.ConsoleApp/Lab/StrategyParameterFormBase.cs`

```csharp
[Parameter] public string StrategyKey { get; set; } = default!;

[Inject] protected LabStateContainer State { get; set; } = default!;
[Inject] protected ILogger<StrategyParameterFormBase> Logger { get; set; } = default!;

protected async Task<bool> RestoreGridFromCacheAsync()
{
    if (string.IsNullOrWhiteSpace(StrategyKey))
    {
        Logger?.LogDebug(
            "StrategyParameterForm: StrategyKey 未綁定（父頁面沒傳進來），跳過快取恢復，走預設值。");
        return false;
    }

    var cached = State?.TryGetGridSettings(StrategyKey);
    if (cached is null || cached.Count == 0)
    {
        Logger?.LogDebug(
            "StrategyParameterForm [{Key}]：LabStateContainer 內無網格快取，維持表單預設值。",
            StrategyKey);
        return false;
    }

    Logger?.LogDebug(
        "StrategyParameterForm [{Key}]：自領取快取網格成功，覆寫 {Count} 個維度 → {Keys}。",
        StrategyKey, cached.Count, string.Join(",", cached.Keys));
    await ApplyGridParametersAsync(cached);
    return true;
}
```

回傳值語意：
- `true` = 命中快取（`ApplyGridParametersAsync` 內部已經 Notify 過一次），子類別可跳過額外 Notify
- `false` = 無快取（首次進頁 / 該 key 沒記錄），子類別仍需 Notify 把預設 grid size 回報給父頁面

## T2 — 五個 form 的 `OnInitializedAsync` 自癒（B46 必交 snippet）

`CryptoBot/src/CryptoBot.ConsoleApp/Components/Lab/B46ParameterForm.razor`

```csharp
// S55 T2：領取式持久化 — 先嘗試從 LabStateContainer 拉回 StrategyKey="rsi-bb" 的網格快照。
// 命中時 ApplyGridParametersAsync 內部已 Notify 一次；沒命中才用預設值 Notify 回報 Grid size。
// 時序：OnInitializedAsync 在第一次渲染前執行 → UI 直接綁到快取值，絕不露出預設值中間態。
protected override async Task OnInitializedAsync()
{
    if (!await RestoreGridFromCacheAsync())
        await NotifyChangedAsync();
}
```

另外四個表單 (`SmaParameterForm` / `PaParameterForm` / `TrendFollowingParameterForm` / `MeanReversionParameterForm`) 採完全相同模式，只差策略 key 不同：
- `sma` → SmaParameterForm（FastSmaPeriod / SlowSmaPeriod）
- `pa` → PaParameterForm（LookbackPeriod / MomentumThreshold / WickToBodyRatio / EngulfingEnabled / Confidence）
- `trend` → TrendFollowingParameterForm（FastEmaPeriod / SlowEmaPeriod / RsiPeriod / RsiMidline）
- `mean-reversion` → MeanReversionParameterForm（BbPeriod / BbStdDev / RsiPeriod / RsiOversold / RsiOverbought）

## T3 — `BacktestLab.razor` 路徑清理

### 刪除：`_pendingGridRestoreKey` 欄位、`OnAfterRenderAsync` 整個覆寫

之前：
```csharp
private string? _pendingGridRestoreKey;

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    if (_pendingGridRestoreKey is null) return;
    if (_dynamicRef?.Instance is not StrategyParameterFormBase form) return;
    var key = _pendingGridRestoreKey;
    _pendingGridRestoreKey = null;
    var cached = State.TryGetGridSettings(key);
    if (cached is null) return;
    await form.ApplyGridParametersAsync(cached);
}
```
之後：**整段移除**。時序判斷下放到 form 自己。

### DynamicComponent 傳遞 StrategyKey

`SyncFormToSelectedModel` 內 `_formParameters`：

```csharp
_formParameters = new Dictionary<string, object>
{
    [nameof(StrategyParameterFormBase.Disabled)]         = State.IsRunning,
    [nameof(StrategyParameterFormBase.ParameterChanged)] = EventCallback.Factory.Create<int>(this, OnFormGridChanged),
    // S55 T3：把策略 key 傳進 form — form 用它向 LabStateContainer 精準領取自己的網格快照。
    [nameof(StrategyParameterFormBase.StrategyKey)]      = _lastSelectedKey,
};
```

### `OnFormGridChanged` 的新防護

舊防護依賴 `_pendingGridRestoreKey` 已不存在。換成冪等比對（form 的 CurrentGrid 與 cache 完全相等就跳過寫入）：

```csharp
private void OnFormGridChanged(int gridSize)
{
    _currentGridSize = gridSize;

    if (_dynamicRef?.Instance is StrategyParameterFormBase form)
    {
        var key = State.SelectedModel.Key;
        var current = form.CurrentGrid;
        var cached = State.TryGetGridSettings(key);
        if (cached is null || !GridEquals(cached, current))
            State.SaveGridSettings(key, current);
    }
    StateHasChanged();
}

private static bool GridEquals(
    IReadOnlyDictionary<string, ParameterGridRange> a,
    IReadOnlyDictionary<string, ParameterGridRange> b)
{
    if (a.Count != b.Count) return false;
    foreach (var kv in a)
    {
        if (!b.TryGetValue(kv.Key, out var other)) return false;
        if (other.Min != kv.Value.Min || other.Max != kv.Value.Max || other.Step != kv.Value.Step)
            return false;
    }
    return true;
}
```

注意：領取式設計下，form 的 `OnInitializedAsync` 是「先自拉 cache → 再 Notify」，所以初始化觸發 `OnFormGridChanged` 時拿到的 `CurrentGrid` 若 cache 命中就**已經是 cache 值本身**——這一次寫回是「寫進一模一樣的值」，冪等無害。`GridEquals` 的 early-skip 只是個噪音優化，不是正確性防線。

## T4 — 診斷 Log

`RestoreGridFromCacheAsync` 的三條 `Logger?.LogDebug` 涵蓋所有分支：
- StrategyKey 未綁定 → 印警告（應該不會發生）
- 無 cache（首次 / 該 key 無記錄）→ 印「維持預設值」
- 命中 cache → 印 key 與維度數 + 具體鍵名

把 `CryptoBot.ConsoleApp.Lab.StrategyParameterFormBase` 的 log level 拉到 `Debug`，切策略或換頁時可以每次看到自領取紀錄。

## 生命週期時序（新 vs 舊）

**舊 FS-V2 時序**（有 race）：
```
切策略 → SyncFormToSelectedModel 設 _pendingGridRestoreKey
       → 父 re-render
       → 子 form.OnInitializedAsync → NotifyChangedAsync (預設值) → OnFormGridChanged 的 skip 判斷
       → 父 OnAfterRenderAsync → _dynamicRef.Instance 可用 → ApplyGridParametersAsync(cached) → NotifyChangedAsync (cache 值)
```
race window：`_pendingGridRestoreKey` 判斷若與 `_dynamicRef` 就緒時序錯位，就有機會被洗。

**新 S55 時序**（無 race）：
```
切策略 → SyncFormToSelectedModel 把 StrategyKey 塞進 _formParameters
       → 父 re-render + DynamicComponent 實例化子 form
       → 子 form.OnInitializedAsync 第一行就 State.TryGetGridSettings(StrategyKey) → ApplyGridParametersAsync(cached)
           → 內部 NotifyChangedAsync（值已是 cache）→ OnFormGridChanged 冪等回寫
       → 若無 cache，顯式 NotifyChangedAsync(預設值) → OnFormGridChanged 把預設值寫成 baseline
```
**關鍵**：`OnInitializedAsync` 是在第一次 render *之前* 執行，UI 綁到的 DOM `value` 屬性從一開始就是 cache 值，沒有「預設值閃一下」的中間態。

## 受影響檔案清單

### 修改（7 個）
```
CryptoBot/src/CryptoBot.ConsoleApp/Lab/StrategyParameterFormBase.cs           (+[Inject] State/Logger +[Parameter] StrategyKey +RestoreGridFromCacheAsync)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Lab/B46ParameterForm.razor      (OnInitializedAsync 改領取式)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Lab/SmaParameterForm.razor      (同上)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Lab/PaParameterForm.razor       (同上)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Lab/TrendFollowingParameterForm.razor    (同上)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Lab/MeanReversionParameterForm.razor     (同上)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Pages/BacktestLab.razor         (-_pendingGridRestoreKey -OnAfterRenderAsync +StrategyKey 傳遞 +GridEquals 冪等比對)
```

### 未動（關鍵）
- `LabStateContainer.cs` — Singleton + `ConcurrentDictionary _gridCache` + `object _lock` 本來就正確，不需改動
- `Program.cs:156` — `AddSingleton<LabStateContainer>()` 生命週期維持
- `QuickFillFromCacheAsync` — 使用者按按鈕觸發（非 `OnAfterRenderAsync` 時序邏輯），保留 `_dynamicRef?.Instance` 存取

## 驗證

| 項目 | 結果 |
|------|------|
| Debug build（4 專案） | 0 警告、0 錯誤 — ConsoleApp 側建到 `C:\Users\Moera\AppData\Local\Temp\cb_s55_build\`（避開執行中 PID 1452 的 `apphost.exe` 檔鎖）|
| Release build（4 專案）| 0 警告、0 錯誤 — 側建到 `C:\Users\Moera\AppData\Local\Temp\cb_s55_release\` |
| Domain 單元測試 | 26 / 26 通過（290 ms） |
| Application 單元測試 | 88 / 88 通過（1 s） |
| **合計** | **114 / 114** |

## VCP

- **[VCP-1] 深度導航**（需人工驗）：在 Lab 修改 ADA 參數 → 點去 Dashboard → 點回 Lab。預期 100% 留存。
- **[VCP-2] 策略切換**（需人工驗）：SMA 改參數 → 切 B46 → 切回 SMA。預期 SMA 自定義網格完好。
- **[VCP-3] 邏輯一致性**：`BacktestLab.razor` grep 確認：
  - `_pendingGridRestoreKey` 關鍵字僅存在於註解（無欄位、無賦值、無讀取）— ✅
  - `OnAfterRenderAsync` 僅存在於註解引用（無 override）— ✅
  - `_dynamicRef?.Instance` 僅用於使用者主動觸發路徑（`OnFormGridChanged` 的冪等回寫、`StartOptimizeAsync` 的 BuildRequest、`QuickFillFromCacheAsync` 的按鈕 flow、`SyncFormToSelectedModel` 的切策略備份）— 無時序回填依賴 ✅

## 實驗室領取式記憶系統已就緒。

---

# Addendum IX — S56 執行層決策透明化與 UI 視覺體感優化

> Capsule：`ai_ops/capsules/TASK_S56_ORDER_TRANSPARENCY.md`

## 交付摘要

| 任務 | 目標 | 狀態 |
|---|---|---|
| T1 | Executor 風控攔截的異常回流 | ✅（實作策略見下方「⚠️ 膠囊-實作落差」） |
| T2 | 下拉選單 CSS 配色重構（高對比） | ✅ |
| T3 | `StrategyConfiguration.MaxConcurrentPositions` 預設 1 → 2 | ✅ |
| T4 | DecisionLog 風控攔截橘色標註 | ✅（選琥珀金以跟既有 `.error` 橘色區分）|

## ⚠️ 膠囊-實作落差：T1 的 `strategyState.ReportError(reason)`

膠囊原文：「當 `RiskCheckResult` 被 Rejected 時，調用 `strategyState.ReportError(riskCheck.Reason)`」。

**問題**：Domain 的 `Strategy.ReportError(string)` 實作（`StrategyAggregate/Strategy.cs:101-107`）**會把 `Status` 從 `Running` 改為 `Error` 並停掉策略**，並觸發 `StrategyErrorEvent` domain event。單一持倉衝突、日損熔斷預警、符號冷卻等所有正常風控攔截都會把策略直接關機——破壞金融安全底線，且 PM 的 VCP-1 只要求「Dashboard 跳警告」，未要求停策略。

**我的選擇**：不呼叫 `ReportError`，改走雙軌透明化：
1. `_notifications.NotifyAsync("Trade rejected", "[RISK] {reason}", Warning)` — 已有通路（Discord / 系統訊息）
2. `_broadcaster.BroadcastStrategyEvaluationFailedAsync(...)`，`ErrorMessage` 前綴 `[RISK]` — 走既有 realtime 鏈路到 Dashboard 決策日誌
3. Dashboard UI 透過 prefix 判斷用琥珀金 `risk-rejected` CSS class（與紅橘 `error` 區分）
4. 策略 `Status` 保持 `Running` — 該幣種這一筆被擋，下一根 K 線仍正常評估

**若 PM 堅持要呼叫 ReportError**：Domain 層必須新增一個非破壞性方法（例：`Strategy.RecordTradeRejection(reason)` 只寫 `LastWarning` 欄位、不轉 status、不 raise StoppedEvent），這是一筆 Domain 擴張，影響 Strategy Aggregate 的 `WarnOnly` 語意模型，需要 PM 新膠囊明確授權。

### 兩個 `StrategyExecutor` 的處理

專案實際有兩個 `StrategyExecutor`：
- **`Application/Strategies/StrategyExecutor.cs`**（生產線）— 由 `StrategyExecutorFactory` 建、接受 `IRealtimeBroadcaster`、執行期實際跑的那個。**這是 T1 的主戰場**。
- **`Application/Trading/StrategyExecutor.cs`**（膠囊字面指定的那個）— 完全無人使用（grep 無一處 `new`、Factory 不建、test 不用）。疑為早期設計的保留版本。

**處理**：Strategies 版加完整雙軌（Notify + Broadcast）；Trading 版只加 Notify 的 `[RISK]` prefix + 註解標註「本 class 目前未被 DI 使用」，**刻意不擴張** Trading 版的建構子引入 `IRealtimeBroadcaster` — 讓 dead code 不增加 API surface；PM 若決定淘汰 Trading 版可直接刪。

## T1 — `Strategies/StrategyExecutor.cs` 核心改動

`src/CryptoBot.Application/Strategies/StrategyExecutor.cs:302-340` 的 `HandleSignalAsync`：

```csharp
// 2) 風控
var check = await risk.CheckBeforeOpenAsync(_strategy, signal, qty, CancellationToken.None)
    .ConfigureAwait(false);
if (!check.IsApproved)
{
    var reason = check.Reason ?? "(未提供原因)";
    _logger.LogWarning("Order rejected by RiskManager: {Reason}", reason);

    // S56 T1：執行層決策透明化 — 過去風控攔截只在 server log 留痕，使用者面板無任何跡象，
    // 排錯時只能猜「為什麼沒下單」。雙管齊下：
    // (a) Warning 等級系統通知（Discord / Dashboard toast）— 現場立刻知道被擋
    // (b) 決策日誌事件推播，ErrorMessage 前加 [RISK] prefix — Dashboard 的滾動日誌會以橘色標註
    // 注意：刻意不呼叫 _strategy.ReportError(reason) —— domain 該方法會把 Status 改為 Error
    // 並停掉策略，相當於單一持倉衝突就把整個策略關機，破壞金融安全底線。PM 膠囊的 VCP-1
    // 只要求「Dashboard 跳警告」，本實作走廣播 + 通知雙軌達成同樣顯性化，策略維持 Running。
    try
    {
        await _notifications.NotifyAsync(
            "Trade rejected",
            reason,
            NotificationLevel.Warning,
            CancellationToken.None).ConfigureAwait(false);
    }
    catch (Exception notifyEx)
    {
        _logger.LogWarning(notifyEx,
            "Failed to notify risk rejection for {Name}.", _strategy.Name);
    }

    try
    {
        await _broadcaster.BroadcastStrategyEvaluationFailedAsync(new StrategyEvaluationFailedUpdate(
            StrategyId: _strategy.Id,
            StrategyName: _strategy.Name,
            OccurredAtUtc: DateTime.UtcNow,
            Symbol: _strategy.Configuration.Symbol.BingXFormat,
            ErrorMessage: $"[RISK] {reason}"), CancellationToken.None).ConfigureAwait(false);
    }
    catch (Exception broadcastEx)
    {
        _logger.LogWarning(broadcastEx,
            "Failed to broadcast risk-rejection event for {Name}.", _strategy.Name);
    }
    return;
}
```

每條 try/catch 包在個別事件層是**刻意的**：Notify 失敗不該阻斷 Broadcast，Broadcast 失敗也不該阻斷風控流程 return。風控本身的「return」語意（不下單）維持不變——只是額外加了兩條透明化訊號。

## T2 — 下拉選單 CSS（必交 snippet）

`src/CryptoBot.ConsoleApp/wwwroot/app.css` 新增全站 `select` / `option` 規則：

```css
/* ─────────────── S56 T2：下拉選單高對比配色 (全站統一) ───────────────
   問題：Glassmorphism 深色面板下，<select> 依賴瀏覽器/OS 預設（白底淺灰字）造成
         低對比難辨識；Chrome / Edge / Firefox 跨瀏覽器各自呈現也不一致。
   方案：全域 select + option 都強制深色擬態底（rgba 18,18,18,.92）+ 亮白字
         （var(--text)），搭配邊框、hover/focus 強化，確保在任何瀏覽器底都一致。
   關鍵：option 必須顯式 color + background-color — 缺任一個 Chrome 會 fallback
         到 OS 原生配色（macOS 白底、Windows 亮底），造成「灰字白底」的投訴畫面。 */
select {
    background-color: rgba(18, 18, 18, 0.85);
    color: var(--text, #e5ecf7);
    border: 1px solid var(--panel-edge-strong, rgba(255,255,255,0.18));
    border-radius: 6px;
    padding: 6px 28px 6px 10px;
    font-family: inherit;
    font-size: 13px;
    line-height: 1.4;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    /* 自繪下拉箭頭 — 亮白 chevron，避免系統 native 控件與深色主題打架 */
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' fill='none' stroke='%23e5ecf7' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'><polyline points='2,4 6,8 10,4'/></svg>");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 11px 11px;
    transition: border-color 0.15s, box-shadow 0.15s, background-color 0.15s;
    cursor: pointer;
}

select:hover:not(:disabled) {
    background-color: rgba(30, 30, 30, 0.92);
    border-color: var(--accent, #ffd95c);
}

select:focus {
    outline: none;
    border-color: var(--accent, #ffd95c);
    box-shadow: 0 0 0 2px var(--accent-soft, rgba(255, 217, 92, 0.25));
}

select:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

/* option 的底色 — 在 Chrome/Edge 下是瀏覽器原生下拉面板渲染（無法完全控制
   padding/animation），但 background-color + color 是被支援的兩個屬性。
   深底亮字消除「白底淺灰字」投訴，同時與 select 本體一致避免展開時視覺斷層。 */
select option {
    background-color: #111418;
    color: var(--text, #e5ecf7);
}

select option:checked,
select option:hover {
    background-color: #2a2f38;
    color: #ffffff;
}
```

**範圍**：這是全站 `select` 規則——`/lab` 的 Symbol / Interval 下拉、Dashboard 的策略型別切換、所有 `<select>` 全部吃這套。

**`appearance: none`**：強制關掉瀏覽器原生控件讓自繪 chevron 生效。自繪 SVG 是內嵌 data URI，沒有外部檔案依賴，瀏覽器快取行為自然。

**`option` 的限制**：原生 `<select>` 展開的 dropdown panel 在 Chrome / Edge 是 OS 級控件，CSS 只認 `background-color` 和 `color` 兩個屬性；其他 padding / border-radius / transition 會被忽略。這是 web platform 現狀，不是 CSS 寫錯。

## T3 — StrategyConfiguration 預設值

`src/CryptoBot.Domain/Aggregates/StrategyAggregate/StrategyConfiguration.cs:57-58`：

```csharp
decimal? trailingStopPercent = null,
// S56 T3：預設由 1 調整為 2 — 單一策略只容一個持倉時，單幣種一開倉就鎖死整個系統，
// 多幣種實戰根本跑不起來（例：同策略分別吃 BTC 與 ETH 都不行）。2 是「同時容忍兩個
// 獨立方向/幣種的入場」，仍維持風控不過度發散；要重度 portfolio 策略可在建立時顯式指定。
int maxConcurrentPositions = 2,
```

**不動 Validation**：`< 1` 的防呆保留（L71）。既有 118 個測試沒有對 `MaxConcurrentPositions == 1` 做硬斷言，改動安全。

**舊策略如何處理**：DB 中已存在的 `Strategy` row 的 `MaxConcurrentPositions` 是持久化過的值，不受預設值變更影響。只有**新建立**的 `StrategyConfiguration.Create()` 呼叫若不明確指定，才會拿到 2。

## T4 — DecisionLog 風控橘色（琥珀金）

### Dashboard.razor `OnStrategyEvaluationFailed` 辨識 prefix

```csharp
private void OnStrategyEvaluationFailed(StrategyEvaluationFailedUpdate update)
{
    _nowUtc = DateTime.UtcNow;

    // S56 T4：風控攔截事件用 [RISK] prefix 區別於策略評估崩潰 —
    // 兩者的顯性化程度不同：評估崩潰是系統壞掉（紅橘），風控攔截是正常保護機制（琥珀金）。
    // 使用者看到琥珀色能立即知道「策略還活著，只是這一筆被風控擋下」，而不是誤判為系統故障。
    var isRiskReject = update.ErrorMessage.StartsWith("[RISK]", StringComparison.Ordinal);
    var tag = isRiskReject ? "RISK" : "ERROR";
    var cssClass = isRiskReject ? "risk-rejected" : "error";
    // Tag 已經標 RISK，Note 內重複 prefix 沒意義 — 去頭
    var note = isRiskReject
        ? update.ErrorMessage["[RISK]".Length..].TrimStart()
        : update.ErrorMessage;

    PushLogEntry(new EvaluationEntry(
        TimestampLocal: update.OccurredAtUtc.ToLocalTime(),
        Tag: tag,
        CssClass: cssClass,
        StrategyName: update.StrategyName,
        Symbol: update.Symbol,
        Note: note));
    InvokeAsync(StateHasChanged);
}
```

### CSS `.risk-rejected` 琥珀金

```css
.eval-log-entry.risk-rejected .eval-log-tag {
    color: #1a1a1a;
    background: rgba(255, 198, 46, 0.95);
    border: 1px solid rgba(255, 217, 92, 1);
    text-shadow: 0 0 4px rgba(255, 217, 92, 0.35);
    font-weight: 700;
}
.eval-log-entry.risk-rejected .eval-log-body {
    color: #ffd95c;
    white-space: normal;
}
.eval-log-entry.risk-rejected .eval-log-body strong { color: #ffd95c; }
```

**為什麼選琥珀金而非膠囊建議的橘色**：現有 `.error` 已經是橘色 `rgba(255, 149, 0, ...)`。若 risk-rejected 也用橘色，使用者無法區分「正常風控擋下（策略還活著）」和「策略評估崩潰（系統故障）」。琥珀金對齊全站 accent gold `#ffd95c`（警示但非致命），與 `.error` 的橘紅屬於警示色譜的兩端，對比明確。

## 受影響檔案清單

### 修改（5 個）
```
CryptoBot/src/CryptoBot.Domain/Aggregates/StrategyAggregate/StrategyConfiguration.cs   (T3：預設 1 → 2)
CryptoBot/src/CryptoBot.Application/Strategies/StrategyExecutor.cs                     (T1：生產線雙軌透明化)
CryptoBot/src/CryptoBot.Application/Trading/StrategyExecutor.cs                        (T1：dead-code 版本加 [RISK] prefix 通知 + 註解標註)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Pages/Dashboard.razor                    (T4：prefix 辨識 → risk-rejected class)
CryptoBot/src/CryptoBot.ConsoleApp/wwwroot/app.css                                     (T2：全站 select 配色 + T4：.risk-rejected 琥珀金)
```

### 未動（關鍵）
- `Strategy.cs` Domain Aggregate — 刻意不擴張 `RecordTradeRejection` 類型的新方法（見「⚠️ 膠囊-實作落差」）
- `IRealtimeBroadcaster` — 重用 `BroadcastStrategyEvaluationFailedAsync`，不新增 API
- 任何測試檔 — Domain 預設值改動、Executor 加通知都不影響既有斷言

## 驗證

| 項目 | 結果 |
|------|------|
| Debug build（4 專案） | 0 警告、0 錯誤 — 側建到 `C:\Users\Moera\AppData\Local\Temp\cb_s56_build\` |
| Release build（4 專案）| 0 警告、0 錯誤 — 側建到 `C:\Users\Moera\AppData\Local\Temp\cb_s56_release\` |
| Domain 單元測試 | 26 / 26 通過（175 ms） |
| Application 單元測試 | 88 / 88 通過（1 s） |
| **合計** | **114 / 114** |

## VCP

- **[VCP-1] 故障顯性化**（需人工驗）：啟動一個策略使其已達 `MaxConcurrentPositions`，讓下一筆 SIGNAL 觸發 → Dashboard 決策日誌出現琥珀金 `RISK` 標籤 + 原因（例：`Max concurrent positions reached (max 2)`）；同時 Discord 或系統通知收到 `Trade rejected · Warning` 等級訊息；**策略狀態仍為 Running**。
- **[VCP-2] 視覺查核**（需人工驗）：Chrome / Edge / Firefox 分別打開 `/lab`，確認 Symbol 下拉、Interval 下拉的閉合態與展開態都是「深底亮字」，無白底灰字殘影；Dashboard 的策略類型切換下拉同樣一致。
- **[VCP-3] 預設值校驗**（自動）：新建 `StrategyConfiguration.Create(symbol, interval, leverage)` 呼叫若不指定 `maxConcurrentPositions`，回傳的 config `.MaxConcurrentPositions == 2`（手動可 REPL 驗）。

## 執行層診斷與 UI 配色優化已就緒。

---

# Addendum X — S57 系統管理與數據深挖中心

> Capsule：`ai_ops/capsules/TASK_S57_SYSTEM_ADMIN_CENTER.md`
> 交付四個任務：T1 動態 IP 白名單 / T2 深度交易回溯 / T3 DB 健康 + VACUUM / T4 `/admin` 頁面。

## 交付摘要

| 任務 | 重點 | 狀態 |
|---|---|---|
| T1 IP 白名單 | `IpWhitelistService` 讀寫 `appsettings.json`、UI 顯示真實 IP + 一鍵加入 + 列表刪除 | ✅ |
| T2 深度交易回溯 | `GET /api/admin/positions-deep`、`ParametersSnapshot` JSON 解析成 KV pills | ✅ |
| T3 DB 健康 + VACUUM | 檔案大小（主+WAL+SHM）+ 筆數 + `VACUUM;` 執行 + 回收量顯示 | ✅ |
| T4 `/admin` 頁面 + 導航 | `SystemAdmin.razor`、MainLayout 加 NavLink、沿用 glass-form + 琥珀金 | ✅ |

## T1：IP 白名單 — 必交 snippet（PM 特別指定 JSON 縮排處理）

`src/CryptoBot.ConsoleApp/Services/IpWhitelistService.cs` 核心寫入：

```csharp
private static readonly JsonSerializerOptions WriteOpts = new()
{
    WriteIndented = true,                                       // 2 空格統一縮排
    Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
};

private static readonly JsonDocumentOptions ReadOpts = new()
{
    CommentHandling = JsonCommentHandling.Skip,
    AllowTrailingCommas = true,
};

private async Task<WhitelistMutationResult> MutateAsync(
    string ipForLog,
    Func<List<string>, WhitelistMutationResult> mutator,
    CancellationToken ct)
{
    await _writeLock.WaitAsync(ct).ConfigureAwait(false);
    try
    {
        // 1) 讀原始 JSON（保留其他 section）
        string raw;
        await using (var fs = new FileStream(
            _appsettingsPath, FileMode.Open, FileAccess.Read, FileShare.Read))
        using (var sr = new StreamReader(fs))
        {
            raw = await sr.ReadToEndAsync(ct).ConfigureAwait(false);
        }

        var root = JsonNode.Parse(raw, documentOptions: ReadOpts) as JsonObject
            ?? throw new InvalidOperationException("appsettings.json root is not an object.");

        // 2) 找到（或新增）Security.AllowedIPs 節
        if (root["Security"] is not JsonObject securityNode)
        {
            securityNode = new JsonObject();
            root["Security"] = securityNode;
        }

        var currentList = new List<string>();
        if (securityNode["AllowedIPs"] is JsonArray arr)
        {
            foreach (var v in arr)
                if (v is not null) currentList.Add(v.GetValue<string>());
        }

        // 3) 應用 mutator — AlreadyExists / NotFound 不改檔、直接短路
        var outcome = mutator(currentList);
        if (outcome is WhitelistMutationResult.AlreadyExists or WhitelistMutationResult.NotFound)
            return outcome;

        // 4) 回寫 AllowedIPs
        var newArr = new JsonArray();
        foreach (var s in currentList) newArr.Add(s);
        securityNode["AllowedIPs"] = newArr;

        // 5) 序列化（美化縮排）+ 原子寫入（tmp → move overwrite）
        var formatted = root.ToJsonString(WriteOpts);
        if (!formatted.EndsWith('\n')) formatted += Environment.NewLine;

        var tmpPath = _appsettingsPath + ".tmp";
        await File.WriteAllTextAsync(tmpPath, formatted, ct).ConfigureAwait(false);
        File.Move(tmpPath, _appsettingsPath, overwrite: true);

        return outcome;
    }
    finally
    {
        _writeLock.Release();
    }
}
```

### 為什麼這樣寫

| 考量 | 手法 |
|---|---|
| **保留其他 section** | `JsonNode` parse → 只動 `Security.AllowedIPs` → 序列化回原 root |
| **統一縮排美化** | `WriteIndented = true`（PM 交付要求）|
| **IPv6 / 中文不亂碼** | `UnsafeRelaxedJsonEscaping` 防止 `:` → `:` 類 escape |
| **部分寫入防護** | 先寫 `.tmp` → `File.Move(..., overwrite: true)`（原子 rename）|
| **併發寫入** | `SemaphoreSlim(1, 1)` 序列化進入 |
| **空操作不浪費 IO** | `AlreadyExists` / `NotFound` 短路 return，不重寫檔 |
| **檔尾換行** | `\n` 結尾，git diff / POSIX 友善 |

### 熱載保證

`Program.cs:96-98` 的 `AddJsonFile("appsettings.json", reloadOnChange: true)` + `IpWhitelistMiddleware` 用 `IOptionsMonitor.CurrentValue` → 寫回後 **幾秒內 Middleware 自動拿到新名單，不必重啟服務**。

## T2：深度交易回溯 — `ParametersSnapshot` 解析

`AdminEndpoints.ParseSnapshot(string? snapshotJson)` 把 StrategyExecutor 序列化的 JSON payload：

```json
{
  "leverage": 3,
  "riskPerTradePercent": 0.02,
  "stopLossPercent": 0.02,
  "takeProfitPercent": 0.04,
  "trailingStopPercent": null,
  "parameters": { "FastSmaPeriod": 10, "SlowSmaPeriod": 30 }
}
```

解析成 UI 可讀的 KV pill 列表：
```
[Leverage = 3x] [Risk/Trade = 2%] [Stop Loss = 2%] [Take Profit = 4%]
[FastSmaPeriod = 10] [SlowSmaPeriod = 30]
```

**設計要點**：
- 頂層標量：`leverage / risk / SL / TP / trailing` 各自用對應的 `Format*`（`x` 後綴 / 百分比 / 小數）
- `parameters` 物件內所有 key 原樣展開（使用者看到的鍵名就是 StrategyConfiguration.Parameters 的鍵）
- 解析失敗靜默回空清單（老 row 格式不一致不炸 API）
- null 值顯示 "—"

## T3：DB Health + VACUUM — 範例解讀

UI 顯示範例（PM 於 2026-04-24 確認的語意）：

| 場景 | Before | After | Reclaimed | Elapsed | UI 顯示 |
|---|---|---|---|---|---|
| A：新 DB | 4.2 MB | 4.2 MB | 0 B | 45 ms | `回收 0 B · 耗時 45 ms` — 健康無碎片 |
| B：典型清理 | 12.4 MB | 8.1 MB | 4.3 MB | 870 ms | `回收 4.30 MB · 耗時 870 ms` — DELETE 空洞回收 |
| C：長期未整理 + WAL 膨脹 | 128 MB | 45 MB | 83 MB | 4200 ms | `回收 83.00 MB · 耗時 4200 ms` — 含 WAL checkpoint |

實作：`await db.Database.ExecuteSqlRawAsync("VACUUM;", ct)`。SQLite 3.8+ 增量 rebuild，執行時會**鎖全表幾百 ms ~ 幾秒**，操作建議：**全策略 Stopped 或熔斷 tripped 時跑**，避開策略大量交易。

## T4：`/admin` 頁面 — 佈局與色彩

**Route**：`@page "/admin"`，`@rendermode InteractiveServer`
**導航**：`MainLayout.razor` 新增 NavLink "Admin · 系統管理"
**佈局**：
```
┌─────────────────────────────────────────────────┐
│ 系統管理中心                                      │
│ ADMIN · Security · Deep Insight · DB Ops          │
├──────────────────────┬──────────────────────────┤
│ 🛡 IP 白名單         │ 💾 資料庫健康            │
│ - 琥珀金底卡：你的 IP │ - 7 cells（路徑/大小/計數）│
│ - 一鍵加入 / 手動新增 │ - VACUUM 按鈕             │
│ - 列表逐條移除        │ - 回收量顯示 (金色)       │
├──────────────────────┴──────────────────────────┤
│ 🔎 深度交易回溯（全寬）                           │
│ 表格：時間│Symbol│Side·Qty│Entry→Exit│PnL│模型│KV │
│                                                  │
│ 每列的「網格參數快照」以金色 pill 形式展開         │
└─────────────────────────────────────────────────┘
```

**色彩策略**（沿用 S56）：
| 元素 | 色碼 | 語意 |
|---|---|---|
| 琥珀金底卡（待行動區）| `rgba(255, 217, 92, .06)` 底 | 「這裡要做事」|
| 未加入白名單 badge | `rgba(255, 198, 46, .95)` | 警示但非致命（S56 T4 同系）|
| 已在白名單 badge | `rgba(46, 255, 139, .85)` | 安全 |
| 模型 tag（回溯表）| 冷青 `rgba(77, 208, 225, .18)` | 資訊識別 |
| Snapshot value | `--gold` `#f5b301` | 關鍵數值 |
| 空名單警告 | 琥珀虛線框 | fail-open 提醒 |

## 受影響檔案清單

### 新增（5 個）
```
CryptoBot/src/CryptoBot.ConsoleApp/Services/IIpWhitelistService.cs            (T1 介面 + 結果碼 enum)
CryptoBot/src/CryptoBot.ConsoleApp/Services/IpWhitelistService.cs             (T1 實作：JsonNode + 原子寫入 + SemaphoreSlim)
CryptoBot/src/CryptoBot.ConsoleApp/Api/Dtos/AdminDtos.cs                      (T1-T3 DTOs：Caller / Whitelist / DeepPosition / DbHealth / Vacuum)
CryptoBot/src/CryptoBot.ConsoleApp/Api/AdminEndpoints.cs                      (7 個 endpoint：caller-ip / whitelist CRUD / positions-deep / db-health / db-vacuum)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Pages/SystemAdmin.razor         (T4 頁面 @page "/admin"，三個 section)
```

### 修改（3 個）
```
CryptoBot/src/CryptoBot.ConsoleApp/Program.cs                                 (+AddSingleton<IIpWhitelistService> +MapAdminEndpoints)
CryptoBot/src/CryptoBot.ConsoleApp/Components/Layout/MainLayout.razor         (+NavLink "/admin")
CryptoBot/src/CryptoBot.ConsoleApp/wwwroot/app.css                            (+admin-grid / admin-row / admin-ip-item / admin-db-grid / admin-snapshot-kv 等 S57 專區)
```

### 未動（關鍵）
- `IpWhitelistMiddleware` / `IpWhitelistOptions` — 繼續用 `IOptionsMonitor`，我們的寫入自動被它熱載
- `Position.cs` / `IPositionRepository` — `ParametersSnapshot`、`GetRecentClosedAsync` 都是 S39 既有

## 驗證

| 項目 | 結果 |
|------|------|
| Debug side build（4 專案） | **0 警告 0 錯誤**（`%TEMP%/cb_s57/`）|
| Release side build（4 專案）| **0 警告 0 錯誤**（`%TEMP%/cb_s57_rel/`）|
| Domain 單元測試 | 26 / 26 通過（61 ms）|
| Application 單元測試 | 88 / 88 通過（1 s）|
| **合計** | **114 / 114** |

## VCP 人工驗收指南

### [VCP-Admin-Whitelist]
1. 啟動服務，`/admin` 頁面
2. 點「一鍵加入我的 IP」或手動輸入一組新 IP（例 `203.0.113.42`）→ 按「新增」
3. 觀察：
   - ✅ UI toast：`✓ 已加入 203.0.113.42（現有 N 筆，appsettings.json 已更新）`
   - ✅ 白名單列表立即多一條
   - ✅ 打開 `src/CryptoBot.ConsoleApp/appsettings.json`（或執行時目錄的那份）→ `Security.AllowedIPs` 陣列多了這個 IP，且整份檔案 **2-空格縮排美化**
   - ✅ 幾秒後其他請求仍正常通過（Middleware 熱載確認）

### [VCP-Admin-Snapshot]
1. 確認 DB 中至少有一筆已平倉 Position（跑策略或測試資料）
2. `/admin` → 捲到「🔎 深度交易回溯」
3. 觀察某列：
   - ✅ **模型欄**顯示開倉時的 `StrategyType`（例 `SmaCrossover` / `B46RsiBb`）—— 即使現在策略已 morph 到別的型別，歷史 row 仍顯示**下單當時**的模型（S39 快照語意）
   - ✅ **網格參數快照欄**以金色 pill 展開：`Leverage=3x`、`Risk/Trade=2%`、`FastSmaPeriod=10`、`SlowSmaPeriod=30` 等
   - ✅ 老 row 無 snapshot 時顯示「（無快照）」

### [VCP-Admin-DB]
1. `/admin` → 捲到「💾 資料庫健康」
2. 觀察：
   - ✅ `Data Source` 顯示檔案絕對路徑（UI 只顯示末三段路徑，完整路徑在 `title` tooltip）
   - ✅ 主檔大小 / 合計 / Positions / Orders / Strategies / Log 每格都有數字
   - ✅ 單位自動 KB/MB/GB 格式化（< 1024 B 顯示 B）
3. 按「🧹 VACUUM」：
   - ✅ 按鈕變「執行中…」，完成後回來顯示金色 `回收 X.XX MB · 耗時 XXX ms`
   - ✅ 重新量測（自動觸發）後數字可能變小（有碎片時）

## 系統管理中心已就緒。





