# CryptoBot Institutional Memory (制度記憶)

> **用途**：將先前踩過的坑轉化為可傳承的制度資產。看到相似症狀時先翻這份、再動手。
> **維護原則**：每一條都有「症狀 → 根因 → 診斷 → 修法 → 預防」五段，讓後手能在 30 秒內判斷要不要走這條。
> **版本歷史**：2026-04-24 建立（涵蓋 S61 / S62 / S63 系列教訓）。

---

## L1 · BingX 精度解析陷阱（來源：S62）

### 症狀
- `OrderSizer.ComputeAsync` 對任何小於 1 的下單量都回傳 `Quantity.Zero`
- `s60_check-kline` 或 DiagnosticTool `size` 指令顯示 `StepSize=4` 之類的整數值，而非 `0.0001` 合理小數
- Dashboard 日誌出現 `[SIZE] aligned qty 0 < minQuantity ...` 連續告警

### 根因
`JK.BingX.Net` SDK 的 `BingXContract.QuantityPrecision` 與 `PricePrecision` **是「小數位數」(int)**，例如 `4` 代表 4 位小數；**不是「步進值」(StepSize)**。老版 `BingXExchangeClient.GetTradingRulesAsync` 的 fallback 鏈把 `QuantityPrecision` 直接當 `StepSize` 餵進 `SymbolTradingRules` → `OrderSizer` 做 `Math.Floor(rawQty / 4) * 4` → 任何 rawQty < 4 的都歸零。

### 診斷三步
1. 在 DB 或內存快取打印當前 `SymbolTradingRules.StepSize`。若為 `2` / `4` / `6` 等整數 → 命中此陷阱。
2. 比對交易所官網規格（如 BTC-USDT 永續應為 `0.0001`）。
3. 檢查 `BingXExchangeClient.GetTradingRulesAsync` 的 stepSize 來源 — 是否讀到了 `*Precision` 屬性。

### 修法
優先使用**真實步進屬性**（讀到 >0 才採用），否則把 precision 轉換：

```csharp
// 先讀真正的步進
decimal stepSize = TryReadDecimal(() => (decimal?)dc.QuantityStep)
                ?? TryReadDecimal(() => (decimal?)dc.StepSize)
                ?? 0m;
// 都沒 → 讀 precision 轉 10^(-n)
if (stepSize <= 0m)
{
    var n = TryReadInt(() => (int?)dc.QuantityPrecision) ?? -1;
    if (n >= 0) stepSize = PrecisionToStep(n);
}

private static decimal PrecisionToStep(int precision)
{
    if (precision < 0) return 0m;
    if (precision == 0) return 1m;
    decimal step = 1m;
    for (int i = 0; i < precision; i++) step /= 10m;  // 不用 Math.Pow 避免 double 漂移
    return step;
}
```

### 預防
- 新增 `TradingRules` 相關 fallback 前先做功課：該 SDK 屬性名對應「步進」還是「精度」？
- 任何時候讀到 StepSize 為整數立刻警覺。
- 寫單元測試：precision=0 → 1、precision=4 → 0.0001、precision=-1 → 0。

---

## L2 · K 線 CloseTime 寫死 +1 秒（來源：S63-HOTFIX）

### 症狀
- MTF 對齊自檢永遠輸出 `MISALIGNED`，即使資料完全正確
- `TrimInProgressTail` 防未來函數機制失效 — 明明有「進行中」K 線卻沒被切掉
- 回測或策略歷史有詭異的時序判斷錯誤

### 根因
`BingXExchangeClient.GetKlinesAsync` 的 REST 路徑把所有週期的 `CloseTime` 寫死為 `openTime.AddSeconds(1)`。`Kline.CloseTime` 只比 `OpenTime` 多 1 秒 → 任何 `CloseTime > DateTime.UtcNow` 的判斷永遠為 false → 防未來函數完全失效。WebSocket 路徑本來就用 `interval.ToTimeSpan()` 是正確的，唯獨 REST 這條錯。

### 診斷兩步
1. 在 `CheckMtfCommand` 或任何會印 K 線範圍的地方，觀察 CloseTime - OpenTime 是否 = interval 真實長度。若只相差 1 秒 → 命中。
2. 檢查 `BingXExchangeClient.GetKlinesAsync` 的 CloseTime 計算是否呼叫 `interval.ToTimeSpan()`。

### 修法
```csharp
var span = interval.ToTimeSpan();  // 已存在的 KlineIntervalExtensions
foreach (var k in result.Data.OrderBy(x => x.Timestamp))
{
    var openTime = k.Timestamp;
    var closeTime = openTime + span;
    // ...
}
```

### 預防
- 跨時序邏輯（對齊、in-progress 檢測、回測重播）的新增代碼，先確認 `Kline.CloseTime` 是正確推算的。
- 單元測試應驗證多個 interval 的 `CloseTime - OpenTime == interval.ToTimeSpan()`。
- 若未來新增 REST 資料源（其他交易所），比照 `KlineIntervalExtensions.ToTimeSpan()` 同一函式產出 CloseTime，不要再各自寫死。

---

## L3 · 中文字串編譯期腐蝕（來源：S63-UX-BOM）

### 症狀
- 終端機輸出中文呈現 `` 或奇怪符號 / 方塊
- 加了 `Console.OutputEncoding = System.Text.Encoding.UTF8;` **依然亂碼**（關鍵線索）

### 根因
在繁體中文 Windows 環境下，若 `.cs` 原始碼檔**不帶 UTF-8 BOM**，C# 編譯器 `csc.exe` 會 fallback 到系統 OEM / ANSI codepage（zh-TW 的 cp950/Big5）讀取。UTF-8 的中文字串 bytes 被誤當 Big5 雙字節解碼 → 存進 DLL metadata 的 UTF-16 字串本身就是亂碼 → Console 設 UTF-8 也只是把亂碼忠實印出來。

