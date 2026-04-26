# 任務膠囊：[S66-A] 執行層冪等下單規約與防護 (Idempotent Ordering) v1.1

> **任務層級**：Milestone 09 (Operations Resilience)
> **觸發原因**：實盤前必須建立下單鏈路的絕對冪等性，防堵網路逾時或連線重置導致的重複開倉（雙倉/多倉）致命風險。前置任務 S63 與憲章 v1.2 已確立。本 v1.1 版本修補了「假冪等」漏洞，強制引入時間對齊與結構化 ID。

## 🎯 任務目標
在下單鏈路中強制導入基於 `ClientOrderId` 的冪等性保證。確保即使發生網路中斷或 API 逾時，同一個交易訊號也絕對不會在交易所產生超過一筆的真實訂單，且本地狀態機必須能優雅處理衝突而不崩潰。

## 📋 實作清單 (Chief Engineer)

### T0. 探針任務 (Probe Before Coding)
- **行動**：在動手修改架構前，必須先建立一個微型診斷指令（或腳本），對 BingX API 進行戳測（Probe）。
- **目標**：確認 BingX `ClientOrderId` 的真實長度上限（如 32 或 36 字元）與允許字元集（如英數、連字號）。
- **產出**：將探測結果記錄於 PR 或提交註解中，作為 T1 決定性 ID 長度截斷的依據。

### T1. 決定性 ID 生成器與介面 (Domain / Application Layer)
- **介面定義**：於 Domain 層 `OrderAggregate` 或 `Services` 內定義 `IClientOrderIdGenerator`。
- **實作要求**：
  - **嚴禁**使用 `Guid.NewGuid()`。
  - 必須採用雜湊或結構化字串：例如 `Hash(StrategyId + Symbol + Side + SignalTime)` 轉換為 Hex 字串，並依據 T0 探測結果進行安全截斷。
  - 保證：同一個策略、同一個時間切片、同一個方向的訊號，永遠產出 100% 相同的 ID。

### T2. 訊號時間對齊與防未來函數 (Domain Layer)
- **修復要求**：
  - `TradingSignal` 必須新增 `SignalTime` 屬性。
  - 呼叫 `IStrategy.AnalyzeAsync` 生成訊號時，必須傳入觸發該次評估的 `Kline.CloseTime`。
  - **鐵律 L2 強制**：`Kline.CloseTime` 必須使用 `interval.ToTimeSpan()` 動態推算，**嚴禁用 `DateTime.UtcNow`**，確保回測與實盤的時間切片絕對一致。

### T3. 資料庫唯一性約束 (Persistence Layer)
- **問題位置**：EF Core 設定檔（如 `OrderConfiguration`）。
- **修復要求**：
  - 為 `Order` 實體的 `ClientOrderId` 欄位加上 `.IsUnique()` 索引約束。
  - 確保本地資料庫在多執行緒併發寫入相同訊號時，能在資料庫層級被擋下。

### T4. 異常處理與對帳轉向 (Infrastructure Layer)
- **問題位置**：`BingXExchangeClient.PlaceOrderAsync` 及其呼叫端。
- **修復要求**：
  - 明確攔截 `ClientOrderId` 衝突的 API Error Code（如 BingX 的 `100414`、`100415` 或 `Duplicate order`）。
  - 若回傳訂單重複，不應視為致命錯誤拋出例外，應優雅攔截並將內部狀態轉向「查詢模式 (Query Order)」，獲取該訂單的實際成交狀態以推進本地狀態機。
  - 當 DB 發生 Unique 衝突時，系統必須保持 `_mutateLock` 不卡死。

### T5. 診斷同步進化 (DiagnosticTool)
- **問題位置**：`CryptoBot.DiagnosticTool` 專案。
- **修復要求**：
  - 新增指令：`s66a_check-order <clientOrderId>`。
  - 查詢本地 DB 顯示該訂單的紀錄與狀態。
  - 呼叫 `IExchangeClient` 查詢交易所端該訂單的真實狀態。
  - 比對兩者是否一致，並輸出明確的診斷結果。

## ✅ 驗證檢核點 (VCP)

- **[VCP-1] 絕對冪等保證**：通過 (2026-04-25 PM 實機驗證，Step 2 攔截成功)。
- **[VCP-2] 狀態機一致性**：通過 (DB Pending First 邏輯已入庫，測試 138/138 PASS)。
- **[VCP-3] 時間對齊無漂移**：通過 (靜態代碼複核確認使用 Kline.CloseTime)。
- **[VCP-4] 診斷綠燈**：通過 (s66a_check-order 輸出正確比對結果)。

## 🧪 實機驗證紀錄 (2026-04-25 PM Probe)
- **環境**：BingX Demo (VST)
- **Duplicate ErrorCode**：`101400`
- **Duplicate Message**：`clientOrderID unique check failed`
- **Not-Found Reaction**：`null`

## 📤 交付要求
- 附上 Unit Tests 或 Integration Tests 驗證 Time-out 與 DB Unique 衝突情境的全綠截圖。 ✅
- 附上執行 `s66a_check-order` 指令，成功追蹤訂單狀態的比對 Log。 ✅ (已於 2026-04-25 11:01 驗收完成)

## 💡 建議後續
1. 升級嗅探邏輯為精確 errorCode == 101400 比對。
2. 移除暫時性探針指令 probe-bingx。