# 任務膠囊：[S61] 訂單狀態同步檢測 (Ghost Order Inspector)

> **任務層級**：Critical (交易安全)
> **設計準則**：透明監控、防範幽靈、雙向校驗。

## 🎯 任務總目標
實作「幽靈訂單」巡檢機制，確保本地 `Orders` 表與交易所實際掛單狀態完全一致。

## 📋 實作清單
- [x] **[介面擴充]**：`IExchangeClient` 增加 `GetOpenOrdersAsync`。
- [x] **[指令實作]**：實作 `s61_sync-orders` 指令。

## 📤 總體驗收交付物 (VCP)
- **[VCP-Audit]**：列出所有不一致項。
- **[VCP-Safety]**：幽靈訂單顯著警告。

---
📝 **最終驗收報告**
- **工程師實證**：已實作 `S61_SyncOrdersCommand.cs`。
- **PM 地端驗證日誌**：
  ```text
  === Ghost Order Inspector ===
  Local Active : 5 | Exchange Open : 0
  -- Local-only (Ghosts Detected) --
  ExchId=2047...80 Side=Buy Status=PartiallyFilled -> Suggest: Sync/Cancel
  Verdict: Inspector successfully identified local-only out-of-sync orders.
  ```
- **驗收狀態**：驗收通過 ✅ (SDK 鏈路已於 S61-HOTFIX 修復)
