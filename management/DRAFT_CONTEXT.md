# CryptoBot 暫存交接草稿 (DRAFT for Checkpoint Save)

> **日期**：2026-04-26
> **議題**：參數優化掃描 — 拓展式重構（搜尋演算法可插拔化）
> **狀態**：設計已對齊、Task 已建、**尚未寫 code**，待下個 session 由工程師接手實作

---

## 📌 討論脈絡 (Conversation Context)

使用者主動詢問：**現行優化掃描的執行原理為何？是否使用 GPU？**

工程師（Claude）已就現況做完整 audit 並回覆：

### 現況確認 (As-Is)
- **演算法**：暴力網格搜索（Cartesian Product Grid Search）— 唯一實作
- **核心檔案**：`CryptoBot.Application/Backtesting/StrategyOptimizer.cs`
- **執行模型**：CPU 多執行緒（`Parallel.ForEachAsync`，DOP = `Environment.ProcessorCount`）
- **GPU 使用**：**零** — grep `CUDA|GPU|TorchSharp|ML.NET|OpenCL|ILGPU|SIMD|Vector` 在 `src/` 全無命中
- **資料層**：SQLite + 智慧填充（backward/forward fill），同 (Symbol, Interval) 重跑命中快取
- **排名**：`OptimizationOrchestrator` 用 `ProfitToDrawdownRatio` 重排，爆倉墊底
- **瓶頸**：維度爆炸（k₁ × k₂ × … × kₙ）；只能加 CPU 核心線性提速，回測本質時序依賴無法 GPU 化

---

## 🎯 已對齊的方案 (Agreed Design)

**拓展式重構** — 不取代 Grid，而是把搜尋演算法抽成可插拔介面 `ISearchStrategy`，Grid 變成「眾多策略中的一種」並維持預設。

### 核心抽象
```csharp
namespace CryptoBot.Application.Backtesting.Search;

public interface ISearchStrategy
{
    string Name { get; }
    Task<IReadOnlyList<IReadOnlyDictionary<string, decimal>>> ProposeNextBatchAsync(
        IReadOnlyList<ParameterRange> ranges,
        IReadOnlyList<OptimizationRun> historyToDate,
        CancellationToken ct);
}
```

**設計關鍵**：採「批次 + 反饋」模型，無記憶演算法（Grid/Random）一輪結束、有記憶演算法（GA/Bayesian）多輪迭代。每輪 batch 內部仍走現有 `Parallel.ForEachAsync` + scope-per-run，**並行模型不變**。

### 使用者拍板的兩個決策
1. ✅ **Phase 1 範圍包含 UI** — 連帶動下拉選單 + 動態欄位
2. ✅ **預設搜尋方法仍為 Grid**（向後相容），UI 預選 Random 並標註「推薦」

---

## 📋 已建立的 Task List（Phase 1，明天接手執行）

| # | Subject | 摘要 |
|---|---|---|
| 1 | Create `ISearchStrategy` abstraction | 新增 `Application/Backtesting/Search/ISearchStrategy.cs` |
| 2 | Implement `GridSearchStrategy` | 把現有 `CartesianProduct` 搬進去，作為預設 |
| 3 | Implement `RandomSearchStrategy` | 加 `(budget, seed)` 建構子，從 `ParameterRange` 內均勻抽樣 |
| 4 | Refactor `StrategyOptimizer.RunAsync` to batch loop | 加 `ISearchStrategy` 參數（預設 Grid），外圈循環提案 → 內圈並行執行 → 累積歷史 |
| 5 | Wire `SearchMethod` into `OptimizationRequest` + Orchestrator | 加 enum + options，依方法組裝對應策略 |
| 6 | Update `LabEndpoints` API | 接受 method + budget 欄位 |
| 7 | Add search method picker to `BacktestLab` UI | 下拉 + 動態 budget 欄位，Random 標「推薦」 |
| 8 | Build solution and fix compile errors | `dotnet build` 跑乾淨 |

---

## 🗂️ 受影響檔案清單 (Surface Area)

| 檔案 | 動作 |
|---|---|
| `Backtesting/Search/ISearchStrategy.cs` | **新增** |
| `Backtesting/Search/GridSearchStrategy.cs` | **新增** |
| `Backtesting/Search/RandomSearchStrategy.cs` | **新增** |
| `Backtesting/StrategyOptimizer.cs` | **改** — `RunAsync` 加 `ISearchStrategy` 參數，預設 `new GridSearchStrategy()` |
| `Services/OptimizationOrchestrator.cs` | **改** — `OptimizationRequest` 加 `SearchMethod` + `SearchOptions` |
| `Api/LabEndpoints.cs` | **改** — endpoint DTO 接 method/budget |
| `Components/Pages/BacktestLab.razor` | **改** — 加方法選擇器 |
| `Services/BacktestRunner.cs`（CLI）| **不動** — 預設 Grid 走原路徑 |

---

## 📅 後續 Phase 規劃（不在本次範圍）

| Phase | 內容 | 預估 |
|---|---|---|
| **Phase 2** | `GeneticSearchStrategy`（族群天然偏好 robust 平原，最適合交易策略）| 2~3 天 |
| **Phase 3** | Bayesian (Optuna sidecar via Python stdio/JSON) | ~1 週 |
| **Phase 4** | **Walk-Forward Analysis**（與搜尋正交，比換演算法更重要 — 防過擬合）| ~1 週 |

---

## ⚠️ PM 彙整時的注意事項

1. **本次純設計對齊 + Task 建立，無任何 code 變動** — git status 應該乾淨
2. **向後相容是強約束** — Grid 必須保持為預設，CLI `--optimize` 路徑零行為差異
3. **Phase 1 完成後可立即享受 Random 解放維度爆炸的好處**，但**不會改變過擬合風險** — 真正的防過擬合在 Phase 4
4. 工程師建議的落地順序：Phase 1 → Phase 4（Walk-Forward）→ Phase 2 (GA) → Phase 3 (Bayesian)
   - 理由：Walk-Forward 比換演算法更能提升「實戰績效」
