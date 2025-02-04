# PDF and Text Analysis Tool

一個基於 Streamlit 和 Google Gemini 的文本分析工具，支持：
- 直接文本輸入分析
- 網址內容分析
- PDF 文件分析

## 功能
- 文本摘要生成
- 關鍵重點提取
- 關鍵字提取

## 安裝步驟

1. 克隆專案


git clone [您的 repository URL]

2. 安裝依賴

bash
pip install -r requirements.txt

3. 設置 Google API Key
在 `.streamlit/secrets.toml` 中添加您的 API Key：

GOOGLE_API_KEY = "your-api-key-here"

4. 運行應用
```bash
streamlit run app.py
```

## 使用說明
1. 選擇輸入方式（直接輸入/網址/PDF）
2. 輸入或上傳內容
3. 點擊"開始分析"
4. 查看分析結果

## 注意事項
- 需要有效的 Google API Key
- PDF 必須是可提取文本的文件
- 網址必須可以公開訪問

