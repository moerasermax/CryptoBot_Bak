# 任務膠囊：S26 視覺化儀表板升級 (ChartInsight)

## 🎯 任務目標
1. **動態權益圖表**：在 `/lab` 實驗室實作權益曲線 (Equity Curve) 的視覺化呈現。
2. **交易標註 (Markers)**：在曲線上精準標註 Buy/Sell 成交點，並顯示成交資訊。
3. **量化指標補完**：實作夏普比率 (Sharpe Ratio) 計算，整合至回測報告。

## 🛠️ 技術上下文 (Full Picture)
- **前端繪圖**：建議使用 **ApexCharts.JS** (CDN 引入) 搭配 Blazor JS Interop。
- **數據源**：使用 S25 實作的 `LeaderboardRowDto.EquityCurve` 與 `BacktestReport.Fills`。
- **指標位置**：`BacktestReport.cs` 及其 DTO 對應項。

## 📋 實作清單
### T1. 量化指標：夏普比率 (Math)
- [ ] 修改 `BacktestReport.cs`：
    - 實作 `SharpeRatio` 屬性。
    - 計算邏輯：以每日收益率（或每根 K 線收益率）的平均值除以標準差，並按年化係數縮放（年化係數 = sqrt(週期數/年)）。
    - 注意：若無成交或標準差為 0，Sharpe 回傳 0。

### T2. 圖表基礎建設 (Infrastructure)
- [ ] 在 `App.razor` 或 `_Host.cshtml` 引入 ApexCharts CDN：
    - `<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>`。
- [ ] 建立 `chart_interop.js` 並掛載至 `wwwroot`，實作繪圖與 Marker 更新邏輯。

### T3. 實驗室圖表呈現 (UI)
- [ ] 修改 `BacktestLab.razor`：
    - 當使用者點擊 Leaderboard 的某一行時，觸發「繪製該組細節圖表」。
    - 將 `EquityCurve` 映射為 X 軸 (Time) 與 Y 軸 (Equity)。
    - 將 `Fills` 映射為圖表上的 Annotation 或 Scatter Points（做多綠箭頭、做空紅箭頭）。
- [ ] **[VCP-Charter]**：確保圖表僅針對 Rank 1 或使用者選定的特定行進行渲染，避免前端效能過載。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-UI]**：回測完成後，點擊 Leaderboard 應能彈出或展開一個動態圖表。
- **[VCP-Accuracy]**：手動驗證夏普比率數值，確保在穩定獲利且波動小的策略（如低槓桿 SMA）下回傳正值且合理。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
