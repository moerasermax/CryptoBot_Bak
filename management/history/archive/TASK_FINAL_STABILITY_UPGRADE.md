# 任務膠囊：[FINAL-STABILITY] 系統穩定性與 UX 最終戰

## 🎯 任務目標
完成所有導致交易中斷與數據丟失的核心修復。這是一次整合任務，目標是將系統推向 100% 的運行妥善率。

## 🚨 最終補強清單 (Post-Verification Fixes)

### T1. [P0] PnL 數據鮮活化徹底修補
- [ ] **連路巡檢**：確保 WebSocket MarkPrice -> Synchronizer -> Broadcaster -> DashboardEventBus -> UI 這一條鏈路完全暢通。
- [ ] **UI 渲染確認**：在 `Dashboard.razor` 的 `OnPositionPnLTicked` 加入 Debug Log，確認 UI 執行緒確實收到了數據並執行了畫面重繪。

### T2. [P0] 實驗室狀態「物理級」記憶
- [ ] **Singleton 強化**：確保 `LabStateContainer` 在整個 Session 期間不被重置。
- [ ] **表單強制回填**：每個參數表單必須在啟動時，以「快取優先」原則覆寫所有本地變數。

### T3. [S55] AI Prompt 參數字典對齊 (優化回饋)
- [ ] **字典注入**：修改 `AiAdvisorPanel`。生成 Prompt 時，自動將該模型在 `StrategyCatalog` 定義的 `ExpectedParameterKeys` 注入到指令中。
- [ ] **明確約束**：在 Prompt 加入：「請使用以下標準鍵名提供建議數值：[Key清單]」，消除 AI 亂猜名稱的問題。

## ✅ 驗收修正標準
- **[PnL-Alive]**：持倉出現後，不需手動重新整理，PnL 數字必須隨行情跳動。
- **[Memory-Solid]**：換頁、換策略 Tab 後，網格數值 100% 留存。
- **[Prompt-Sync]**：生成出的 Prompt 應包含正確的 `FastEmaPeriod` 等本系統鍵名。


## 📤 交付要求
- 完成後回報「全系統最終穩定性升級已就緒」。
- **請附上處理併發異常 (T2) 的核心代碼片段。**
