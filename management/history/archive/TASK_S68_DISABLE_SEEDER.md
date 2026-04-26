# 任務膠囊：[S68] 環境清理 — 停用種子策略機制 🧹

## 1. 任務目標 (Goal)
關閉系統啟動時自動預置並執行測試策略的機制，以減少 Dashboard 上的背景噪音，確保使用者對策略狀態有完全的控制權。

## 2. 實作清單 (Implementation List)
- [ ] **[Setup]** 修改 `src/CryptoBot.ConsoleApp/appsettings.json`：將 `StrategySeed.Enabled` 設為 `false`。
- [ ] **[Cleanup]** 手動清理 DB（選做）：若使用者希望徹底移除該策略，請進入 `cryptobot.db` 刪除名為 `SMA-BTC15m-TestDrive` 的策略紀錄。
- [ ] **[Verification]** 啟動檢查：確保啟動 Log 顯示 `StrategySeed disabled — skipping.`。

## 3. 驗收檢核點 (VCP)
- **VCP-1 (Configuration)**: 檢查 `appsettings.json` 中 `Enabled` 欄位為 `false`。
- **VCP-2 (Startup Log)**: 啟動時不再出現 `Starting strategy SMA-BTC15m-TestDrive` 的日誌輸出。
- **VCP-3 (Dashboard)**: Dashboard 的策略列表中不再自動出現該測試策略。

## 4. 交付要求 (Deliverables)
- [ ] 完成設定檔更新。
- [ ] 產出簡單的啟動 Log 截圖或文字證明。

---
## 5. 驗證反饋紀錄 (History)
- 2026-04-26: 使用者反應種子策略造成 Dashboard 噪音，由 PM 立項停用。