### 診斷兩步
1. 驗證 DLL 內字串。用 PowerShell 讀取 DLL 內「某個預期的中文字串」UTF-16 LE bytes 是否匹配：
   ```powershell
   $bytes = [System.IO.File]::ReadAllBytes("YourAssembly.dll")
   $hex = [System.BitConverter]::ToString($bytes).Replace("-","").ToLower()
   # 例如「落在」UTF-16 LE = 3d 84 28 57
   $hex.IndexOf("3d842857") -ge 0
   ```
   若為 `False` → 編譯期就已腐蝕。
2. 用 `head -c 3 file.cs | od -An -tx1` 檢查每個含中文的 `.cs` 檔是否有 `ef bb bf` 前綴。

### 修法
**方案 A（首選）**：給每個含中文字串的 `.cs` 檔補 UTF-8 BOM：
```bash
for f in Commands/*.cs Program.cs ...; do
  tmp="$f.bomtmp"
  printf '\xef\xbb\xbf' > "$tmp"
  cat "$f" >> "$tmp"
  mv "$tmp" "$f"
done
```

**方案 B（系統級根治）**：Windows 11 → 設定 → 時間與語言 → 語言與地區 → 系統管理語言設定 → 勾選「Beta：使用 Unicode UTF-8 提供全球語言支援」→ 重啟。全系統 ANSI codepage = 65001，之後編譯 / agent spawn / CMD 全鏈路預設 UTF-8。

### 預防
- 新建任何含中文 `Console.WriteLine` 或字串常數的 `.cs` 檔，**寫完立刻補 BOM**（專案 workflow 已成既有慣例）。
- `Console.OutputEncoding = UTF8;` 仍應保留作為執行期防線，但要意識到：它**只解決輸出端編碼**，解不了**編譯期已被腐蝕的字串**。
- 若 agent（Gemini、VS Code extension）代跑輸出亂碼但直接 cmd 正常 — 不是原始碼問題，是 agent 重導向 stdout時用錯 codepage，屬於 agent 端設定問題，源端無法根治。

---

## L4 · `dynamic` 會被 SDK `internal` 類別封鎖（來源：S61-HOTFIX）

### 症狀
- 使用 `dynamic` 呼叫第三方 SDK 方法在執行期拋 `Microsoft.CSharp.RuntimeBinder.RuntimeBinderException`：
  > `'XXX' does not contain a definition for 'YYY'`
- 但同一個方法用**靜態型別**直接呼叫卻完全正常

### 根因
.NET DLR runtime binder **看不到 `internal` 類別的成員**，即使方法簽名完全對得上也會綁定失敗。
`JK.BingX.Net` v3.10.0 的許多 API 具體實作類別（如 `BingXRestClientPerpetualFuturesApiTrading`）是 `internal`，靜態型別呼叫因為有 public 介面或 partial public contract 所以能通過編譯並正常執行，但 dynamic 從使用端的組件視角看過去，看到的是 internal 牆 → 綁定失敗。

### 診斷
若 `dynamic` 呼叫拋 `RuntimeBinderException`，先別懷疑方法不存在，先試靜態型別呼叫。能過就是這個原因。

### 修法
**棄用 dynamic，一律靜態呼叫**。若方法名 / 欄位名未知，寧願讓編譯器報錯（在本機即時修正）也不要用 dynamic 當容錯層 — 容錯層會掩蓋 `internal` 綁定失敗，導致生產時靜默回空集合。

```csharp
// ❌ 錯示範：dynamic 在 internal SDK 實作下會運行期拋 RuntimeBinderException
dynamic trading = _client.PerpetualFuturesApi.Trading;
var task = (Task)trading.GetOpenOrdersAsync(symbol, ct: ct);

// ✅ 正確：靜態型別，compile-time 檢查 + 執行期不會被 internal 牆擋
var result = await _client.PerpetualFuturesApi.Trading
    .GetOpenOrdersAsync(symbol: symbol.BingXFormat, ct: ct)
    .ConfigureAwait(false);
```

### 預防
- 整個 codebase 對第三方 SDK 不使用 `dynamic`。已知例外：`BingXContract` 的欄位名不確定問題用 `dynamic` 讀欄位可接受（是「看不到 internal 方法」的問題，不是「看不到 internal 欄位」），但**方法呼叫永遠靜態**。
- Code review 看到新的 `dynamic` 使用一律要求說明為何不能靜態。

---

## L5 · `IExchangeClient` 擴充的 5 個實作者對齊慣例（來源：S61）

### 症狀
擴充 `IExchangeClient` 介面新增方法後編譯失敗，報錯「沒有實作 IExchangeClient 的 X 成員」。

### 根因
`IExchangeClient` 不只 `BingXExchangeClient` 在實作。實際上有 **5 個必須同時補齊的地方**：

| # | 檔案 | 用途 | 典型實作 |
|---|---|---|---|
| 1 | `src/CryptoBot.Infrastructure/Exchange/BingX/BingXExchangeClient.cs` | 生產實作 | 呼叫 BingX SDK |
| 2 | `src/CryptoBot.Infrastructure/Backtesting/BacktestSimulator.cs` | 回測模擬器 | 回空 / 依回測語意模擬 |
| 3 | `tests/CryptoBot.Application.Tests/Synchronization/AccountSynchronizerTests.cs` → `SyncFakeExchangeClient` | 同步測試 fake | 回空 |
| 4 | `tests/CryptoBot.Application.Tests/Integration/S7TestDriveIntegrationTests.cs` → `PipelineFakeExchangeClient` | 端對端測試 fake | 回空 |
| 5 | `tests/CryptoBot.Application.Tests/Strategies/StrategyEngineTests.cs` → `FakeExchangeClient` | 策略引擎測試 fake | 回空 |

少任一個測試專案都不能編譯。

### 修法 SOP
1. 擴充 `IExchangeClient.cs` — 介面方法宣告 + 相關 DTO（建議與既有 `ExchangePositionInfo` 放同檔）。
2. 實作 `BingXExchangeClient` — 真正呼叫 SDK，路徑對齊既有方法（如 `CancelOrderAsync` / `GetOrderAsync`）。**靜態型別呼叫，見 L4。**
3. `BacktestSimulator` 補 stub — 回空集合 / 固定值，註解說明「回測情境下不支援」。
4. 3 個測試 Fake 各補一個方法 — 回空即可，後續單元測試若需要行為再各自 override。
5. Build `dotnet build CryptoBot.sln -c Debug` 驗證 0 警 0 錯。

