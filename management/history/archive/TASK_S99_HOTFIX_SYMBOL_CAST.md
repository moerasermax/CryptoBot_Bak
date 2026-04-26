# 緊急修復膠囊：[S99-HOTFIX] Symbol 轉型崩潰

## 🎯 任務目標
修正 EMA 策略觸發 SELL 訊號後導致的 `Invalid cast from 'System.String' to 'Symbol'` 異常。此錯誤導致系統無法正常結算平倉，視同無法下單。

## 🛠️ 技術診斷
- **報錯現場**：`SIGNAL SELL` 之後。
- **可能原因**：
    1. **S39 歷史系統副作用**：在紀錄 `Position` 到資料庫或從資料庫讀取時，`Symbol` 欄位被當作純 `String` 處理，但在實體類別中需要的是 `Symbol` Value Object。
    2. **Dapper/EF Mapping 缺失**：檢查 `PositionRepository` 是否缺少了將資料庫字串轉回 `Symbol` 物件的邏輯。

## 📋 修復清單
- [ ] **T1. 定位與重現**：讀取 `src/CryptoBot.Infrastructure/Persistence/Repositories/PositionRepository.cs`，檢查 `Symbol` 的讀取邏輯。
- [ ] **T2. 邏輯修正**：
    - 若使用 Dapper，確保已註冊 `SqlMapper.TypeHandler<Symbol>`。
    - 若使用 EF Core，確保 `PositionConfiguration` 已設定 `HasConversion`。
- [ ] **T3. 數據流巡檢**：檢查 `StrategyExecutor.cs` 在處理賣出訊號時，傳入 `Close()` 的參數類型是否正確。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Run]**：在 Dashboard 啟動策略，模擬或等待一個 SELL 訊號，確認不再噴出 `Invalid cast` 錯誤且交易歷史能正常跳出新紀錄。

## 📤 交付要求
- 完成後回報「Symbol 轉型 Bug 已徹底修復」。
- **請附上修正後的 Mapping 或轉換邏輯代碼片段。**
