import os
import time
import traceback
import urllib.parse
import urllib.request
import requests
import feedparser  # <--- 新增依赖
from bs4 import BeautifulSoup
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 模块一：获取文章列表 (升级为 RSS 方案 - 极度稳定) ---
def fetch_jqzj_articles(max_articles=3):
    print(f"🚀 启动 RSS 订阅获取策略...")
    articles_found = []

    # 定义高质量 AI RSS 源列表
    # 1. InfoQ AI (深度技术)
    # 2. 36Kr AI (行业资讯) - 使用 RSSHub 镜像或直接解析 XML
    # 为了演示最稳定性，这里使用 InfoQ 和 机器之心的 RSS (如果有)
    # 这里我们使用一个聚合策略
    rss_sources = [
        {
            "name": "InfoQ AI",
            "url": "https://www.infoq.cn/feed/topic/ai"
        },
        {
            # 这是一个非常通用的 AI 新闻 RSS 源
            "name": "OSChina AI",
            "url": "https://www.oschina.net/news/rss?show=news"
        }
    ]

    for source in rss_sources:
        if len(articles_found) >= max_articles:
            break
            
        print(f"📡 正在拉取源: {source['name']}...")
        try:
            # 使用 feedparser 解析
            feed = feedparser.parse(source['url'])
            
            # 检查是否有内容
            if not feed.entries:
                print(f"⚠️ {source['name']} 未返回内容，尝试下一个...")
                continue
                
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                
                # 简单的关键词过滤，确保是 AI 相关的 (针对通用源)
                # 如果是垂直源(如InfoQ AI)则不需要太严格
                keywords = ['AI', '模型', '深度学习', 'GPT', 'LLM', '开源', '算法', '智能', 'DeepSeek', 'Gemini']
                is_relevant = False
                
                if source['name'] == "InfoQ AI":
                    is_relevant = True # 专栏本身就是 AI
                else:
                    # 检查标题是否包含关键词
                    if any(k.lower() in title.lower() for k in keywords):
                        is_relevant = True
                
                if is_relevant:
                    # 去重
                    if not any(d['url'] == link for d in articles_found):
                        print(f"   Found: {title}")
                        articles_found.append({'title': title, 'url': link})
                
                if len(articles_found) >= max_articles:
                    break
                    
        except Exception as e:
            print(f"❌ 拉取 {source['name']} 失败: {e}")

    print(f"✅ 总共获取到 {len(articles_found)} 篇 AI 文章。")
    return articles_found