### 預防
- `IExchangeClient` 的測試 Fake 未來可考慮抽成共用 base class（例如 `FakeExchangeClientBase` 全部回空）避免三份複製貼上 — 但暫以顯式清單保持可見性。
- 介面擴充前先 `grep -r ": IExchangeClient" src tests` 列出全部實作者，確認一次補齊。

---

## 附錄 · 通用「沉默 Bug」自檢清單

當發現「代碼看起來對但行為不對」時，依序檢查：

1. **時序欄位**：所有 `CloseTime` / `EndTime` / 類似派生時間是否用統一的 `interval.ToTimeSpan()` 或等價函式推算，還是寫死了常數？
2. **原始碼編碼**：含中文的 `.cs` 檔是否有 UTF-8 BOM？（用 `head -c 3 file.cs | od -An -tx1` 一次看清）
3. **SDK 精度欄位**：讀 BingX / 其他 SDK 的 `*Precision` 欄位是不是把「小數位數」當「步進值」？
4. **dynamic 綁定**：有新 `RuntimeBinderException`？八成是呼叫 internal 實作。
5. **介面擴充**：新增介面方法後編譯報錯，先 grep 所有 implementer 是否齊全。
6. **防未來函數**：`TrimInProgressTail` 或相似切尾邏輯沒把尾根切掉時，先懷疑 CloseTime 是不是錯的。
7. **靜默失敗**：策略 / 執行層的 `return` 前有沒有只 log 就吞掉訊號的地方？應改為廣播 `[SIZE]` / `[RISK]` 前綴讓 Dashboard 顯性化。
8. **手動注入測試資料 vs EF 行為不對齊**：用 `sqlite3` 注入 row 後 EF 操作該 row 失敗（rows=0 / `DbUpdateConcurrencyException`）？極可能是 Guid / 日期等型別的字串格式與 EF 預設不同。先 `SELECT Id, length(Id), typeof(Id) FROM Orders LIMIT 5` 看 EF 真實儲存格式，與注入值對比 case + 格式。詳見 §S66-B-Hotfix。

---

## S66-A · BingX ClientOrderId 冪等回應契約（來源：T0 探針 × 2 輪）

### 探針執行紀錄

| 輪次 | 日期 | SDK 版本 | 用途 |
|---|---|---|---|
| 1 | 2026-04-25 10:49 UTC+8 | JK.BingX.Net 3.10.0 | 取得真實訊息（Path-B 嗅探未升級時）|
| 2 | 2026-04-25 11:25 UTC+8 | JK.BingX.Net 3.10.0 | 升級嗅探含 `unique` 後重跑，取得真實 errorCode |

兩輪皆於 VST Demo 環境執行 BTC-USDT，限價買 0.0001 BTC @ 市價 50% floor by tick。

### 真實 BingX 行為（兩輪交叉確認）

| 觀測項 | 確診值 |
|---|---|
| **Duplicate ClientOrderId 的 errorCode** | `101400` |
| **Duplicate ClientOrderId 的 Message** | `"clientOrderID unique check failed"`（注意 `clientOrderID` 大寫 D） |
| **未知 ClientOrderId 的 GetOrderAsync 行為** | 回 `null`（不拋例外）|
| **BingX 是否對 ClientOrderId 去重** | **是** —— 雙層防線（交易所 + 本地 Unique）都成立 |

### 偵測契約（鎖死於 `BingxDuplicateErrorSnifferTests`）

`BingXExchangeClient.IsDuplicateClientOrderIdError(int? errorCode, string? message)`：

| 防線 | 規則 | 用途 |
|---|---|---|
| 1️⃣ errorCode 主防線 | `errorCode == 101400` | 精確、language-independent；T0 實證值 |
| 2️⃣ message 備援防線 | 含 `client` + (`unique` \| `duplicate` \| `exists` \| `already`) 任一者 | 防 BingX 改 errorCode 但訊息穩定的情境；或 SDK 未暴露 errorCode 的少數路徑 |

兩條任一命中即視為冪等衝突。常數：
```csharp
internal const int BingxDuplicateClientOrderIdErrorCode = 101400;
```

### 修法 / 驗收
- 常數值由 `BingxDuplicateErrorSnifferTests.T0_constant_matches_2026_04_25_probe_evidence` 鎖死
- 偵測組合由 21 條 `[InlineData]` 涵蓋：T0 確診 / code 主防 / message 備援 / 不誤判
- 任何修改 `IsDuplicateClientOrderIdError` 不得讓 `[InlineData(101400, "clientOrderID unique check failed")]` 失敗

### 預防：SDK 升版健檢 SOP

升版 `JK.BingX.Net` 後第一件事：
```bash
cd CryptoBot/src/CryptoBot.ConsoleApp
dotnet ../CryptoBot.DiagnosticTool/bin/Debug/net8.0/CryptoBot.DiagnosticTool.dll probe-bingx
```

對照本段表格三個觀測項。任一項漂移必須：
1. 更新本段（新增一輪探針紀錄、保留歷史）
2. 更新 `BingxDuplicateClientOrderIdErrorCode` 常數
3. 加一條 `[InlineData(newCode, newMessage)]` 鎖死新值
4. 視情況擴充 message 嗅探詞清單

`probe-bingx` 不可刪 —— 它是 SDK 升版的 regression canary。

---

## S66-B-Hotfix · SQLite Guid 大小寫陷阱（手動注入 vs EF 預設格式）

### 症狀
- 對帳服務（或任何 EF UPDATE 流程）對某筆訂單執行 `order.Reject()` 等 mutation
- log 顯示 `changed=N` 與 `[RECONCILIATION] DB persistence mismatch! changed=N but SaveChanges affected 0 rows`
- 同時 EF 內部拋 `DbUpdateConcurrencyException` 但 `sqlite3` CLI 用 `WHERE Id = '...'` 明顯找得到 row

