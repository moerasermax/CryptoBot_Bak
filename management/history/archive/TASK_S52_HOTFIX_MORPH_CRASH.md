# 緊急修復膠囊：[S52-HOTFIX] 跨模型套用 HTTP 500 崩潰

## 🎯 任務目標
修正當使用者將一組「少參數模型」(如 Bollinger) 的優化結果，套用到「多參數模型」(如 Price Action) 時，因參數鍵名不匹配導致的後端崩潰。

## 📋 修復清單

### T1. 參數結構重洗 (Api/Infrastructure)
- [ ] **LabEndpoints.cs**：
    - 在 `/apply` 邏輯中，如果是「跨模型套用」(SourceModelKey != TargetStrategyType)。
    - **禁用** `config.UpdateParameters(newOnes)`。
    - **改為**：根據實驗室當前模型的 `ExpectedParameterKeys`，從優化結果中提取數值。若結果中不存在某鍵，則使用預設值或 0。
    - 確保 `newConfig` 物件是乾淨的，不攜帶舊模型的殘留參數（如 `WickToBodyRatio` 不應出現在 Bollinger 策略中）。

### T2. 狀態機安全轉換 (Application)
- [ ] 確保套用時，若策略正在 `Running`，則 API 會透過 `IStrategyRuntimeController` 先執行 `Stop`。
- [ ] 換型、改名、更新參數後，再重新執行 `Start`。

### T3. 錯誤捕捉與反饋 (UX)
- [ ] 補齊 `try-catch`。當發生轉型或映射失敗時，回傳 `400 Bad Request` 並附上明確的「參數缺失」或「邏輯衝突」文字。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Cross-Apply]**：重複使用者的場景：
    1. 啟動一個 Price Action 策略 (多參數)。
    2. 在 Lab 優化 Bollinger (少參數)。
    3. 點擊套用。
    4. **預期結果**：系統應成功更名為 `[Bollinger] ADA-5m (Opt)`，狀態燈閃爍後重啟，參數僅剩 5 個。

## 📤 交付要求
- 完成後回報「跨模型套用崩潰已修復」。
- **請附上 LabEndpoints 中處理參數重新封裝的代碼片段。**
