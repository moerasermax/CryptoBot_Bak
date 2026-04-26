# 任務膠囊：[S66-C] 結構化日誌與 Trace ID 追蹤 (Structured Logging & Tracing)

> **任務位階**：IRON §⑤ 風控透明化 與 運維韌性
> **執行者**：Claude (Chief Engineer)
> **目標**：在每一筆訊號觸發的最源頭產生唯一的 TraceId，並使其貫穿 Domain 實體 (Order)、執行層日誌與 UI 即時推播事件，以利故障排除與鏈路追蹤。

---

## 🎯 實作清單 (Implementation List)

### T1：日誌基礎設施設定
- 修改 `src/CryptoBot.ConsoleApp/Program.cs`：在 Serilog 的 `LoggerConfiguration` 中啟用 `Enrich.FromLogContext()`。
- 修改日誌輸出格式 (Template) 以包含 `{TraceId}` 佔位符。

### T2：Domain 與即時事件擴充 (Data Structures)
- **Domain**：在 `CryptoBot.Domain.Aggregates.OrderAggregate.Order` 新增 `string? TraceId` 欄位，並更新 `CreateLimitOrder` / `CreateMarketOrder` / `CreateStopMarketOrder` 等工廠方法接收此參數。
- **Realtime DTOs**：在以下 record 新增 `string? TraceId` 屬性（保持向後相容性，或作為建構子參數）：
  - `StrategyEvaluatedUpdate`
  - `StrategyEvaluationFailedUpdate`
  - `TradeFilledUpdate`

### T3：執行層 Trace ID 注入與傳遞 (StrategyExecutor)
- **進入點**：在 `src/CryptoBot.Application/Strategies/StrategyExecutor.cs` 的 `HandleKlineUpdateAsync` 第一行，使用 `Guid.NewGuid().ToString("N")[..12]` 生成一個短 Hash 作為 `TraceId`。
- **上下文綁定**：使用 `using (LogContext.PushProperty("TraceId", traceId))` 包裹整個 K 線處理邏輯。
- **向下傳遞**：
  - 廣播 `StrategyEvaluatedUpdate` 與 `StrategyEvaluationFailedUpdate` 時帶上此 `TraceId`。
  - 在 `HandleSignalAsync` 中，將 `TraceId` 傳遞給 `Order.Create*` 工廠方法。

---

## ✅ 驗收標準 (VCP)

1. **[VCP-Build]**：全專案編譯 0 警告、0 錯誤。
2. **[VCP-Log-Context]**：啟動系統並讓策略執行一次心跳，觀察終端機輸出的 `[INF]` 訊息中是否帶有類似 `[TraceId: 3f8a9b2c1d]` 的標籤。
3. **[VCP-Persistence]**：檢查 DB 中新建立的 `Orders`，確認 `TraceId` 欄位有值。
4. **[VCP-UI]**：(可選) 觀察 Dashboard 開發者工具的 SignalR WebSocket 流量，確認推播的 Payload 帶有 `traceId`。