### 根因
EF Core + Microsoft.Data.Sqlite 預設將 `Guid` 序列化為 **UPPERCASE TEXT**，格式為 `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`。
SQLite 的 TEXT 比對**大小寫敏感**（`'ABC' = 'abc'` → `0`）。

PM 在驗收時用 `lower(hex(randomblob(N)))` 注入測試 row：
```sql
INSERT INTO Orders (Id, ...) VALUES (
    lower(hex(randomblob(4))) || '-1111-2222-3333-' || lower(hex(randomblob(6))),
    ...
);
```
產出 **小寫 Guid**（如 `deadbeef-1111-2222-3333-444455556666`）。
EF 後續 UPDATE 路徑：
1. SELECT 讀 row（成功，EF 解析 Guid 與大小寫無關）
2. Mutate 屬性 → ChangeTracker 標 Modified
3. 產出 `UPDATE Orders SET ... WHERE Id = @p3`，binding `@p3` 為 EF 預設**大寫 TEXT**
4. SQLite 比對 stored=`'deadbeef-...'` vs param=`'DEADBEEF-...'` → **不匹配**，0 rows
5. EF 預期 1 row → 拋 `DbUpdateConcurrencyException`

**這次跨三輪 hotfix 都被誤診為 ChangeTracker 失靈或 OrderRepository 短路**。實際 ChangeTracker、Repository、Value Converter 全部都對；錯的是注入 SQL 的 Guid 大小寫。

### 診斷三步
1. 用 EF 自己塞的 row 看真實格式：
   ```bash
   sqlite3 cryptobot.db "SELECT Id, length(Id), typeof(Id) FROM Orders LIMIT 5;"
   ```
   觀察 EF 寫的是大寫還是小寫；`length` 應為 36（含連字號）；`typeof` 應為 `text`。
2. 與注入 row 的 Id 對比：
   ```bash
   sqlite3 cryptobot.db "SELECT Id FROM Orders WHERE ClientOrderId = '<your fake cid>';"
   ```
3. 驗證 SQLite 大小寫敏感：
   ```bash
   sqlite3 ":memory:" "SELECT 'ABC' = 'abc';"  # 回 0 確認
   ```

### 修法
**只改注入 SQL，不改 EF / OrderRepository**。

❌ 錯誤示範：
```sql
lower(hex(randomblob(4))) || '-1111-2222-3333-' || lower(hex(randomblob(6)))
```

✅ 正確示範：
```sql
upper(hex(randomblob(4))) || '-1111-2222-3333-' || upper(hex(randomblob(6)))
```
或寫死大寫常數：`'AABBCCDD-1111-2222-3333-EEFF00112233'`。

如果歷史 row 已經是小寫，可一行修正：
```sql
UPDATE Orders SET Id = upper(Id) WHERE Id != upper(Id);
```

### 預防
- 任何手動 `INSERT INTO Orders` / `Positions` / `Strategies` 涉及 Guid 欄位的 SQL，全部用 `upper(...)` 或大寫字面量
- PM / 工程師交付測試指令前自我檢查清單：注入 SQL 的 Guid 是否大寫？
- `OrderReconciliationService` 的 `[RECONCILIATION] DB persistence mismatch!` 警示是這條坑的偵測器，**不可移除**
- 此規則同時適用於其他 Guid 欄位：`Orders.StrategyId`、`Positions.Id`、`Strategies.Id` 等

### 附帶教訓 — 三輪誤診的協作風險
PM 連續兩輪基於「ChangeTracker 失靈」假設發膠囊，工程師接受並動 OrderRepository。第三輪實證根因後**全部回退**。教訓：
- PM 給「建議方向」時，工程師不可直接照做 —— 要求實證根因（如 SQL 比對、log樣本）
- 不寫死的「警示偵測器」（如 mismatch warning）價值極高 —— 即使根因被誤判，偵測器仍會在後續 reproduce 時揭露真相
- 涉及序列化 / 字串比對的 bug 永遠先看 raw 儲存值，不要相信「型別系統會自動匹配」

---

## S66-C · 全鏈路 Trace ID 與層級決策

### 症狀（觸發場景）
PM 在 S66-C TraceId 膠囊指定使用 `using (LogContext.PushProperty("TraceId", traceId))` 包整個 K 線 tick 處理路徑。`LogContext` 是 Serilog 的型別（命名空間 `Serilog.Context`）。

### 技術實證（實作真相）
- **生成點**：`StrategyExecutor.HandleKlineUpdateAsync` 起頭，生成 `Guid.NewGuid().ToString("N")[..12]`。
- **傳遞鏈**：
  1. **`_logger.BeginScope(IDictionary<string, object>)`** ← 不是 LogContext.PushProperty！
     原因：IRON ⑥ 抽象不洩漏；UseSerilog 自動把 BeginScope 橋接到 Serilog LogContext。
  2. `Order.TraceId` → 存入 SQLite，與訂單永久綁定。
  3. `SignalR` 推播負載 → `StrategyEvaluatedUpdate.TraceId`，供 UI 診斷使用。

### 根因（為什麼不能用 LogContext.PushProperty）
照膠囊原文寫會讓 `CryptoBot.Application` 加 `using Serilog.Context;` —— **違反 IRON ⑥**。
Serilog 是 Infrastructure 層的實作；Application 層只該知道 `ILogger<T>` 框架抽象。一旦直接引用，未來更換日誌庫時整層 Application 都要改。

### 修法
改用 `_logger.BeginScope(IDictionary<string, object>)`。關鍵機制是 `builder.Host.UseSerilog()` 會自動把 BeginScope properties 橋接到 `LogContext`。

### 驗收
- `StrategyExecutor_TraceId_PropagatesFromKlineToOrderAndBroadcast` 測試通過。
- `[TraceId: a1b2c3d4e5f6]` 標籤在 console log 正確渲染。

### 預防：未來工程師接到類似膠囊時的 SOP
1. 任何 PM 膠囊指定實作相依於具體日誌庫型別時，自動偏離為框架抽象（`ILogger.BeginScope`）。
2. 在交付摘要報備該偏離與理由（IRON ⑥）。

