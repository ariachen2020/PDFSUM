import os
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'error'
import streamlit as st
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import time
from google.api_core.exceptions import ResourceExhausted
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import PyPDF2
import io

# 初始化 Gemini 模型
try:
    model = genai.GenerativeModel('gemini-1.5-pro',
                                generation_config={
                                    'temperature': 0,
                                    'top_p': 0.95,
                                    'top_k': 50,
                                    'max_output_tokens': 4096,
                                })
except Exception as e:
    st.error(f"模型初始化失败: {str(e)}")
    model = None

def initialize_model(api_key):
    """初始化 Gemini 模型"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash',
                                    generation_config={
                                        'temperature': 0.7,
                                        'top_p': 0.8,
                                        'top_k': 40,
                                        'max_output_tokens': 8192,  # 2.0-flash 支持更大的輸出限制
                                    })
        return model
    except Exception as e:
        return None

def analyze_text(text, model):
    """使用 Gemini 分析文字"""
    if model is None:
        return "模型初始化失败，请检查 API Key"
        
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
        except Exception as e:
            if attempt == max_retries - 1:
                return f"分析过程发生错误: {str(e)}"
            time.sleep(retry_delay)
            continue

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

def batch_analyze_pdfs(files, model):
    """批量分析多個PDF文件"""
    results = {}
    for file in files:
        try:
            text, error = extract_pdf_text(file)
            if error:
                results[file.name] = f"處理失敗: {error}"
                continue
                
            analysis = analyze_text(text, model)
            results[file.name] = analysis
            
        except Exception as e:
            results[file.name] = f"處理失敗: {str(e)}"
    
    return results

def main():
    st.title("文字分析工具")
    
    # API Key 输入区域
    api_key = st.sidebar.text_input("输入 Google API Key:", type="password")
    if not api_key:
        st.warning("请先输入 Google API Key")
        st.info("获取 API Key 的步骤：\n1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)\n2. 登录并创建 API Key")
        return
    
    # 初始化模型
    model = initialize_model(api_key)
    if model is None:
        st.error("API Key 无效或初始化失败")
        return
    
    # 输入区域
    input_type = st.radio("选择输入方式:", ["直接输入文字", "输入网址", "上传PDF文件", "批量处理PDF"])
    
    if input_type == "直接输入文字":
        text = st.text_area("请输入要分析的文字:", height=200)
        if st.button("开始分析") and text:
            with st.spinner("正在分析中..."):
                result = analyze_text(text, model)
                st.write(result)
                
    elif input_type == "输入网址":
        url = st.text_input("请输入网址:")
        if url and st.button("开始分析"):
            with st.spinner("获取网页内容..."):
                text, error = get_url_content(url)
                if error:
                    st.error(error)
                else:
                    st.success("成功获取网页内容")
                    with st.expander("预览网页内容"):
                        st.text(text[:500] + "...")
                    with st.spinner("正在分析中..."):
                        result = analyze_text(text, model)
                        st.write(result)
                        
    elif input_type == "上传PDF文件":
        uploaded_file = st.file_uploader("选择PDF文件", type=['pdf'])
        if uploaded_file and st.button("开始分析"):
            with st.spinner("处理PDF文件..."):
                text, error = extract_pdf_text(uploaded_file)
                if error:
                    st.error(error)
                else:
                    st.success("成功读取PDF文件")
                    with st.expander("预览PDF内容"):
                        st.text(text[:500] + "...")
                    with st.spinner("正在分析中..."):
                        result = analyze_text(text, model)
                        st.write(result)
                        
    else:  # 批量处理PDF
        uploaded_files = st.file_uploader("选择多个PDF文件", type=['pdf'], accept_multiple_files=True)
        if uploaded_files and st.button("开始批量分析"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = {}
            for i, file in enumerate(uploaded_files):
                status_text.text(f"正在处理: {file.name}")
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                
                with st.expander(f"文件: {file.name}", expanded=False):
                    text, error = extract_pdf_text(file)
                    if error:
                        st.error(f"处理失败: {error}")
                        continue
                        
                    result = analyze_text(text, model)
                    st.write(result)
                    results[file.name] = result
            
            progress_bar.progress(1.0)
            status_text.text("处理完成！")
            
            # 提供下载分析结果的功能
            if results:
                combined_results = "\n\n".join([f"=== {filename} ===\n{content}" 
                                              for filename, content in results.items()])
                st.download_button(
                    label="下载分析结果",
                    data=combined_results,
                    file_name="batch_analysis_results.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main() 