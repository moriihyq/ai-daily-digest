import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import time
import traceback

# --- 模块一：获取文章列表 (V6 - 已验证) ---
def fetch_jqzj_articles(max_articles=3):
    print("开始通过API获取文章列表 (V6)...")
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
                # 我们同时需要id和url
                link = f"https://www.jiqizhixin.com/articles/{article_id}"
                articles_found.append({'title': title, 'url': link, 'id': article_id})
        print(f"成功获取到 {len(articles_found)} 篇文章。")
        return articles_found
    except Exception as e:
        print(f"错误：获取文章列表API失败 - {e}")
        traceback.print_exc()
        return []

# --- 模块二：获取文章正文 (V4 - API直连最终版) ---
def get_article_content(article_id):
    """
    通过文章ID，直接请求内容API，获取最干净的文章正文HTML。
    """
    print(f"正在通过内容API获取文章正文 (ID: {article_id})...")
    # 这就是隐藏的内容API
    content_api_url = f"https://www.jiqizhixin.com/api/v1/articles/{article_id}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.jiqizhixin.com/"}
    try:
        response = requests.get(content_api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # 从返回的JSON中，找到包含HTML正文的键
        html_content = data.get('data', {}).get('content')
        if html_content:
            # 使用BeautifulSoup解析这段HTML，提取纯文本
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = '\n'.join(p.get_text(strip=True) for p in soup.find_all('p'))
            print("成功提取到文章正文。")
            return text_content
        else:
            print("警告：内容API返回的数据中没有正文。")
            return None
    except Exception as e:
        print(f"错误：请求内容API失败 - {e}")
        return None

# --- 模块三：Gemini总结 (V3 - 旗舰模型版) ---
def summarize_with_gemini(api_key, title, content):
    if not content:
        print(f"因'{title}'文章内容为空，跳过Gemini总结。")
        return f"**对文章 '{title}' 的总结失败：未能获取到原文。**"
    print(f"正在使用Gemini总结文章: {title}")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    作为一名顶尖的AI技术分析师，请使用中文，为我精准地总结下面这篇关于“{title}”的文章。
    请严格按照以下Markdown格式输出，不要有任何多余的文字：

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
    {content[:20000]}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"错误：调用Gemini API失败 - {e}")
        return f"**对文章 '{title}' 的总结失败：API调用出错。**"

# --- 模块四：Server酱推送 (保持不变) ---
def push_to_wechat(send_key, title, content):
    print("正在推送到微信...")
    url = f"https://sctapi.ftqq.com/sctapi/v1/send" # 使用V1版本send API
    data = {'title': title, 'desp': content}
    try:
        response = requests.post(url, params={'sendkey': send_key}, data=data)
        if response.json().get("code") == 0:
            print("成功：消息已推送到微信！")
        else:
            print(f"错误：推送失败 - {response.text}")
    except Exception as e:
        print(f"错误：推送请求失败 - {e}")

# --- 主执行函数 (V3 - 最终版) ---
if __name__ == "__main__":
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    server_send_key = os.environ.get("SEND_KEY")

    if not gemini_api_key or not server_send_key:
        print("错误：必须在环境变量中设置 GEMINI_API_KEY 和 SEND_KEY")
    else:
        articles = fetch_jqzj_articles(max_articles=3)
        if articles:
            final_report = "## 🚀 AI前沿每日速报\n\n"
            for article in articles:
                # 调用内容获取函数时，传入article ID
                content = get_article_content(article['id'])
                summary = summarize_with_gemini(gemini_api_key, article['title'], content)
                final_report += f"### 📄 {article['title']}\n\n"
                final_report += f"**原文链接**：[{article['url']}]({article['url']})\n\n"
                final_report += summary
                final_report += "\n\n---\n\n"
                time.sleep(1) 
            push_to_wechat(server_send_key, "今日AI前沿速报", final_report)
        else:
            print("没有获取到文章，今日不推送。")






