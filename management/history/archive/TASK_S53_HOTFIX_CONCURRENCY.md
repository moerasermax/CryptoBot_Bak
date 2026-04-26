# 緊急修復膠囊：[S53-HOTFIX] 資料庫併發衝突 (Concurrency Error)

## 🎯 任務目標
修正導致下單失敗的 `DbUpdateConcurrencyException`。確保當多個執行緒同時操作同一個策略或帳戶實體時，系統能透過 Reload/Retry 機制自動恢復，而非導致下單指令中斷。

## 🛠️ 技術診斷
- **報錯現場**：`SIGNAL BUY` 之後，系統執行資料落地時。
- **根本原因**：樂觀併發衝突。多個背景服務（Executor 與 Synchronizer）試圖同時更新同一行 `Strategies` 或 `Positions` 資料。

## 📋 修復清單

### T1. 全域併發重試機制 (Application/Infrastructure)
- [ ] **UnitOfWork 強化**：在 `SaveChangesAsync` 中封裝一個能處理併發異常的重試 Helper。
- [ ] **策略 Reload 邏輯**：當發生衝突時，呼叫 `Entry(entity).Reload()` 獲取最新資料庫狀態，並重新套用變更。

### T2. StrategyExecutor 流程加固 (Trading)
- [ ] 在 `HandleSignalAsync` 中，將下單紀錄與狀態更新包裝在更高層級的重試區塊中。
- [ ] 確保 `SIGNAL` 產出後，即使發生資料庫競爭，也必須完成下單並確保紀錄落地。

### T3. 事務邊界縮小 (Optimization)
- [ ] 減少不必要的全表更新。例如：心跳更新只更新時間戳，不應觸發整行實體的寫入。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Concurrent-Buy]**：在高頻模擬測試中，觀察出現 SIGNAL BUY 時。
- **預期結果**：即使 Log 中出現過短暫的 Retry 警告，最終訂單必須顯示為 `New` 或 `Filled`，且交易歷史出現紀錄。

## 📤 交付要求
- 完成後回報「資料庫併發衝突已解決」。
- **請附上處理 DbUpdateConcurrencyException 的重試代碼片段。**
