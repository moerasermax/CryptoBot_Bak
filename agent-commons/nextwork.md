# CryptoBot Next Work

> **更新日期**：2026-05-13
> **當前狀態**：優化與新功能開發 (Evolution Mode)

---

## 🚀 執行中任務 (Active - 最高優先)

### [S72] 同步邏輯加固 (Reconciliation Hardening) 🚨
- [ ] **幽靈損益清理**：手動清理 `LINK-USDT` 殘留倉位數據。
- [ ] **同步器重構**：基於 Evidence-based 原則重寫同步邏輯，避免再次出現數據不對齊。

### [S75] Sidekick Hub — gemini --acp 長連接 IPC 重構 🚨 (與 [S72] 平級)
- [ ] **Phase 1**：探 ACP method schema (`authenticate` / `session.new`/`load` / `prompt` / `cancel`)。
- [ ] **Phase 2**：`GlobalAiChatService.cs` IPC 重構（long-lived `gemini --acp` + JSON-RPC stdin/stdout）。
- [ ] **Phase 3**：加固（429 retry + fallback model / cwd 隔離 / process tree kill）。
- [ ] **Phase 4**：整合測試 + VCP（既有 227 tests 不退步、新增 ACP IPC 整合測試）。
- 詳見 `agent-commons/capsules/TASK_S75_SIDEKICK_HUB.md` + `roles/engineer/drafts/2026-05-13_S75_PHASE0_REPORT.md`。
- 依賴：避免在 S72 完成前進入 Domain 層侵入性修改（限 Application + Infrastructure 層）。

### [S69] 貝氏優化引擎 (Python Sidecar)
- [ ] **實作 Python 端**：開發 `ai_ops/sidecar/` 優化邏輯，對齊 C# 端傳輸協定。

---

## 📅 待辦清單 (Backlog)

### [S31] LIVE 小額實盤部署 🚨
- [ ] **部署前哨**：確保所有核心同步邏輯 (S72) 於 Demo 盤穩定運行 24h。
- [ ] **環境切換**：準備正式環境 API Key。
