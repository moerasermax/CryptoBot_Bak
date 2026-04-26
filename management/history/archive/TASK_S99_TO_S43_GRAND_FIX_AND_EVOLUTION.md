# 任務膠囊：[S99-S43] 核心救火與戰情室全面進化

## 🎯 任務目標
這是一次涵蓋「底層修復」與「頂層體驗」的大型手術。必須優先解決導致無法下單與持倉隱形的 P0 級 Bug，隨後完成 Dashboard 的戰情室升級與新決策大腦的開發。

## 🚨 第一階段：緊急救火 (P0 Bug Fixes)

### T1. [S99] `Invalid cast` 轉型崩潰修復
- **問題**：觸發 SELL 訊號後，處理 Position 時發生字串轉 Symbol 的失敗。
- **行動**：檢查 `PositionRepository.cs` 與 `StrategyExecutor.cs`，確保所有讀寫邏輯皆正確處理 `Symbol` Value Object，避免強制轉型錯誤。

### T2. [S50] 智慧下單量與保證金保護 (Insufficient Margin)
- **問題**：系統死板使用靜態大額資金下單，導致模擬盤餘額不足被拒絕。
- **行動**：修改 `StrategyExecutor.CalculateQuantity`。下單前必須呼叫 `IExchangeClient.GetFuturesBalanceAsync` 獲取真實可用餘額，並以此動態計算下單量（預留 5% 緩衝）。

### T3. [S47-R] 實驗室「鋼鐵級」狀態記憶
- **問題**：切換頁面後，實驗室的網格參數 (Min/Max/Step) 會全部消失。
- **行動**：在 `LabStateContainer` 建立快取機制。當使用者修改表單時即時寫入；當回到 Lab 頁面時 (`OnInitializedAsync`)，強制從快取回填表單數值。

### T4. [BUGFIX] 持倉隱形競態條件修復 (Race Condition)
- **問題**：開單成功後，Dashboard 的 `Active Positions` 仍為空。
- **行動**：在 `StrategyExecutor.HandleOpenSignalAsync` 中，將 `_broadcaster.BroadcastTradeAsync` 的呼叫移至 `await _unitOfWork.SaveChangesAsync(ct);` 成功執行**之後**。確保前端收到 SignalR 推播去拉資料時，DB 已有紀錄。

---

## 🏟️ 第二階段：戰情室進化 (P1 UX & Features)

### T5. [S42 & S44] 戰情室左右分欄與滾動日誌
- **版面重組**：將 Dashboard 改為左右分欄 (`CSS Grid 350px 1fr`)。
- **心跳燈**：在策略名稱旁加入綠色 `.heartbeat-dot`，每分鐘評估時閃爍。
- **決策日誌**：在右側上方建立一個最多保留 30 筆的滾動 List，顯示最近的 `AnalyzeAsync` 詳細指標與決策結果。

### T6. [S45] 策略熱轉型與自動命名
- **自動轉型**：在 `/apply` API 中，確保套用參數時，強制覆寫目標策略的 `StrategyType`、`Symbol` 與 `Interval` 為實驗室當前設定。
- **自動改名**：依據規則 `[模型名] 幣種-週期 (Opt)` 重新命名策略（例如 `[B46 Hybrid] SOL-15m (Opt)`）。

### T7. [S43] 開發 PA 價格行為動能模型
- **策略開發**：新增 `PriceActionPredictor`。不依賴均線，純看 K 線實體/影線比例與吞噬形態來預測下一根漲跌。
- **出場智慧**：由大腦根據形態反轉主動發出平倉訊號。

## ✅ 驗證檢核點 (VCP)
- **[VCP-P0-Fixes]**：不噴 `Invalid cast`、不報 `Insufficient margin`、換頁參數不消失、開單後持倉立刻顯示。
- **[VCP-WarRoom]**：Dashboard 呈現左右分欄，綠燈會閃，日誌會滾，套用後名稱自動改變。

## 📤 交付要求
- 完成後回報「核心救火與戰情室進化已全面就緒」。
- **請附上 T2 中動態獲取餘額的代碼片段。**