# --- 模块二：获取文章正文 (优化版) ---
def get_article_content(url):
    print(f"正在使用Selenium加载文章页面: {url}...")
    
    # 配置 Selenium - 增加防检测参数
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # 伪装 User-Agent，防止被拦截
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # 设置页面加载超时，防止卡死
        driver.set_page_load_timeout(30)
        driver.get(url)
        
        # 智能等待正文出现
        wait = WebDriverWait(driver, 10)
        
        # InfoQ 的正文 class 通常是 'article-content' 或 'infoq-article'
        # OSChina 的正文通常是 'editor-viewer'
        # 我们尝试获取 body 标签下的主要文本，或者使用通用选择器
        try:
            # 尝试通过通用标签 p 获取文本，这比找特定 class 更通用
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            # 过滤掉太短的段落（导航栏等）
            text_content = "\n".join([p.text for p in paragraphs if len(p.text) > 10])
            
            # 如果抓到的内容太少，尝试抓取 body
            if len(text_content) < 200:
                text_content = driver.find_element(By.TAG_NAME, "body").text
                
        except:
            # 兜底：直接获取 body 文本
            text_content = driver.find_element(By.TAG_NAME, "body").text

        print(f"成功提取文本，长度: {len(text_content)} 字符")
        return text_content
        
    except Exception as e:
        print(f"错误：使用Selenium获取正文失败 - {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- 模块三：Gemini总结 (保持不变) ---
def summarize_with_gemini(title: str, content: str) -> str:
    if not content or len(content) < 100:
        print(f"因'{title}'文章内容为空或过短，跳过Gemini总结。")
        return f"**⚠️ 无法读取文章内容，可能是链接受到访问限制。**\n🔗 [点击直接阅读原文]({title})" # 这里的title应该是url，稍后在主逻辑修正
        
    print(f"正在使用Gemini为学生视角总结文章: {title}")
    try:
        # Use a stable version of Gemini for article summarization
        model_name = 'gemini-3.1-flash-image-preview' 
        model = genai.GenerativeModel(model_name)

        prompt = f"""
        作为一名优秀的AI技术研究者，请为一名人工智能专业大二学生解读这篇文章。
        文章标题：{title}
        
        请严格按照以下Markdown格式输出：
        ### 📚 核心摘要
        （一句话概括核心观点）
        ### 💡 关键技术/观点
        - **点一**：(解释技术原理或核心事件)
        - **点二**：(解释)
        ### 👨‍💻 对学生的价值
        - **知识关联**：(关联到机器学习、神经网络等具体课程知识)
        - **实践建议**：(如何动手尝试)
        ---
        文章内容片段：
        {content[:10000]} 
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"错误：调用Gemini API总结文章失败 - {e}")
        traceback.print_exc()
        return f"**对文章 '{title}' 的总结失败：API调用出错。**"

# --- 模块四：推送 (保持不变) ---
def push_to_wechat(token: str, title: str, content: str):
    print("正在使用 PushPlus 推送到微信...")
    url = "http://www.pushplus.plus/send"
    # 截断过长的内容防止推送失败
    if len(content) > 10000:
        content = content[:10000] + "\n\n(内容过长已截断...)"
        
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

# --- 模块五：GitHub Trending (保持不变) ---
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
            
            p_tag = repo.find('p', class_='col-9 color-fg-muted my-1 pr-4')
            repo_description = p_tag.get_text(strip=True) if p_tag else "暂无描述。"
            
            # 修复星星抓取，有时候结构会变
            star_link = repo.find('a', href=f"{repo_relative_url}/stargazers")
            repo_stars = star_link.get_text(strip=True) if star_link else "N/A"
            
            trending_repos.append({'name': repo_name, 'url': repo_url, 'description': repo_description, 'stars': repo_stars})
        print(f"成功抓取到 {len(trending_repos)} 个热门项目。")
        return trending_repos
    except Exception as e:
        print(f"错误：抓取 GitHub Trending 失败 - {e}")
        return []

# --- 模块六：Gemini 分析项目 (保持不变) ---
def analyze_project_with_gemini(project_data: dict) -> str:
    print(f"正在使用 Gemini 分析开源项目: {project_data['name']}")
    try:
        model_name = 'gemini-1.5-flash' # 修正版本号为有效模型
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        请为一名AI专业的大学生，深入解读这个GitHub热门项目。
        项目：{project_data['name']}
        描述：{project_data['description']}
        链接：{project_data['url']}
        
        Markdown格式输出：
        ### 🌟 项目速览
        (一句话介绍)
        ### 💡 核心价值
        (解决了什么痛点)
        ### 🛠️ 技术栈
        (关键技术/库)
        ### 📖 大二学生学习指南
        - **入门**：(如何开始)
        - **进阶**：(学习重点)
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"错误：调用 Gemini 分析项目失败 - {e}")
        traceback.print_exc()
        return f"**对项目 '{project_data['name']}' 的分析失败。**"

# --- 模块七：获取并分析 Arxiv 论文 ---
def fetch_arxiv_papers(max_papers=3):
    print("🚀 启动 Arxiv 最新前沿论文搜索 (聚焦 GUI-Agent & 具身智能)...")
    
    # 关键词构建：GUI agent, vision language navigation, embodied AI等
    search_query = 'all:"GUI agent" OR all:"embodied AI" OR all:"vision-language navigation"'
    # URL 编码
    search_query = urllib.parse.quote(search_query)
    
    url = f'http://export.arxiv.org/api/query?search_query={search_query}&start=0&max_results={max_papers}&sortBy=submittedDate&sortOrder=descending'
    
    papers = []
    try:
        response = urllib.request.urlopen(url)
        feed = feedparser.parse(response)
        
        for entry in feed.entries:
            paper_info = {
                'title': entry.title,
                'url': entry.id,
                'summary': entry.summary,
                'authors': [author.name for author in entry.authors]
            }
            papers.append(paper_info)
            print(f"   Found Paper: {paper_info['title']}")
            
    except Exception as e:
        print(f"❌ 拉取 Arxiv 失败: {e}")
        traceback.print_exc()
        
    print(f"✅ 总共获取到 {len(papers)} 篇最新相关论文。")
    return papers

def analyze_paper_with_gemini(paper_data: dict) -> str:
    print(f"正在使用 Gemini 分析论文: {paper_data['title']}")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        作为一名AI专业的研究人员，请深入浅出地解读这篇最新论文的摘要，提取其核心贡献。
        论文标题：{paper_data['title']}
        作者：{', '.join(paper_data['authors'])}
        摘要内容：{paper_data['summary']}
        
        请严格按照以下Markdown格式输出：
        ### 🎯 核心解决的问题
        (一句话概括)
        ### 🔬 创新点/方法
        - **点一**：(...)
        - **点二**：(...)
        ### 🚀 对研究的启发
        (这篇论文对 GUI-Agent 或 具身智能方向有什么启发价值)
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"错误：调用 Gemini 分析论文失败 - {e}")
        traceback.print_exc()
        return f"**对论文 '{paper_data['title']}' 的分析失败。**"

# --- 主执行函数 ---
if __name__ == "__main__":
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN")

    if not gemini_api_key or not pushplus_token:
        print("❌ 错误：环境变量 GEMINI_API_KEY 或 PUSHPLUS_TOKEN 未设置")
        # 本地测试时可以临时在这里写死 key，但不要提交到 github
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            print("✅ Gemini API 配置成功。")
        except Exception as e:
            print(f"错误：配置 Gemini API 失败 - {e}")
            exit()

        final_report = "# 🚀 每日 AI 前沿速报\n\n"
        final_report += f"📅 {time.strftime('%Y-%m-%d')}\n\n"
        
        # --- Part 1: 文章 ---
        final_report += "## 📰 精选技术文章\n"
        articles = fetch_jqzj_articles(max_articles=2) # 建议先抓2篇，防止超时
        
        if articles:
            for index, article in enumerate(articles):
                print(f"--- 处理文章 {index+1}: {article['title']} ---")
                content = get_article_content(article['url'])
                
                # 如果正文获取失败，content 为 None，Gemini 函数会处理
                summary = summarize_with_gemini(article['title'], content)
                
                final_report += f"### {index+1}. {article['title']}\n"
                final_report += f"🔗 [阅读原文]({article['url']})\n\n"
                final_report += summary + "\n\n"
        else:
            final_report += "今日 RSS 源暂无更新或抓取受限。\n\n"

        final_report += "---\n\n"

        # --- Part 2: 项目 ---
        final_report += "## 💻 GitHub 热门 Python 项目\n"
        trending_projects = fetch_github_trending(top_n=1)
        if trending_projects:
            project = trending_projects[0]
            analysis = analyze_project_with_gemini(project)
            
            final_report += f"### 🚀 {project['name']} (⭐ {project['stars']})\n"
            final_report += f"🔗 [项目地址]({project['url']})\n\n"
            final_report += analysis + "\n\n"
        else:
            final_report += "今日未能获取到热门项目。\n\n"

        final_report += "---\n\n"

        # --- Part 3: Arxiv 前沿论文 (GUI Agent & 具身智能) ---
        final_report += "## 🎓 最新前沿学术论文\n"
        arxiv_papers = fetch_arxiv_papers(max_papers=2)
        if arxiv_papers:
            for index, paper in enumerate(arxiv_papers):
                print(f"--- 处理论文 {index+1}: {paper['title']} ---")
                
                analysis = analyze_paper_with_gemini(paper)
                
                final_report += f"### {index+1}. {paper['title']}\n"
                final_report += f"👨‍🔬 **作者**: {', '.join(paper['authors'])}\n"
                final_report += f"🔗 [Arxiv 链接]({paper['url']})\n\n"
                final_report += analysis + "\n\n"
        else:
            final_report += "今日最新前沿论文暂无更新。\n\n"

        # --- 推送 ---
        push_to_wechat(pushplus_token, "今日AI速报 (含Arxiv学术版)", final_report)


















