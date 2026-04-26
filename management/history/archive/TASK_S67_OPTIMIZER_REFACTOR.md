# 任務膠囊：[S67] 優化器架構升級 — 可插拔搜尋演算法 🧩

## 1. 任務目標 (Goal)
將現有的暴力網格搜尋 (Grid Search) 重構為可擴展的策略模式，引入 `ISearchStrategy` 介面，並實作「隨機搜尋 (Random Search)」以解決參數維度爆炸問題。

## 2. 實作清單 (Implementation List)

### 階段一：[Abstraction & Logic] - 核心邏輯
- [ ] **[Execution]** 定義介面：建立 `Application/Backtesting/Search/ISearchStrategy.cs`。
- [ ] **[Execution]** 遷移 Grid：實作 `GridSearchStrategy.cs`（搬遷現有笛卡兒積邏輯）。
- [ ] **[Execution]** 實作 Random：實作 `RandomSearchStrategy.cs`（支援 budget 與均勻抽樣）。
- [ ] **[Execution]** 重構 Optimizer：修改 `StrategyOptimizer.RunAsync` 採「提案 → 批次執行 → 反饋」模型。

### 階段二：[Integration & UI] - 系統整合
- [ ] **[Execution]** 擴充 DTO：`OptimizationRequest` 加入 `SearchMethod` 與 `Budget` 欄位。
- [ ] **[Execution]** API 更新：`LabEndpoints` 接受新搜尋參數。
- [ ] **[UI]** 介面升級：在 `BacktestLab.razor` 加入搜尋方法下拉選單，Random 標註為「推薦」。

### 階段三：[Verification] - 品質保證
- [ ] **[Test]** 單元測試：驗證 `RandomSearchStrategy` 在給定 budget 下產出的參數組數量正確。
- [ ] **[Test]** 向後相容測試：驗證現有 CLI `--optimize` 在未指定方法時仍走 Grid Search 且結果不變。

## 3. 驗收檢核點 (VCP)
- **VCP-1 (Compile)**: 全專案 `dotnet build` 0 錯誤 0 警告。
- **VCP-2 (Backward Compatibility)**: 現有回測功能不受影響。
- **VCP-3 (UI Functional)**: UI 能正確切換 Grid/Random，且選擇 Random 時會出現 Budget 欄位。
- **VCP-4 (Logic)**: 執行 Random Search 時，日誌應顯示「Search Method: Random, Budget: X」。

## 4. 交付要求 (Deliverables)
- [ ] 完整 Phase 1 代碼提交。
- [ ] `HANDOFF_20.md`：紀錄優化器架構之重大突破。

---
## 5. 驗證反饋紀錄 (History)
- 2026-04-26: 由 PM 基於設計草稿正式立項。
- 2026-04-26: 工程師交付，PM 執行全路徑驗收（含 Build、Unit Tests、API 400 攔截與 UI 原始碼抽驗）✅ 全數通過。
