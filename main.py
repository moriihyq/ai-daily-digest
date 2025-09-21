import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import time

# --- 模块一：从“机器之心”网站爬取最新的AI文章 ---
# --- 模块一：从“机器之心”网站爬取最新的AI文章 (V2 - 更新版) ---
def fetch_jqzj_articles(max_articles=3):
    """
    从机器之心网站爬取最新的文章列表。
    :param max_articles: 你想获取的文章数量。
    :return: 一个包含文章字典（标题和链接）的列表。
    """
    print("开始从机器之心爬取最新文章...")
    # 目标URL和请求头
    url = "https://www.jiqizhixin.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles_found = []
        # V2更新：机器之心更新了前端样式，我们需要用新的class来定位文章
        # 现在文章列表项在 class='article-item_root__...'.
        article_items = soup.find_all('div', class_=lambda c: c and c.startswith('article-item_root__'), limit=max_articles)
        
        for item in article_items:
            # 标题和链接都在 class='article-item_titleLink__...' 的 <a> 标签里
            link_tag = item.find('a', class_=lambda c: c and c.startswith('article-item_titleLink__'))
            
            if link_tag:
                title = link_tag.get_text(strip=True)
                # 链接是相对路径，需要拼接成完整URL
                link = "https://www.jiqizhixin.com" + link_tag['href']
                articles_found.append({'title': title, 'url': link})
        
        print(f"成功爬取到 {len(articles_found)} 篇文章。")
        return articles_found
    except requests.RequestException as e:
        print(f"错误：爬取机器之心文章失败 - {e}")
        return []

def get_article_content(url):
    """
    根据给定的URL，爬取文章的正文内容。
    :param url: 文章链接。
    :return: 文章的纯文本内容。
    """
    print(f"正在爬取文章内容: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 机器之心的正文在 class="js-entry-content" 的 div 中
        content_div = soup.find('div', class_='js-entry-content')
        if content_div:
            # 提取所有文本，并用换行符连接
            text_content = '\n'.join(p.get_text(strip=True) for p in content_div.find_all('p'))
            return text_content
        else:
            print("警告：未找到文章正文内容。")
            return "无法提取文章内容。"
    except requests.RequestException as e:
        print(f"错误：爬取文章内容失败 - {e}")
        return None

# --- 模块二：使用Gemini API进行分析和总结 ---
def summarize_with_gemini(api_key, title, content):
    """
    使用Google Gemini API来总结文章。
    :param api_key: 你的Gemini API Key.
    :param title: 文章标题.
    :param content: 文章正文.
    :return: Gemini生成的Markdown格式总结.
    """
    print(f"正在使用Gemini总结文章: {title}")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # 精心设计的Prompt，告诉AI它是什么角色，要做什么，以及输出格式
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
    {content[:8000]}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"错误：调用Gemini API失败 - {e}")
        return f"**对文章 {title} 的总结失败。**"

# --- 模块三：通过Server酱推送到微信 ---
def push_to_wechat(send_key, title, content):
    """
    将格式化好的报告通过Server酱推送到微信。
    :param send_key: 你的Server酱SendKey.
    :param title: 推送的标题.
    :param content: 推送的主体内容，支持Markdown.
    """
    print("正在推送到微信...")
    url = f"https://sctapi.ftqq.com/{send_key}.send"
    data = {
        'title': title,
        'desp': content
    }
    try:
        response = requests.post(url, data=data)
        if response.json()["code"] == 0:
            print("成功：消息已推送到微信！")
        else:
            print(f"错误：推送失败 - {response.text}")
    except requests.RequestException as e:
        print(f"错误：推送请求失败 - {e}")

# --- 主执行函数：串联所有模块 ---
if __name__ == "__main__":
    # 从环境变量中获取密钥，这是最安全的方式
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    server_send_key = os.environ.get("SEND_KEY")

    if not gemini_api_key or not server_send_key:
        print("错误：必须在环境变量中设置 GEMINI_API_KEY 和 SEND_KEY")
    else:
        # 1. 爬取文章列表
        articles = fetch_jqzj_articles(max_articles=3)
        
        if articles:
            final_report = "## 🚀 AI前沿每日速报\n\n"
            
            # 2. 遍历每篇文章，获取内容并总结
            for article in articles:
                content = get_article_content(article['url'])
                if content:
                    summary = summarize_with_gemini(gemini_api_key, article['title'], content)
                    
                    # 3. 将总结格式化到最终报告中
                    final_report += f"### 📄 {article['title']}\n\n"
                    final_report += f"**原文链接**：[{article['url']}]({article['url']})\n\n"
                    final_report += summary
                    final_report += "\n\n---\n\n"
                    
                    # 友好等待，避免对目标网站造成太大压力
                    time.sleep(1) 
            
            # 4. 推送最终报告
            push_to_wechat(server_send_key, "今日AI前沿速报", final_report)
        else:

            print("没有获取到文章，今日不推送。")
