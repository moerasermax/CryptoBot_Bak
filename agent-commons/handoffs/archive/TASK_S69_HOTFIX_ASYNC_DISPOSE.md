# 任務膠囊：S69 貝氏優化引擎 IAsyncDisposable 釋放漏洞修復 (Hotfix)

## 📌 1. 背景與動機
使用者測試時發現 `OptimizationOrchestrator` 回報警告：
> ⚠ 'CryptoBot.Infrastructure.Backtesting.Search.BayesianSearchStrategy' type only implements IAsyncDisposable. Use DisposeAsync to dispose the container.

**根因分析**：
`BayesianSearchStrategy` 為了與 FastAPI Sidecar 溝通並在結束時清理 Study，實作了 `IAsyncDisposable`。然而在 `OptimizationOrchestrator` 中，使用 `_scopeFactory.CreateScope()` 建立同步 Scope，並透過 `using var scope = ...` 進行同步釋放。當 DI 容器嘗試釋放一個僅實作 `IAsyncDisposable` 的實例時，會拋出警告或錯誤。

## 🎯 2. 實作清單
- [ ] 修改 `CryptoBot/src/CryptoBot.ConsoleApp/Services/OptimizationOrchestrator.cs`。
- [ ] 找到解析 `IAdaptiveSearchStrategy` 的區塊（約 L140 附近）。
- [ ] 將 `using var scope = _scopeFactory.CreateScope();` 改為 `await using var scope = _scopeFactory.CreateAsyncScope();`。
- [ ] 確認整個專案沒有因為此改動產生新的編譯錯誤或警告。

## 🔬 3. 驗證檢核點 (VCP)

### VCP-1: 編譯品質 (IRON §3.1)
- **指令**: `dotnet build CryptoBot/CryptoBot.sln`
- **期望輸出**: 0 警告 / 0 錯誤。
- **失敗解讀**: 
  - 若仍有其他 Async 相關警告，需一併檢視 `StrategyOptimizer.RunAsync` 等呼叫層級。
  - 若報錯，檢查是否正確 using `Microsoft.Extensions.DependencyInjection` 擴充方法。

### VCP-2: 測試通過率
- **指令**: `dotnet test CryptoBot/CryptoBot.sln`
- **期望輸出**: 100% Pass。

## 📨 4. 交付要求 (致工程師)
請工程師（ClaudeCode）接手此膠囊，修改代碼後確保通過 `dotnet build` 與 `dotnet test`，並在回覆中附上 `🧪 PM 驗收測試計畫`，以便我執行確認無警告殘留。