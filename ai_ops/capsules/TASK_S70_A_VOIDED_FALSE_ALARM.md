> ⛔ **VOIDED 2026-04-27（工程師代為標註 — 使用者授權選項 B）**
> 本子膠囊在 PM 主膠囊（已 VOIDED）誤判延伸下建立，目標「修復 NullablePriceConverter」與「補全 LimitPrice」均建立在不存在的 bug 上：
> - `NullablePriceConverter.cs:13-18` 邏輯完全正確（null↔null、值↔值），無映射 bug
> - `OrderConfiguration.cs:33` 配置正確（無 IsRequired，允許 NULL）
> - Market / StopMarket 單 LimitPrice 天生 NULL（`Order.cs:114-178`），是設計正常
> 本膠囊整體無實作項目可執行，撤銷。後續 Dashboard PnL 顯示問題改由 `TASK_S70_DASHBOARD_PNL_CORRECTION.md` 處理。

---

# 膠囊：TASK_S70_A_FIX_PERSISTENCE_AND_RECONCILIATION（已撤銷）

## 1. 目標 (Objective)
- 修復 `Infrastructure.Persistence` 層 `NullablePriceConverter` 配置，確保 `LimitPrice` 正確落庫。
- 開發歷史數據修復工具，補全 DB 中已存在但遺失 `LimitPrice` 的歷史訂單。

## 2. 執行策略 (Strategy)
- [Diagnostic] 檢視 `CryptoBot.Infrastructure/Persistence/Configurations/OrderConfiguration.cs` 及相關 Converter 定義。
- [Act] 修正配置，確保 `decimal` 類型能正確映射。
- [Act] 實作 `s70_patch-orders` 工具，透過 `IExchangeClient` 查詢歷史訂單並以 `ExchangeOrderId` 映射修正 DB 紀錄。

## 3. 驗收標準 (Acceptance Criteria)
- 修正後新訂單 `LimitPrice` 不再為 NULL。
- 歷史訂單透過 PATCH 工具補全後，總損益計算正確。

## 4. 權責邊界 (Role)
- PM (我)：負責驗證邏輯與數據對齊。
- 工程師 (您)：負責程式碼修改、測試與工具開發。
