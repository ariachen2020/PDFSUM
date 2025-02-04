import streamlit as st
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import os
import time
from google.api_core.exceptions import ResourceExhausted
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import PyPDF2
import io

# 設置 Google API 金鑰
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

# 初始化 Gemini 模型
try:
    model = genai.GenerativeModel('gemini-1.5-pro',
                                generation_config={
                                    'temperature': 0.7,
                                    'top_p': 0.8,
                                    'top_k': 40,
                                    'max_output_tokens': 2048,
                                })
except Exception as e:
    st.error(f"模型初始化失败: {str(e)}")
    model = None

def analyze_text(text):
    """使用 Gemini 分析文字"""
    if model is None:
        return "模型初始化失败，请刷新页面重试"
        
    prompt = f"""
    請分析以下文字，並提供:
    1. 主要摘要 (200字以內)
    2. 關鍵重點 (列點式)
    3. 關鍵字 (以逗號分隔)
    
    文字內容:
    {text}
    """
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except ResourceExhausted:
            if attempt == max_retries - 1:
                return "API 配额已达上限，请稍后再试。"
            time.sleep(retry_delay)
            continue
        except Exception as e:
            return f"分析过程发生错误: {str(e)}"

def generate_word_frequency(text):
    """生成文字頻率統計"""
    words = text.split()
    word_freq = Counter(words)
    return dict(word_freq.most_common(10))

def create_wordcloud(text):
    """生成文字雲"""
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    return plt

def get_url_content(url):
    """从网址获取内容"""
    try:
        # 验证URL格式
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return None, "请输入有效的网址"
        
        # 发送请求获取内容
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 使用BeautifulSoup解析内容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除script和style元素
        for script in soup(["script", "style"]):
            script.decompose()
            
        # 获取文本内容
        text = soup.get_text(separator=' ', strip=True)
        return text, None
        
    except requests.exceptions.RequestException as e:
        return None, f"获取网页内容失败: {str(e)}"
    except Exception as e:
        return None, f"处理过程发生错误: {str(e)}"

def extract_pdf_text(pdf_file):
    """从PDF文件中提取文本"""
    try:
        # 创建 PDF 文件对象
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # 提取所有页面的文本
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip(), None
    except Exception as e:
        return None, f"PDF处理失败: {str(e)}"

def main():
    st.title("文字分析工具")
    
    # 输入区域
    input_type = st.radio("选择输入方式:", ["直接输入文字", "输入网址", "上传PDF文件"])
    
    if input_type == "直接输入文字":
        text = st.text_area("请输入要分析的文字:", height=200)
    elif input_type == "输入网址":
        url = st.text_input("请输入网址:")
        if url:
            text, error = get_url_content(url)
            if error:
                st.error(error)
                text = ""
            else:
                st.success("成功获取网页内容")
                with st.expander("预览网页内容"):
                    st.text(text[:500] + "...")
    else:  # 上传PDF文件
        uploaded_file = st.file_uploader("选择PDF文件", type=['pdf'])
        if uploaded_file:
            text, error = extract_pdf_text(uploaded_file)
            if error:
                st.error(error)
                text = ""
            else:
                st.success("成功读取PDF文件")
                with st.expander("预览PDF内容"):
                    st.text(text[:500] + "...")
    
    if st.button("开始分析") and 'text' in locals() and text:
        with st.spinner("分析中..."):
            # AI 分析
            analysis_result = analyze_text(text)
            
            # 顯示分析結果
            st.subheader("AI 分析結果")
            st.write(analysis_result)
            
            # 生成並顯示文字雲
            st.subheader("文字雲視覺化")
            fig = create_wordcloud(text)
            st.pyplot(fig)
            
            # 生成並顯示詞頻統計
            st.subheader("詞頻統計")
            word_freq = generate_word_frequency(text)
            freq_df = pd.DataFrame(list(word_freq.items()), columns=['詞語', '頻率'])
            st.bar_chart(freq_df.set_index('詞語'))
            
            # 下載功能
            st.download_button(
                label="下載分析結果",
                data=f"分析結果:\n{analysis_result}\n\n詞頻統計:\n{freq_df.to_csv(index=False)}",
                file_name="analysis_result.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main() 