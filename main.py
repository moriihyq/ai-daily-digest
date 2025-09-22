import os
import time
import traceback
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 模块一：获取文章列表 (无需修改) ---
def fetch_jqzj_articles(max_articles=3):
    print("开始通过API获取文章列表...")
    api_url = "https://www.jiqizhixin.com/api/v4/articles.json?sort=time&page=1"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.jiqizhixin.com/"}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        articles_found = []
        articles_list = data.get('articles', [])
        for item in articles_list[:max_articles]:
            title = item.get('title', '无标题')
            article_id = item.get('id')
            if article_id:
                link = f"https://www.jiqizhixin.com/articles/{article_id}"
                articles_found.append({'title': title, 'url': link})
        print(f"成功获取到 {len(articles_found)} 篇文章。")
        return articles_found
    except Exception as e:
        print(f"错误：获取文章列表API失败 - {e}")
        traceback.print_exc()
        return []

# --- 模块二：获取文章正文 (无需修改) ---
def get_article_content(url):
    print(f"正在使用Selenium加载文章页面: {url}...")
    chrome_options = Options()
    # 在GitHub Actions等无头环境中运行的必要参数
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        # 等待文章内容容器加载完成
        wait = WebDriverWait(driver, 15)
        content_div = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "detail__content"))
        )
        text_content = content_div.text
        print("成功使用Selenium提取到文章正文。")
        return text_content
    except Exception as e:
        print(f"错误：使用Selenium获取正文失败 - {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- 模块三：Gemini总结 (✨ 按照官方文档重写) ---
def summarize_with_gemini(title: str, content: str) -> str:
    """
    使用已配置好的 Gemini API 为文章生成结构化摘要。
    
    Args:
        title: 文章标题。
        content: 文章的文本内容。

    Returns:
        由 Gemini 生成的 Markdown 格式摘要，或一条错误信息。
    """
    if not content:
        print(f"因'{title}'文章内容为空，跳过Gemini总结。")
        return f"**对文章 '{title}' 的总结失败：未能获取到原文。**"
    
    print(f"正在使用Gemini总结文章: {title}")
    
    try:
        # 1. 选择一个现代且高效的模型 (官方推荐)
        # gemini-1.5-flash-latest 在速度和性能上取得了很好的平衡
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # 2. 构建一个结构清晰、指令明确的 Prompt
        prompt = f"""
        作为一名顶尖的AI技术分析师，请使用中文，为我精准地总结下面这篇关于“{title}”的文章。
        请严格按照以下Markdown格式输出，不要有任何多余的文字或解释：

        ### 1. 核心摘要
        （用一句话概括文章最核心的观点或成果。）

        ### 2. 关键要点
        - **要点一**：(提炼出第一个关键信息)
        - **要点二**：(提炼出第二个关键信息)
        - **要点三**：(提炼出第三个关键信息)

        ### 3. 价值洞察
        （从你的专业角度，分析这个技术或资讯可能带来的影响、应用前景或值得关注的亮点。）

        ---
        文章原文如下：
        {content[:25000]}
        """ # 增加了内容切片长度以适应更长的文章

        # 3. 调用API并返回结果
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"错误：调用Gemini API失败 - {e}")
        traceback.print_exc()
        return f"**对文章 '{title}' 的总结失败：API调用出错。**"

# --- 模块四：推送 (无需修改) ---
def push_to_wechat(token: str, title: str, content: str):
    print("正在使用 PushPlus 推送到微信...")
    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown" # 使用Markdown模板以获得更好的显示效果
    }
    try:
        response = requests.post(url, json=data)
        response_json = response.json()
        if response_json.get("code") == 200:
            print("成功：消息已通过 PushPlus 推送到微信！")
        else:
            print(f"错误：PushPlus 推送失败 - {response.text}")
    except Exception as e:
        print(f"错误：PushPlus 推送请求失败 - {e}")

# --- 主执行函数 (✨ 采用官方推荐的配置方式) ---
if __name__ == "__main__":
    # 1. 从环境变量中安全地获取密钥
    # 您的截图显示您已在GitHub Secrets中正确设置了 GEMINI_API_KEY
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN")

    if not gemini_api_key or not pushplus_token:
        print("错误：必须在环境变量中设置 GEMINI_API_KEY 和 PUSHPLUS_TOKEN")
    else:
        # 2. ✨ 程序开始时，一次性配置 Gemini API
        try:
            genai.configure(api_key=gemini_api_key)
            print("Gemini API 配置成功。")
        except Exception as e:
            print(f"错误：配置 Gemini API 失败 - {e}")
            exit() # 配置失败则直接退出

        # 3. 开始执行核心逻辑
        articles = fetch_jqzj_articles(max_articles=3)
        if articles:
            final_report = "## 🚀 AI前沿每日速报\n\n"
            for article in articles:
                content = get_article_content(article['url'])
                # ✨ 调用重写后的函数，无需再传入密钥
                summary = summarize_with_gemini(article['title'], content)
                
                final_report += f"### 📄 {article['title']}\n\n"
                final_report += f"**原文链接**：[{article['url']}]({article['url']})\n\n"
                final_report += summary
                final_report += "\n\n---\n\n"
                # 在文章处理间隙加入短暂延时，避免过于频繁的请求
                time.sleep(1) 
            
            # 4. 推送最终报告
            push_to_wechat(pushplus_token, "今日AI前沿速报", final_report)
        else:
            print("没有获取到文章，今日不推送。")











