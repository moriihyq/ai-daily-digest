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

# --- 模块一：获取文章列表 ---
def fetch_jqzj_articles(max_articles=3): # <-- 修改回获取 3 篇文章
    print(f"开始通过API获取 {max_articles} 篇最新文章...")
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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        content_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "detail__content")))
        text_content = content_div.text
        print("成功使用Selenium提取到文章正文。")
        return text_content
    except Exception as e:
        print(f"错误：使用Selenium获取正文失败 - {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- 模块三：Gemini总结 (无需修改) ---
def summarize_with_gemini(title: str, content: str) -> str:
    if not content:
        print(f"因'{title}'文章内容为空，跳过Gemini总结。")
        return f"**对文章 '{title}' 的总结失败：未能获取到原文。**"
    print(f"正在使用Gemini为学生视角总结文章: {title}")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""
        作为一名优秀的AI技术研究者和科普专家，请为一名正在学习人工智能的大学二年级学生，深入浅出地解读下面这篇关于“{title}”的文章。
        请严格按照以下Markdown格式输出，语言要既专业又易于理解：
        ### 📚 核心摘要 (一句话概括)
        （用最凝练的一句话，说明白这篇文章的核心贡献或观点是什么。）
        ### 📚 主要内容 (总结全文)
        （要求结构清晰，易懂，不要太长）
        ### 💡 关键要点 (技术视角)
        - **技术点一**：(深入挖掘第一个关键信息，如果涉及特定算法、模型结构或技术方法，请点出其名称和作用。)
        - **技术点二**：(同上，解释第二个关键信息，侧重于“如何实现”或“为何有效”。)
        ### 👨‍💻 对我的价值 (学习与实践)
        - **知识关联**：(这篇文章的内容，与我在大学课程（如机器学习、深度学习）中学到的哪个具体知识点相关？)
        - **实践建议**：(基于这篇文章，我如果想动手实践，可以尝试什么？)
        ---
        文章原文如下：
        {content[:20000]}
        """
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
    data = {"token": token, "title": title, "content": content, "template": "markdown"}
    try:
        response = requests.post(url, json=data)
        response_json = response.json()
        if response_json.get("code") == 200:
            print("成功：消息已通过 PushPlus 推送到微信！")
        else:
            print(f"错误：PushPlus 推送失败 - {response.text}")
    except Exception as e:
        print(f"错误：PushPlus 推送请求失败 - {e}")

# --- 模块五：抓取 GitHub Trending 项目 (无需修改) ---
def fetch_github_trending(top_n=1):
    print(f"开始抓取 GitHub Trending Top {top_n} Python 项目...")
    url = "https://github.com/trending/python?since=daily"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        repo_list = soup.find_all('article', class_='Box-row')
        trending_repos = []
        for repo in repo_list[:top_n]:
            repo_title_element = repo.find('h2', class_='h3 lh-condensed').find('a')
            repo_name = repo_title_element.get_text(strip=True).replace(" / ", "/")
            repo_relative_url = repo_title_element['href']
            repo_url = f"https://github.com{repo_relative_url}"
            description_element = repo.find('p', class_='col-9 color-fg-muted my-1 pr-4')
            repo_description = description_element.get_text(strip=True) if description_element else "暂无描述。"
            star_element = repo.find('a', href=f"{repo_relative_url}/stargazers")
            repo_stars = star_element.get_text(strip=True) if star_element else "N/A"
            trending_repos.append({'name': repo_name, 'url': repo_url, 'description': repo_description, 'stars': repo_stars})
        print(f"成功抓取到 {len(trending_repos)} 个热门项目。")
        return trending_repos
    except Exception as e:
        print(f"错误：抓取 GitHub Trending 失败 - {e}")
        traceback.print_exc()
        return []

# --- 模块六：使用 Gemini 分析开源项目 (无需修改) ---
def analyze_project_with_gemini(project_data: dict) -> str:
    print(f"正在使用 Gemini 分析开源项目: {project_data['name']}")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""
        作为一名资深的AI技术导师和顶尖的开源项目贡献者，先深入了解这个项目的准确具体内容，请为一名AI专业的大学生，深入解读下面这个今天在GitHub上很热门的开源项目。
        项目名称：{project_data['name']}
        项目描述：{project_data['description']}
        项目链接：{project_data['url']}
        星标数：{project_data['stars']}
        请严格按照以下Markdown格式输出：
        ### 🌟 项目速览 (Project Overview)
        （用一句话概括这个项目是做什么的，核心价值是什么。）
        ### 💡 价值与痛点 (Value & Pain Point)
        （分析这个项目为什么会变得热门？它解决了哪个具体痛点？）
        ### 🛠️ 技术栈亮点 (Tech Stack Highlights)
        （根据园原项目的具体内容，详细说明它用到了哪些关键的技术、框架或库？其中有没有值得关注的亮点？）
        ### 📖 作为大二AI学生，如何学习这个项目？对我的发展有什么帮助，我能学到什么
        - **第一步**：（给出开始学习这个项目的具体步骤。）
        - **第二步**：(给出深入学习的建议。)
        - **第三步**：(给出对我现阶段学习的指导意义和启发)
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"错误：调用 Gemini 分析项目失败 - {e}")
        traceback.print_exc()
        return f"**对项目 '{project_data['name']}' 的分析失败：API调用出错。**"

# --- 主执行函数 (V4 - 三篇文章 + 一个项目) ---
if __name__ == "__main__":
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN")

    if not gemini_api_key or not pushplus_token:
        print("错误：必须在环境变量中设置 GEMINI_API_KEY 和 PUSHPLUS_TOKEN")
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            print("Gemini API 配置成功。")
        except Exception as e:
            print(f"错误：配置 Gemini API 失败 - {e}")
            exit()

        final_report = "## 🚀 华工AI学子专属速报\n\n"
        
        # --- Part 1: 文章速览 (三篇) ---
        final_report += "### 📰 今日文章速览\n"
        articles = fetch_jqzj_articles(max_articles=3) # <-- 获取三篇文章
        if articles:
            # ✨ 使用 for 循环来处理每一篇文章
            for index, article in enumerate(articles):
                print(f"--- 开始处理第 {index+1}/{len(articles)} 篇文章 ---")
                content = get_article_content(article['url'])
                summary = summarize_with_gemini(article['title'], content)
                
                final_report += f"#### {index+1}. {article['title']}\n"
                final_report += f"**原文链接**：[{article['url']}]({article['url']})\n\n"
                final_report += summary
                
                if index < len(articles) - 1:
                    final_report += "\n\n" # 在文章之间添加一些间距
        else:
            final_report += "今日未能获取到新文章。\n"
            
        final_report += "\n---\n\n"

        # --- Part 2: 热门开源项目分析 (一篇) ---
        final_report += "### 💻 今日热门开源项目\n"
        trending_projects = fetch_github_trending(top_n=1)
        if trending_projects:
            project = trending_projects[0]
            analysis = analyze_project_with_gemini(project)
            
            final_report += f"#### 🚀 {project['name']} (⭐ {project['stars']})\n"
            final_report += f"**项目链接**：[{project['url']}]({project['url']})\n\n"
            final_report += analysis
        else:
            final_report += "今日未能获取到热门开源项目。\n"

        # 3. 推送整合后的报告
        push_to_wechat(pushplus_token, "今日AI前沿速报 (文章+项目)", final_report)