---

## S66-D · NTP 時鐘漂移與簽章失效 (來源：T1 探針)

### 症狀
- 交易所 REST API 頻繁回報「簽章失效 / 時間戳超出窗口」類錯誤（具體 errorCode 值待未來實機觸發 probe 確診後補登）。
- 本地計算的 K 線 CloseTime 與交易所成交時間出現顯著（> 1s）的視覺落差。

### 核心演算法 (Round-trip Mid-point)
為了抵消網路延遲，偏差計算採「包夾法」：
1. `T1` = 本地發送請求時間。
2. `T_server` = 交易所回傳的伺服器時間。
3. `T2` = 本地接收回應時間。
4. `Offset = T_server - (T1 + T2) / 2`。

### 實證防線
- **Warning 閾值**：±500ms（日誌警示）。
- **Reject 閾值**：±1000ms（RiskManager 強制攔截，琥珀金標記）。
- **實測數據 (2026-04-25)**：量測值 `-947ms`，處於臨界危險邊緣（距 reject 線僅 53ms）。疑似 OS 時鐘服務未及時同步，待使用者執行 `w32tm /resync` + 重跑 `s66d_check-skew` 驗證根因。

### 預防
- 若 `s66d_check-skew` 顯示為 `UNSAFE`，必須執行系統校時。
- 嚴禁修改 `RiskManager` 移除此項檢查。

---

## S66-E · 啟動期 Pre-flight Check 與 Skew 測量服務統一

### 症狀（觸發場景）
S66-D 的 `NtpDriftMonitor` 在啟動 5 分鐘窗口內尚未做首次 sync，使用者沒有顯眼的視覺指標即可知時鐘狀態。實測 2026-04-25 撞到 -931ms 偏差（距 RiskManager 攔截線僅 69ms），啟動 log 中沒有醒目警示，使用者只能跑 `s66d_check-skew` 才知道。

### 根因（為什麼需要這條）
- 啟動期偏差可見性不足 → 使用者可能直接跑實盤
- `NtpDriftMonitor` 與 `CheckSkewCommand` 各自實作一份「包夾測量」演算法 → 演算法漂移風險

### 修法
1. **抽取 `ISkewMeasurementService`** 至 Application 層 —— 單一資料來源，演算法集中於 `SkewMeasurementService.MeasureAsync()`
2. **`IStartupHealthCheck` / `StartupSkewCheck`** —— 純資料層，回傳 `StartupCheckResult`（含 `SkewStatus` enum、Offset、Action advice）。**不**呼叫 `Console`、不決定 exit code（IRON ⑥）
3. **`StartupBannerRenderer`**（ConsoleApp 層）—— 渲染 ASCII banner，handle CJK / emoji 寬度
4. **`appsettings:Startup.AbortIfSkewExceedsMs`** —— `int?` nullable；設定且偏差超過即 `Environment.Exit(1)`，預設 `null` 不阻擋
5. **重構**：`NtpDriftMonitor` + `CheckSkewCommand` 改用 `ISkewMeasurementService`

### 驗收契約（鎖死於測試）
- `SkewMeasurementServiceTests`：中點數學 / 正向偏差 / 負向偏差 / 例外傳遞 = 4 條
- `StartupSkewCheckTests`：閾值邊界 11 + 訊息驗證 6 = 17 條
- Boundary 行為：`±500ms` 仍 Safe（嚴格 > 才升級）/ `±1000ms` 仍 Warning / `>1000ms` Unsafe

### 預防（未來工程師的 SOP）
- 任何「需在 ConsoleApp 啟動瞬間做的健檢」遵循相同分層：
  - **Application 層**：純資料 service，回 record
  - **ConsoleApp 層**：渲染 + exit 決策
- 不要把「健檢結果」與「abort 邏輯」混在 Application 層 —— 那會讓 Application 直接相依 `Environment.Exit` / `Console`，違反 IRON ⑥
- 若未來新增其他啟動健檢項（例：DB 連線、API key 有效性），擴充 `IStartupHealthCheck` 介面為多項組合，`StartupCheckResult` 升級為 record list

---

## L6 · IRON §② 金鑰洩漏與 Git 歷史淨化（來源：S67/S68）

### 症狀
- 真實 API Key 或 Webhook 地址被 commit 進 Git 並 push 到公開 Repo（如 GitHub）。
- `git log -p` 可搜尋到敏感字串。

### 根因
開發期間為了方便驗證，直接將金鑰填入 `appsettings.json` 的 placeholder 位置，且未意識到該檔案已被 Git 追蹤。即便後續刪除該行再 commit，歷史紀錄中仍留有明文。

### 診斷
```bash
git log --all -p | grep "敏感片段"
```
若有輸出，代表安全性已崩潰。

### 修法 (P0/P1/P2)
1. **P0 (即時止損)**：立即於交易所/平台「撤銷」該金鑰，不要寄望於刪除歷史（刪除前可能已被爬蟲抓走）。
2. **P1 (歷史淨化)**：使用 `git-filter-repo` (推薦) 或 `BFG Repo-Cleaner` 徹底抹除敏感檔案或字串。
   ```bash
   git filter-repo --path src/CryptoBot.ConsoleApp/appsettings.json --invert-paths --force
   ```
   *(註：這會重寫所有受影響的 Commit Hash)*
3. **P2 (強制同步)**：所有協作者需重新 clone 或執行 `git reset --hard origin/main`，並強制推送 (`force-push`) 回遠端。

### 預防
- **絕對禁止** 在任何被 Git 追蹤的檔案中寫入真實金鑰。
- 專案應預置 `.gitignore` 排除 `appsettings.Local.json`。
- **金鑰注入規範**：本地開發一律透過 `appsettings.Local.json` 或環境變數注入。

---

## L7 · 優化器搜尋策略解耦與互動式需求（來源：S67）

