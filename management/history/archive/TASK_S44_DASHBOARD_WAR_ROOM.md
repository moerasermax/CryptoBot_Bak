# 任務膠囊：[S44] Dashboard 戰情室版面重組與滾動日誌

## 🎯 任務目標
將 Dashboard 升級為「交易戰情室」佈局，善用寬螢幕空間，並提供即時滾動的「決策日誌」，讓使用者能追蹤 Bot 的每一次評估細節，不再盲目等待。

## 📋 實作清單

### T1. 滾動決策日誌 (Realtime/UI)
- [ ] **日誌模型**：建立 `EvaluationEntry` 物件（含時間、幣種、策略、指標摘要、決策結果）。
- [ ] **滾動窗口**：在 Dashboard 實作一個 List，每當有新評估即推入。
- [ ] **逐筆移除邏輯**：使用 `LinkedList` 或 `Queue` 維持最大 30 筆紀錄。

### T2. 左右分欄版面重組 (ConsoleApp/UI)
- [ ] **CSS Grid 佈局**：
    - 將 Dashboard 的主容器改為 `grid-template-columns: 350px 1fr;`。
    - **左側欄**：顯示 Active Strategy 策略卡片（心跳燈位置）。
    - **右側主區**：
        - 上半：決策動態日誌（具備獨立捲軸）。
        - 下半：交易歷史表（TradeHistoryTable）。
- [ ] **全站寬度**：確保在 95% 寬度下，左右兩欄的比例視覺平衡。

### T3. 視覺細節優化 (UX)
- [ ] **日誌樣式**：
    - `[INF]` (一般評估) 灰色。
    - `[SIGNAL BUY/SELL]` 亮綠/亮紅。
    - `[ERROR]` 橘色。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Layout]**：在大螢幕上觀察，Dashboard 不再是長長一條，而是左右併排。
- **[VCP-Rolling]**：觀察 30 分鐘後，日誌是否正確維持在 30 筆，且最新的一筆位於最上方（或最下方）。

## 📤 交付要求
- 完成後回報「Dashboard 戰情室版面已進化」。
- **請附上 Dashboard 左右分欄的 CSS Grid 代碼片段。**
