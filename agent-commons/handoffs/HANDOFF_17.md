# CryptoBot 專案交接文件 #17 (Checkpoint: s66b-reconciliation-complete)

> **版本**：Milestone 09 (Operations Resilience - Stage 2 Complete)
> **日期**：2026-04-25
> **狀態**：交易所對帳服務上線 · 持久化失效修復 · Guid 大小寫陷阱排除 · PM 紀律與憲章 v1.5 升級

---

## 📌 里程碑概述 (Milestone Summary)

本階段完成了運維韌性的第二塊拼圖：**交易所狀態對帳機制 (S66-B)**。我們成功部署了背景巡檢服務，用以自動清理「殭屍單/孤兒單」，並在過程中確診並排除了一個深藏於 SQLite 環境下的 Guid 格式比對陷阱。此外，本階段正式整併了使用者提出的工作流程優化，將憲章升級至 v1.5。

---

## 🚀 核心升級與修復戰果 (Key Achievements)

### 1. 🔄 交易所對帳服務 (OrderReconciliationService)
- **背景巡檢**：實作每分鐘一次的自動對帳，針對 `Status.New` 且超過時間閾值的訂單進行同步或 Reject 清理。
- **韌性偵測器**：在對帳邏輯中嵌入 `DB persistence mismatch!` 警示機制，能主動偵測 EF Core 追蹤失效。
- **孤兒清理 (A2)**：針對查無此單且超過 5 分鐘的 Pending 訂單，執行本地 Reject，確保狀態機不卡死。

### 2. 🔧 持久化失效診斷與 Guid 陷阱排除
- **確診根因**：實證了 SQLite 環境下 Guid `Id` 儲存為大寫 TEXT，若手動注入或查詢參數格式（大小寫）不符，會導致 `WHERE Id` 比對失敗並引發 `DbUpdateConcurrencyException`。
- **工法修正**：確認 `OrderRepository.UpdateAsync` 維持原始實作即可工作正常，關鍵在於維持資料 ID 的格式一致性。

### 3. ⚖️ 憲章治理與協作優化 (Charter v1.5)
- **角色權責鎖定**：正式確立「PM 絕對禁止修改業務程式碼」之鐵律，維持管理與執行層之專業分流。
- **語言與編碼規範**：強制全專案、GitHub Commit 與 Release Notes 預設使用 **繁體中文**；確立 `chcp 65001` 與「純粹代碼區塊」交付原則。
- **驗收品質強化**：要求 PM 必須忠實且完整地回寫歷史驗收紀錄，並確保指令格式不含行號以利複製。

---

## 📈 技術指標
- **測試通過率**：169/169 (100%)。
- **對帳週期**：1 Min (Tick) / 5 Min (Threshold)。
- **實盤準備度**：**🕒 進度 85%**。

---

## ⚠️ 下一階段預告 (Up Next)
- **[S31-LIVE] 實盤試車**：小額 VST/Live 驗證，正式進入真實交易環境。
- **[S66-A-errorCode-Refine]**：將 BingX 嗅探邏輯鎖定為確診的 `101400`。
- **[S29] UI 優化**：提升移動端 Dashboard 的操作體驗。

---
_「當我們與真實世界同步時，系統才具備了真正的生命力。」_