### 症狀
- 優化器 (Optimizer) 只能跑全網格搜尋 (Grid Search)，當參數維度增加（如 4 個以上）時，計算量呈指數級爆炸，回測永無止盡。
- 難以引入貝氏優化 (Bayesian) 等需要「邊跑邊學」的演算法，因為原本的 `RunAsync` 是一次性展開所有組合。

### 根因
搜尋邏輯（如何產生參數組）與執行邏輯（如何跑回測）高度耦合在 `StrategyOptimizer` 內部。

### 診斷
觀察 `StrategyOptimizer` 是否包含多層巢狀 `foreach` 循環。若是，則缺乏擴充性。

### 修法
1. **抽象化**：定義 `ISearchStrategy` 介面，僅負責 `Enumerate(ranges)`。
2. **策略模式**：
   - `GridSearchStrategy`：實作傳統笛卡兒積。
   - `RandomSearchStrategy`：實作基於 Budget 的隨機抽樣。
3. **互動式支援**：針對貝氏優化，介面應考慮支援 `Suggest()` 與 `Tell()` 模式，而非單純的 `IEnumerable`。

### 預防
- 核心引擎不應假設搜尋空間的大小或順序。
- UI 應同步提供搜尋方法的切換，並動態顯示對應參數（如 Random 的 Budget）。

---

## L8 · PM 驗收測試計畫忽略 DiagnosticTool（來源：S69-HOTFIX_CLOSE_SIGNAL_RISK，2026-04-26）

### 症狀
- 工程師（ClaudeCode）交付的 `🧪 PM 驗收測試計畫` 中：
  - 前置檢查只用 OS `tasklist`，沒驗 API Mode（IRON §② 金鑰唯一路徑檢查缺席）。
  - 情境 3「實盤平倉行為驗證」寫成「啟動策略 → 觀察 ConsoleApp log」，未列任何 DiagnosticTool 指令。
  - 期望輸出錨點是「log 字串 grep」而非可重現的 probe 結構化輸出。
- 使用者抓到後直接質疑「為啥沒用 CryptoBot.DiagnosticTool」。

### 根因
寫驗收計畫時偷懶往「肉眼觀察 log」靠攏，未先盤點 DiagnosticTool 已存在的命令並 map 到 VCP。本專案 DiagnosticTool 已有 10 個命令（`env` / `strategies` / `s66a_check-order` / `s66d_check-skew` / `s61_sync-orders` 等），覆蓋幾乎所有可重現驗收場景，工程師卻未引用。違反三條：
1. **DISCIPLINE §1.4 實證先行**：log 不是結構化實證。
2. **DISCIPLINE §7「用具體 DiagnosticTool 指令驗證，禁止只寫文字描述」**（前置檢查條款）。
3. **DISCIPLINE §5.1 禁未經實證的描述性括號**：「觀察 log 出現 X」無法當作可重現抽驗。

### 診斷
工程師交付前自問：
1. 本膠囊涉及哪些領域？（風控 / 下單 / 對帳 / 時鐘 / 配置 / DB / WS）
2. 每個領域對應到哪個 DiagnosticTool 命令？答不出來代表沒準備好交付。
3. 每個 VCP 的「期望輸出錨點」是 DiagnosticTool stdout 的具體字串嗎？若是「log 出現 X」直接退回重寫。

### 修法
補強 S69-HOTFIX_CLOSE_SIGNAL_RISK 情境 3 為四步 probe 鏈：
- `env` — Demo 雙保險（IRON §②）
- `s66d_check-skew` — NTP 偏差預檢（避免觀察項命中污染判讀）
- `strategies` — 確認測試策略 status
- 觸發開倉 + 平倉，**抄下 ClientOrderId**
- `s66a_check-order <Cid>` — 端到端證明平倉單下出且交易所成交
- `s61_sync-orders` — 確認無幽靈單殘留

每一步都有 stdout 結構化錨點與失敗解讀表，符合 §7 結構。

### 預防
- **工程師交付前自查清單新增一條**：本膠囊 VCP 是否含 DiagnosticTool 指令？若涉及「BingX / DB / 風控 / 對帳 / 時鐘 / 配置 / 訂單」任一面向但 VCP 全是 `dotnet build|test` + `tasklist` → 不合格，重寫。
- **領域對照表**（工程師日後翻這張表生 VCP）：

| 涉及領域 | 對應 DiagnosticTool 命令 |
|---|---|
| API Mode / 金鑰 / 餘額 | `env` |
| 策略 status / 配置 | `strategies` |
| 訂單下出 / 對帳 | `s66a_check-order <Cid>` |
| NTP 漂移 | `s66d_check-skew` |
| 幽靈單清查 | `s61_sync-orders <Symbol>` |
| K 線資料一致性 | `s60_check-kline <Symbol> <Interval>` |
| 多週期對齊 | `s63_check-mtf <Symbol>` |
| WebSocket 連線 | `s31_check-ws` |
| 下單量精度 | `size <entryPrice> <strategyName>` |
| BingX errorCode 探針 | `probe-bingx [Symbol]`（DEMO ONLY） |

- **DISCIPLINE §1.6 v1.11 自查 Checklist 第 4 條已寫過此原則**（「每個 VCP 含具體 probe 指令 + 期望輸出錨點 + 失敗解讀表」），但僅在「強化抽驗模式」啟動時 enforced。本案教訓：**§7 結構要求對所有膠囊適用，不應等到強化抽驗模式才補**。下版 DISCIPLINE 修訂時，工程師應推動把這條從「強化抽驗模式條件項」升級為「§7 全域強制項」。

---

## §S70 跨時區資料判讀與 Dashboard 顯示語意分離原則（2026-04-27）

### 症狀

使用者觀察到 Dashboard「TODAY P&L」卡片顯示與真實虧損方向不符或數字偏差顯著。具體場景：使用者台灣時間 04-27 06:01 觀察，依交易所明細手算今日真實淨損益 ≈ −1,998 USDT，但 Dashboard 卡片可能顯示為正值或數字偏差大。

PM 在最初診斷時亦因「DB 時間欄是 UTC、PM 在 UTC+8 環境下閱讀」誤判為「DB 紀錄停在 04-23、資料斷鏈」，連續產出兩份基於誤判的膠囊（已 VOIDED）。

