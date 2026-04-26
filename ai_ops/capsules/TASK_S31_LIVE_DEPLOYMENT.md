# 任務膠囊：[S31-LIVE] 小額實盤首單試車 (GO LIVE!) 💰

## 1. 任務目標 (Goal)
在實盤環境下，使用真實 USDT 進行首筆小額成交測試（5-10 USDT, 1x 槓桿），驗證全鏈路（下單、冪等、對帳、時鐘、風控）在真實交易所環境下的運作正確性。

## 2. 實作清單 (Implementation List)
- [ ] **[Diagnostic]** 環境預檢：驗證 API 金鑰連線性、帳戶餘額 (USDT > 20) 與時鐘偏差 (Skew < 500ms)。
- [ ] **[Diagnostic]** 實務精度探針：再次確認交易所步進值與精度 (Check Sizing/Precision)。
- [ ] **[Execution]** 啟動實盤策略：在 Dashboard 啟動指定策略，觀察日誌輸出。
- [ ] **[Verification]** 訂單生命週期追蹤：確認 TraceId 正確產生並透傳至交易所 ClientOrderId。
- [ ] **[Verification]** 對帳回歸：觀察 `OrderReconciliationService` 是否正確將交易所訂單狀態同步回本地。

## 3. 驗收檢核點 (VCP)
- **VCP-1 (Environment)**: `check-skew` 偏差絕對值必須 < 500ms (若 OS 未校時，禁止開車)。
- **VCP-2 (Balance)**: 帳戶內必須有足夠 USDT。
- **VCP-3 (Execution)**: 成功下達一張 `New` 狀態訂單，並在 1 分鐘內成交或手動平倉，且本地 DB 狀態同步為 `Filled`。
- **VCP-4 (TraceId)**: 透過 `check-order` 指令能看到該訂單的 TraceId 與 ClientOrderId 對齊。

## 4. 交付要求 (Deliverables)
- [ ] `Institutional_Memory.md` 更新：紀錄首筆實盤成交的延遲、errorCode (如有) 與對帳耗時。
- [ ] `HANDOFF_19.md`：紀錄 Milestone 10 (Go Live) 的初步成果。

---
## 5. 驗證反饋紀錄 (History)
*(待填寫)*
