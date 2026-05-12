# CryptoBot Next Work

> **更新日期**：2026-05-12
> **當前狀態**：優化與新功能開發 (Evolution Mode)

---

## 🚀 執行中任務 (Active - 最高優先)

### [S72] 同步邏輯加固 (Reconciliation Hardening) 🚨
- [ ] **幽靈損益清理**：手動清理 `LINK-USDT` 殘留倉位數據。
- [ ] **同步器重構**：基於 Evidence-based 原則重寫同步邏輯，避免再次出現數據不對齊。

### [S69] 貝氏優化引擎 (Python Sidecar)
- [ ] **實作 Python 端**：開發 `ai_ops/sidecar/` 優化邏輯，對齊 C# 端傳輸協定。

---

## 📅 待辦清單 (Backlog)

### [S31] LIVE 小額實盤部署 🚨
- [ ] **部署前哨**：確保所有核心同步邏輯 (S72) 於 Demo 盤穩定運行 24h。
- [ ] **環境切換**：準備正式環境 API Key。