### 根因（兩條獨立 bug）

#### 根因 #1 — 時區錯位

`CryptoBot.ConsoleApp/Services/DashboardStatsService.cs:42`：

```csharp
var dayStart = DateTime.UtcNow.Date;
```

`DateTime.UtcNow.Date` 在 UTC+8 環境下定義的「今日 00:00」實際對應台灣時間 08:00。使用者眼中的「今日」（台灣 00:00 起）與此窗口錯位 8 小時，當天起始 8 小時的窗口會包含**昨日後段（台灣 08:00 ~ 24:00）的交易**。

#### 根因 #2 — 顯示語意混算

`DashboardStatsService.cs:53`：

```csharp
TodayPnL: realizedToday + unrealized,
```

欄位命名為「TodayPnL」但實際內容為「今日已實現 + 當前所有開倉浮動」。`Position.UnrealizedPnL`（`Position.cs:82-92`）不分今日昨日，全部 OpenPositions 浮動加總進來。命名與內容語意嚴重不符。

兩條 bug 疊加 → 卡片數字無法被使用者用任何單一心智模型解讀。

### 診斷

#### 1. SQL 對帳（依使用者本地時區）

```sql
SELECT ROUND(SUM(RealizedPnL),2) AS NetPnL, COUNT(*) AS N
FROM Positions
WHERE ClosedAt >= datetime('now','start of day','-8 hours')
  AND ClosedAt IS NOT NULL;
```

`-8 hours` 是 SQLite 對 UTC 時間的補償，用以對齊台灣 00:00 起算的窗口。將結果與交易所明細手算對比，差距 < 5 USDT 即計算路徑無誤。

#### 2. 比對交易所明細手算

每筆交易兩個損益數字：
- 數字 1（負較大）= **淨 PnL（已扣手續費）** ← 對應系統 `Position.RealizedPnL`
- 數字 2（負較小）= **毛 PnL（grossPnL，未扣手續費）**

判讀「真實落袋金額」應看數字 1。

### 修法（採方案 C：A + B 同時做）

#### A. 時區可配置

```csharp
// appsettings.json：
// "Display": { "LocalTimeZone": "Asia/Taipei" }

var tzId = _config["Display:LocalTimeZone"] ?? "Asia/Taipei";
var localTz = TimeZoneInfo.FindSystemTimeZoneById(tzId);
var nowLocal = TimeZoneInfo.ConvertTimeFromUtc(DateTime.UtcNow, localTz);
var dayStartLocal = nowLocal.Date;
var dayStartUtc = TimeZoneInfo.ConvertTimeToUtc(dayStartLocal, localTz);
```

#### B. DTO 拆分

```csharp
public sealed record DashboardStatsUpdate(
    DateTime Timestamp,
    decimal TotalEquity,
    decimal TodayRealizedPnL,    // 今日已實現（依本地時區）
    decimal OpenUnrealizedPnL,   // 當前所有開倉浮動（不限今日）
    int ActiveStrategyCount);
```

UI 卡片分區顯示，禁止合併。

### 預防（鐵則化）

1. **DB 一律存 UTC**（已是慣例）；**UI / Dashboard / 任何「日界」型 query 一律先換算到使用者本地時區再計算**
2. **任何「今日」「昨日」「本週」型語意 query 必須在實作旁註明所用時區**（避免下次同類偏差）
3. **PnL 顯示一律拆「已實現」與「浮動」兩欄位**，不混算（合併會掩蓋真實狀態，違反 IRON ⑤ 風控透明化）
4. **PM / 工程師判讀時間軸資料前**：先確認資料源時區（UTC？本地？），用 `datetime(col,'+8 hours')` 等 SQL 函數明示換算，不用心算
5. **時區配置可配置化**：避免硬編碼 `Asia/Taipei`，未來海外使用者擴展不再撞同類雷

### 何時要回頭讀本章節

- 任何涉及 Dashboard 卡片 / 報表 / Email 通知時間欄位的需求
- 任何「以日 / 週 / 月為單位的 PnL / 成交量 / 損益」查詢
- 跨時區使用者擴展時（例如海外部署）
- PM 判讀使用者「最近 N 筆 / 今天 / 昨天」資料前

---

## §S72 AccountSynchronizer Phantom Close 真因與實證對帳紀律（2026-05-05）

### 症狀

Position `99A3E51D-257E-4F42-B856-40B572F5C506`（LINK-USDT Short 9573.2 lot）DB 標記 `IsClosed=1` + `RealizedPnL=+1902.647794` + `ExitPrice=9.301` + `ClosedAt=2026-05-04 07:36:53 UTC`，但 Orders 表 04-27 後**完全無對應 LINK-USDT 平倉 Order 紀錄**。Dashboard `TodayRealizedPnL` 顯示 +1902 與使用者「04-27 後未交易」陳述衝突。

### 根因

`AccountSynchronizer.ReconcileAsync` line 144-170 對「本地 Open / 遠端 GetOpenPositions 不存在」的 orphan position 採用：

```csharp
var mark = await _exchange.GetMarkPriceAsync(local.Symbol, ct);
local.Close(mark, reason: "Reconcile: position not found on exchange");
```

**用當下 MarkPrice 推算 ExitPrice → 算出虛假 RealizedPnL → 入帳廣播**。當 BingX `GetOpenPositions` 因任何原因回傳缺項（WS / REST 一致性偏差、查詢時點遠端短暫不見、第三方手動清倉、SDK fallback），系統把「我看不到」**等同**於「已平倉」，並用「當下市價」充當成交價。

無對應 Order 紀錄、無真實成交實證、無 [RECONCILIATION] 廣播 — 是「**盲猜獲利**」的標準教科書範例。違反 IRON ⑤ 風控透明化（靜默結算）+ evidence-first §4 反捏造原則。

`HandleAccountUpdateAsync` line 271-303 對 `remote.Quantity == 0` 的處理同樣使用 MarkPrice fallback（line 281-284），同源缺陷。

