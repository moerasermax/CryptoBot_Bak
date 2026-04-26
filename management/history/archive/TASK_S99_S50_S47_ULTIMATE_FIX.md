# 任務膠囊：[S99-S50-S47] 核心穩定性大三元修復 (救火任務)

## 🎯 任務目標
徹底修復導致系統「無法成交」與「實驗室失憶」的三大核心缺陷：
1. **轉型崩潰 (S99)**：解決 SELL 訊號後的 `Invalid cast`。
2. **保證金不足 (S50)**：實現動態下單量校正。
3. **實驗室失憶 (S47)**：實作網格參數的深度持久化。

## 📋 實作清單

### T1. [S99] Symbol 轉型與 Repository 修復
- [ ] **檢查 PositionRepository.cs**：確保從資料庫讀取 `Symbol` 欄位時，正確使用了 Value Object 轉換，而非直接塞入字串。
- [ ] **檢查 StrategyExecutor.cs**：定位 `SIGNAL SELL` 後的結算流程，確保傳入 `Close()` 的參數類型 100% 匹配。

### T2. [S50] 智慧下單量與保證金保護
- [ ] **動態餘額感應**：修改 `StrategyExecutor.CalculateQuantity`。
    - **邏輯**：下單前必須呼叫 `IExchangeClient.GetFuturesBalanceAsync` 獲取真實可用餘額。
    - **計算公式**：`MaxNotional = AvailableBalance * Leverage * 0.95` (保留 5% 緩衝避免 Rejected)。
    - **縮放**：若計算出的 Qty 超過 MaxNotional，則自動下調至安全範圍。

### T3. [S47-REVISED] 實驗室「鋼鐵級」狀態記憶
- [ ] **LabStateContainer.cs**：
    - 建立 `GridStateStore`：儲存包含 `Min`, `Max`, `Step`, `Symbol`, `Interval` 在內的所有 UI 欄位狀態。
- [ ] **BacktestLab.razor** 與各子表單：
    - 在 `OnInitializedAsync` 時強制從 `GridStateStore` 恢復數據。
    - 在任何 `@bind:after="OnChanged"` 觸發時，同步寫回 Store。
- [ ] **目標**：切換到 Dashboard 再回來，所有網格參數必須完好如初。

## ✅ 驗證檢核點 (VCP)
- **[VCP-No-Cast-Error]**：觸發 SELL 訊號不再噴出 `Invalid cast`。
- **[VCP-No-Rejected]**：即使帳戶餘額減少，下單量會自動縮減，不再出現 `Insufficient margin` 報錯。
- **[VCP-Lab-Memory]**：在 Lab 設定複雜網格後換頁再回，數值 100% 留存。

## 📤 交付要求
- 完成後回報「核心大三元修復已就緒」。
- **請附上 StrategyExecutor 中「動態可用餘額」獲取的代碼片段。**
