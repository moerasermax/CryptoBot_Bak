# CryptoBot Next Work

> **更新日期**：2026-05-04
> **當前狀態**：數據修復中 (Recovery Mode)

---

## 🚀 執行中任務 (Active - 最高優先)

### [S72] 同步邏輯加固與幽靈損益清理 🚨
- [ ] **DB 修復**：修正 `LINK-USDT` 幽靈單損益，恢復 Dashboard 真實性。
- [ ] **同步器重構**：移除「盲猜市價」邏輯，改為「Trade History 實證對帳」。

### [S71] 數據脫節診斷 🏁
- [x] **診斷工具修復**：Option A 已落實。
- [x] **根因判定**：證實為同步器盲猜市價導致的幽靈損益。
- (本任務隨 S72 啟動後結案存檔)

---

## 📅 待辦清單 (Backlog)

### [S69-HOTFIX2] 無法平倉 Bug 待驗收 🚨
- [ ] **實盤驗證**：確認 RiskManager `already has 1 open positions` 錯誤已徹底消失。

### [S69] 貝氏優化引擎 (Python Sidecar)
- [ ] 實作 Python 端優化邏輯。

### [S31] LIVE 小額實盤部署
- [ ] 啟動小額實盤測試。
