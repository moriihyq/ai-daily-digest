import requests
import google.generativeai as genai
import os
import time
import traceback # 引入traceback库用于更详细的错误打印

# --- 模块一：爬虫 (V6 - 胜利最终版) ---
def fetch_jqzj_articles(max_articles=3):
    """
    通过你亲自找到的、当前正在使用的官方API来获取最新文章列表。
    :param max_articles: 你想获取的文章数量。
    :return: 一个包含文章字典（标题和链接）的列表。
    """
    print("开始通过API直连方式获取最新文章 (V6 - 胜利版)...")
    # 这是你找到的、经过验证的、当前网站正在使用的正确API地址
    api_url = f"https://www.jiqizhixin.com/api/v4/articles.json?sort=time&page=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.jiqizhixin.com/"
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        articles_found = []
        
        # 胜利的关键修正：从返回的字典中，精确地取出 'articles' 这个键对应的值（也就是文章列表）
        articles_list = data['articles']
        
        for item in articles_list[:max_articles]:
            # 根据你的截图，'title' 和 'id' 的键名无误
            title = item.get('title', '无标题')
            article_id = item.get('id')
            if article_id:
                # 链接结构也确认无变化
                link = f"https://www.jiqizhixin.com/articles/{article_id}"
                articles_found.append({'title': title, 'url': link})
        
        print(f"成功通过API获取到 {len(articles_found)} 篇文章。")
        return articles_found
    except Exception as e:
        print(f"错误：通过API获取文章失败 - {e}")
        traceback.print_exc() # 打印完整的错误堆栈，以备不时之需
        return []

# --- 模块二：获取文章正文 (保持不变) ---
def get_article_content(url):
    print(f"正在爬取文章内容: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', class_='js-entry-content')
        if content_div:
            text_content = '\n'.join(p.get_text(strip=True) for p in content_div.find_all('p'))
            return text_content
        else:
            print("警告：未找到文章正文内容。")
            return "无法提取文章内容。"
    except requests.RequestException as e:
        print(f"错误：爬取文章内容失败 - {e}")
        return None

# --- 模块三：Gemini总结 (保持不变) ---
def summarize_with_gemini(api_key, title, content):
    print(f"正在使用Gemini总结文章: {title}")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
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
        # 导入bs4用于解析html
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except Exception as e:
        print(f"错误：调用Gemini API失败 - {e}")
        return f"**对文章 {title} 的总结失败。**"

# --- 模块四：Server酱推送 (保持不变) ---
def push_to_wechat(send_key, title, content):
    print("正在推送到微信...")
    url = f"https://sctapi.ftqq.com/{send_key}.send"
    data = {'title': title, 'desp': content}
    try:
        response = requests.post(url, data=data)
        if response.json()["code"] == 0:
            print("成功：消息已推送到微信！")
        else:
            print(f"错误：推送失败 - {response.text}")
    except requests.RequestException as e:
        print(f"错误：推送请求失败 - {e}")

# --- 主执行函数 (保持不变) ---
if __name__ == "__main__":
    # 需要在GitHub Actions Secrets中配置好这两个密钥
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    server_send_key = os.environ.get("SEND_KEY")

    if not gemini_api_key or not server_send_key:
        print("错误：必须在环境变量中设置 GEMINI_API_KEY 和 SEND_KEY")
    else:
        articles = fetch_jqzj_articles(max_articles=3)
        if articles:
            final_report = "## 🚀 AI前沿每日速报\n\n"
            for article in articles:
                # BeautifulSoup需要单独安装，确保requirements.txt里有它
                from bs4 import BeautifulSoup
                content = get_article_content(article['url'])
                if content:
                    summary = summarize_with_gemini(gemini_api_key, article['title'], content)
                    final_report += f"### 📄 {article['title']}\n\n"
                    final_report += f"**原文链接**：[{article['url']}]({article['url']})\n\n"
                    final_report += summary
                    final_report += "\n\n---\n\n"
                    time.sleep(1) 
            push_to_wechat(server_send_key, "今日AI前沿速报", final_report)
        else:
            print("没有获取到文章，今日不推送。")