### 診斷

#### 1. 資料層揭示

```sql
-- LINK-USDT Position 標 IsClosed=1
SELECT Id, IsClosed, RealizedPnL, ExitPrice, OpenedAt, ClosedAt FROM Positions
WHERE Id = upper('99A3E51D-257E-4F42-B856-40B572F5C506');

-- 但 05-04 LINK-USDT Order 完全空白
SELECT count(*), min(CreatedAt), max(CreatedAt) FROM Orders
WHERE Symbol='LINK-USDT' AND CreatedAt LIKE '2026-05%';
-- 0 || ←「真實平倉路徑必有 Order 紀錄」的 invariant 被打破
```

#### 2. 工具層揭示

`s61_sync-orders LINK-USDT` 同時揪出 3 筆殭屍 PartiallyFilled Order（同 StrategyId），印證「user-data WS 漏接最終 fill update + ReconcileAsync 只啟動時跑」雙重缺陷。

### 修法

#### A. 資料修復（一次性）

```sql
BEGIN TRANSACTION;
UPDATE Positions
SET RealizedPnL = '0',
    ClosedAt = '2026-04-27 01:03:02'
WHERE Id = upper('99A3E51D-257E-4F42-B856-40B572F5C506')
  AND IsClosed = 1
  AND RealizedPnL = '1902.647794';
-- rows_affected = 1 才 COMMIT
COMMIT;
```

採「歸零止損」原則：因無真實平倉 Order 可佐證實際 PnL，依「寧可報錯也不要假宣告獲利」紀律歸零。`ClosedAt` 改為對應該 Strategy 04-27 末筆 LINK-USDT Order（`D05DCE5F`）的 UTC 時間，符合 IM §S70 預防原則「DB 一律存 UTC」。

ExitPrice 留 9.301 未動（守膠囊範疇），數學上與 PnL=0 不一致，待後續決策。

#### B. AccountSynchronizer 重構 — 實證對帳

**移除盲猜路徑**（兩條）：

1. `ReconcileAsync` orphan close 不再用 `GetMarkPriceAsync`
2. `HandleAccountUpdateAsync` 對 `remote.Quantity == 0` 不再用 `remote.MarkPrice` fallback

**改為實證流程**：

```
1. 部位消失 → 呼叫 IExchangeClient.GetTradeHistoryAsync(symbol, since=OpenedAt) 取近期成交
2. 找到對應成交 → 以真實成交價（加權平均）結算 RealizedPnL
3. 無對應成交（Unaccounted）→ 採隱式約定：IsClosed=1, RealizedPnL='0',
   並 LogError + IRealtimeBroadcaster 廣播 [CRITICAL_SYNC] 雙軌通知；不清 ExitPrice
4. 不執行 schema 變更（不引入 PositionStatus enum）— 維持最小衝擊
```

**殭屍 PartiallyFilled 補殺**：

`ReconcileAsync` 升級為週期性背景服務（`PeriodicReconciliationHostedService`，預設每 60s 一次），對 ActiveOrders 強制呼叫 `RefreshOrderStatusAsync`。

### 預防（鐵則化）

1. **「狀態變更 → 入帳」路徑必須以交易所 REST 實證為據**，禁用 MarkPrice / CurrentPrice 推算。違反此鐵則 = 假宣告獲利
2. **Position 結算路徑必須對應 Order 紀錄**：DB invariant — `Position.IsClosed=1` 必有同 Strategy / Symbol / 對應時間的 Order 平倉紀錄；缺項即為 phantom
3. **對帳異常必廣播**：自動補正、實證查無、降級走隱式約定 — 三類事件全部 `[CRITICAL_SYNC]` 廣播 + LogError 雙軌；違反即違 IRON ⑤
4. **ReconcileAsync 不可只跑啟動時**：須週期性執行（背景 IHostedService），確保長 session 仍能補殺 WS 漏接
5. **「我看不到」≠「已平倉」**：交易所 REST 短暫缺項不等於成交事件；查無實證時保留本地 Open + 報錯，不結算

### 何時要回頭讀本章節

- 任何「狀態變更 / 自動結算」型代碼路徑修法（Position / Order / Balance）
- AccountSynchronizer / OrderReconciliationService / 對帳服務新增邏輯前
- 任何用 `GetMarkPriceAsync` / `GetCurrentPrice` / 行情價填充「真實成交資料」的場景 — 立刻視為紅旗
- WS 訂閱漏接 / 殭屍訂單 / 跨 session 復原時的對帳設計

---

_「所有沒寫下來的教訓，都會變成下次的 Bug。」_

---

## L9 · BingX VST 假性成交回報陷阱 (S71/S72)

**症狀**：
- 系統對早已過期的 `PartiallyFilled` 單發出狀態更新請求 (`check-order`)。
- BingX VST API (`GetOrderByClientOrderIdAsync`) 錯誤回報該單已 `Filled`，且附帶完整的假數量與價格。
- 導致本地同步器信以為真，引發幽靈獲利 (Phantom Profit) 或數據錯亂。

**根因**：
- BingX 模擬盤 (VST) 的撮合引擎與歷史紀錄資料庫存在極端的不一致性。
- 當查詢處於邊界狀態的舊單時，API 可能基於快取或預設邏輯給出錯誤終態，而非真實的 `Canceled`。

**診斷**：
- 懷疑產生幽靈單時，**嚴禁單憑 API 回報結案**。
- 必須比對：(1) 真人登入 BingX VST UI 查詢「歷史成交」；(2) 查詢時段是否在邏輯空窗期。

**修法**：
- 放棄依賴 API 自動修正。
- 直接下 SQL 更新：`UPDATE Orders SET Status = 4, RejectReason = 'VST API 假性回報', FilledQuantity = '0', AverageFillPrice = NULL`。執行完全去毒 (Complete Detox) 以對齊 UI 事實。

**預防**：
- **UI is the Ultimate Truth in VST**：模擬盤下，API 與 UI 有出入時，一律以 UI 歷史為準。
- 任何查無實證的 API `Filled` 回報，不可進入 PnL 結算。
