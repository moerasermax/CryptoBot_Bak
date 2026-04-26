# 任務膠囊：[S42-S47] Dashboard 戰情室升級與策略全同步修補

## 🎯 任務目標
1. **全面透明化 (S42/S44)**：將 Dashboard 改為左右分欄戰情室，增加評估心跳燈與 30 筆滾動日誌。
2. **修復核心 Bug (S45)**：確保「套用」功能會同步更新策略的幣種、週期與模型類型。
3. **體驗優化 (S47)**：實驗室網格參數在切換頁面時具備記憶功能。
4. **大腦開發 (S43)**：新增 PA 價格行為預測模型。

## 📋 實作清單

### T1. 戰情室版面重組 (Dashboard Evolution)
- [ ] **左右佈局**：CSS Grid `350px 1fr`。左：策略卡片；右：滾動日誌(上) + 歷史表(下)。
- [ ] **心跳脈動**：策略名稱旁加入綠色 `.heartbeat-dot`，每分鐘評估時閃爍。
- [ ] **滾動日誌**：顯示最近 30 次 `AnalyzeAsync` 的詳細指標與決策（如：RSI=72 -> 觸發超買 -> 下單）。

### T2. 策略全屬性同步與轉型 (Morphing & Sync Fix)
- [ ] **LabEndpoints.cs**：
    - `/apply` API 接收 `OptimizationGlobals` (含 Symbol/Interval)。
    - 建立 `newConfig` 時強制覆寫目標策略的 `Symbol`, `Interval` 與 `StrategyType`。
- [ ] **自動改名**：改為 `[模型名] 幣種-週期 (Opt)`，例如 `[B46 Hybrid] SOL-15m (Opt)`。

### T3. 實驗室狀態持久化 (Lab Persistence)
- [ ] **LabStateContainer.cs**：新增 `GridSettingsCache` 字典，按策略 Key 儲存最後一次的 Min/Max/Step 設定。
- [ ] **BacktestLab.razor**：在切換策略 tab 時自動回填緩存設定。

### T4. PA 價格行為模型開發 (S43)
- [ ] **策略實作**：開發 `PriceActionPredictor`，分析影線長度、吞噬形態與動能得分。
- [ ] **出場智慧**：由大腦根據形態反轉主動平倉。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Sync]**：在 Lab 優化 SOL-15m 後套用，Dashboard 卡片應立即顯示為 SOL-15m。
- **[VCP-WarRoom]**：Dashboard 呈現左右分欄，且能看到不斷捲動的「決策理由」。
- **[VCP-Memory]**：在 Lab 設定好網格後點去 Dashboard 再回來，設定值沒有消失。

## 📤 交付要求
- 完成後回報「戰情室升級與同步系統已就緒」。
- **必須附上 LabEndpoints 中 Symbol 覆寫部分的代碼。**
