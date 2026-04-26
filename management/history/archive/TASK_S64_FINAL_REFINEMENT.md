# 任務膠囊：[S64] 系統精煉與制度記憶持久化 (Final Refinement)

> **任務層級**：Major (架構優化與知識沉澱)
> **設計準則**：精簡代碼、消除歧義、傳承教訓。

## 🎯 任務總目標
1. 清理專案中過時且具備誤導性的 `Trading/StrategyExecutor.cs` 代碼，消除「雙執行引擎」的分歧隱患。
2. 建立專案專屬的技術避坑指南 `Institutional_Memory.md`，將先前開發過程中的慘痛教訓轉化為可傳承的制度資產。

## 📋 實作清單
### Phase 1: 死碼清理 (System Cleanup)
- [ ] **[移除死碼]**：直接刪除 `src/CryptoBot.Application/Trading/StrategyExecutor.cs`。
    - **原因**：該檔案目前未被 DI 使用且邏輯與生產線版本分歧，保留它會增加維護成本與誤用風險。
- [ ] **[編譯檢查]**：確保刪除後，全專案（含測試）能正常編譯，無殘留引用。

### Phase 2: 制度記憶建立 (Institutional Memory)
- [ ] **[建立文件]**：建立 `management/protocols/Institutional_Memory.md`。
- [ ] **[核心內容]**：至少包含以下三點已驗證的技術教訓：
    1. **S62 精度解析教訓**：BingX SDK 的 `*Precision` 是小數位數（int），不是步進值（StepSize）。計算量能時必須使用 `10^(-n)` 轉換，或優先讀取 `QuantityStep/StepSize`。
    2. **S63 沉默 Bug 診斷**：若 `TrimInProgressTail` 防護失效，應優先檢查 `CloseTime` 是否推算錯誤；若中文字亂碼，應確認 `.cs` 檔案是否具備 **UTF-8 BOM**。
    3. **介面擴充慣例**：當擴充 `IExchangeClient` 介面時，必須同步更新所有 5 個實作者（含模擬器與 3 個測試 Fake），確保編譯鏈路與測試環境完整。

## 📤 總體驗收交付物 (VCP)
- **[VCP-Cleanup]**：確認 `src/CryptoBot.Application/Trading/StrategyExecutor.cs` 已徹底從專案中移除。
- **[VCP-Build]**：全專案編譯 0 警告 0 錯誤。
- **[VCP-Memory]**：確認 `Institutional_Memory.md` 內容完整且路徑正確。

---
📝 **最終驗收報告**
- **工程師實證**：徹底移除 `Trading/` 目錄及其子項。建立 `Institutional_Memory.md`，整合 S61/S62/S63 的核心技術教訓與自檢清單。
- **地端驗收結果**：確認目錄已刪除，文檔內容結構化且具備高度技術參考價值。全專案編譯與測試保持綠燈。 ✅
