# HANDOFF_26

> **里程碑**：CryptoBot Sidekick (全域 AI 助理) 實裝 & 舊版 AI 建議路徑徹底清理。

---

## 1. 里程碑摘要
本 Session 完成了 [S74-C] 與 [S74-D] 任務，成功將 AI 輔助功能從單一頁面的按鈕，升級為全站常駐的「CryptoBot Sidekick」。同時執行了架構純粹化清理，移除了所有不再使用的舊版 IAiAdvisorService 及其相關實作，顯著提升了系統的維護性。

## 2. 完整膠囊清單
- **[S74-C] Global AI Sidebar**：實裝全域常駐側邊欄，支援 Scoped 多輪對話記憶與跨頁面參數套用。
- **[S74-D] Legacy Cleanup**：移除 `IAiAdvisorService` 體系，包含 Gemini HTTP 與舊版 InteractiveCli 實作，整合進 Sidekick。

## 3. Protocols 版本迭代軌跡
- **IRON §⑥ & §⑩ & §⑫**：全程遵循。新檔案 (5 檔) 皆包含 UTF-8 BOM，且維持 Infrastructure 與 ConsoleApp 之間的單向解耦（透過 Application 層介面）。

## 4. Institutional_Memory 新增段落引述
- *（無新增物理段落，本次為功能整合與架構清理）*

## 5. 技術指標
- **編譯**：`dotnet build` 通過 (Debug)，0 警告 0 錯誤。
- **測試**：227 項測試全綠 (0 失敗, 0 略過)。
- **Sidekick**：經預驗證支援 `gemini --session-id` 單發模式，對話歷史持久。

## 6. 下一階段預告
- **[S72] 同步邏輯加固**：重啟 `LINK-USDT` 幽靈損益清理與同步器重構任務。
- **[S69] 貝氏優化引擎**：開發 Python Sidecar 邏輯。
