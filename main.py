import os
import time
import urllib.parse
import urllib.request
import requests
import feedparser
import traceback
from bs4 import BeautifulSoup
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 模块一：获取文章列表 (RSS 方案) ---
def fetch_jqzj_articles(max_articles=2):
    print(f"🚀 启动 RSS 订阅获取策略...")
    articles_found = []
    rss_sources = [
        {"name": "InfoQ AI", "url": "https://www.infoq.cn/feed/topic/ai"},
        {"name": "OSChina AI", "url": "https://www.oschina.net/news/rss?show=news"}
    ]

    for source in rss_sources:
        if len(articles_found) >= max_articles: break
        print(f"📡 正在拉取源: {source['name']}...")
        try:
            feed = feedparser.parse(source['url'])
            if not feed.entries: continue
                
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                keywords = ['AI', '模型', '深度学习', 'GPT', 'LLM', '开源', '算法', '智能', 'Agent', '具身']
                
                is_relevant = source['name'] == "InfoQ AI" or any(k.lower() in title.lower() for k in keywords)
                if is_relevant and not any(d['url'] == link for d in articles_found):
                    print(f"   Found: {title}")
                    articles_found.append({'title': title, 'url': link})
                if len(articles_found) >= max_articles: break
        except Exception as e:
            print(f"❌ 拉取 {source['name']} 失败: {e}")
    return articles_found

# --- 模块二：获取文章正文 ---
def get_article_content(url):
    print(f"正在使用Selenium加载文章页面: {url}...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        driver.get(url)
        WebDriverWait(driver, 5) # 极简等待
        
        try:
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            text_content = "\n".join([p.text for p in paragraphs if len(p.text) > 10])
            if len(text_content) < 200:
                text_content = driver.find_element(By.TAG_NAME, "body").text
        except:
            text_content = driver.find_element(By.TAG_NAME, "body").text
        return text_content
    except Exception as e:
        print(f"错误：获取正文失败 - {e}")
        return None
    finally:
        if driver: driver.quit()

# --- 模块三：Gemini 新闻深度分析 (动态科普机制) ---
def summarize_with_gemini(title: str, content: str) -> str:
    if not content or len(content) < 100: return f"**⚠️ 内容过短或受限**\n🔗 [手动阅读]({title})"
        
    print(f"🧠 [文章分析] 进行前沿动向提取与自动扫盲判别: {title}")
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f"""
        作为一名资深AI算法高级研究员，请重点提取这篇技术文章的研究方向与机制创新。
        文章标题：{title}
        
        工作判定逻辑：该用户主攻【GUI Agent】、【情感计算(RepE表征工程)】、【大语言模型智能体】和【具身智能】。
        
        请严格按照以下Markdown格式输出：
        ### 📚 核心进展与前沿动向
        (一句话概括这篇文章中最核心的推进点)
        ### 💡 核心机制剖析
        - **关键机制一**：(...)
        - **关键机制二**：(...)
        
        ### 🧠 通俗原理解释 (自适应模块)
        *(执行指令：仅当该文章**不属于**上述四大主攻领域时，生成此模块。用生动形象的大白话、打比方来解释文章里的核心概念或生僻术语，确保跨领域的同学也能瞬间抓到本质。如果文章属于主攻领域范围内，则**直接不要输出**该标题和内容！)*
        ---
        正文：
        {content[:8000]} 
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**总结失败：** {e}"

# --- 模块四：GitHub Trending (周期拉长至 Weekly 过滤杂质) ---
def fetch_github_trending(top_n=1):
    print(f"开始抓取 GitHub Trending (Weekly) 沉淀项目...")
    # 改为每周热门，更能筛出有含金量的基座级项目
    url = "https://github.com/trending/python?since=weekly" 
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        repo_list = soup.find_all('article', class_='Box-row')
        trending_repos = []
        for repo in repo_list[:top_n]:
            a_tag = repo.find('h2', class_='h3 lh-condensed').find('a')
            repo_name = a_tag.get_text(strip=True).replace(" / ", "/")
            repo_url = f"https://github.com{a_tag['href']}"
            p_tag = repo.find('p', class_='col-9 color-fg-muted my-1 pr-4')
            desc = p_tag.get_text(strip=True) if p_tag else "N/A"
            stars = repo.find('a', href=f"{a_tag['href']}/stargazers").get_text(strip=True)
            trending_repos.append({'name': repo_name, 'url': repo_url, 'description': desc, 'stars': stars})
        return trending_repos
    except Exception as e:
        return []

def analyze_project_with_gemini(project_data: dict) -> str:
    print(f"🧠 [GitHub评估] 实战价值评估: {project_data['name']}")
    try:
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        prompt = f"""
        作为AI科研导师，严格评估这个本周高Star项目对一线AI研究者的【实战价值】。
        项目：{project_data['name']}
        描述：{project_data['description']}
        
        Markdown格式：
        ### 🌟 项目速览
        (一句话讲清楚它到底是个啥)
        ### 🛠️ 解决的痛点与底层引擎
        (它到底依靠什么技术起家的？解决了什么确切痛点？)
        ### 🚀 科研实用价值终判
        (客观评价：它只是个简单的API套壳玩具，还是个极其好用的代码基座？能否作为后续研究的Baseline，或者直接为你剥离出一个好用的数据处理/评估工具？如有需要拔草避坑的请直言不讳)
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**项目评估失败：** {e}"

# --- 模块五：ArXiv 论文 (智能优先过滤机制) ---
def fetch_arxiv_papers(target_count=3):
    print("🚀 启动 ArXiv 广域检索与本地排序引擎...")
    # 扩大检索词面，后续做本地细筛
    query = 'all:"GUI Agent" OR all:"UI Agent" OR all:"affective computing" OR all:"representation engineering" OR all:"autonomous agent" OR all:"embodied AI"'
    query_url = f'http://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&start=0&max_results=15&sortBy=submittedDate&sortOrder=descending'
    
    papers = []
    try:
        response = urllib.request.urlopen(query_url)
        feed = feedparser.parse(response)
        
        # 核心加权逻辑(匹配你的顶级优先级)
        for entry in feed.entries:
            text = (entry.title + " " + entry.summary).lower()
            score = 0
            # Tier 1: GUI, Agent, Emotion/RepE
            if any(k in text for k in ['gui', 'ui agent', 'web agent']): score += 100
            if any(k in text for k in ['emotion', 'affective', 'representation engineering', 'concept erasure']): score += 100
            if any(k in text for k in ['autonomous agent', 'llm agent', 'agent architecture']): score += 90
            # Tier 2: 具备智能与其他
            if any(k in text for k in ['embodied', 'robotics']): score += 70
            
            papers.append({
                'title': entry.title,
                'url': entry.id,
                'summary': entry.summary,
                'authors': [a.name for a in entry.authors],
                'score': score
            })
            
        # 根据含金量相关词语优先级排序，取头部 target_count 篇
        papers.sort(key=lambda x: x['score'], reverse=True)
        final_papers = papers[:target_count]
        print(f"✅ 从池中过滤出 {len(final_papers)} 篇与主攻方向极度吻合的论文。")
        return final_papers
        
    except Exception as e:
        print(f"❌ ArXiv 拉取失败: {e}")
        return []

def analyze_paper_with_gemini(paper_data: dict) -> str:
    print(f"🧠 [论文透视] 调用 expert 与 generator 重组论文: {paper_data['title']}")
    try:
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        prompt = f"""
        你现在是我的顶尖 AI 科研导师，体内已激活 `expert-paper-reader` 与 `research-idea-generator` 技能。
        我的算力有限(贫民窟级别)，重点研究领域为：【GUI-Agent】【情感计算(RepE机制)】和【具身大模型】。
        请化身“严苛审稿人”加上“Idea缝合怪”，将这篇论文解剖重构：
        
        论文核心信息：
        标题：{paper_data['title']}
        摘要：{paper_data['summary']}
        
        必须按下面骨架输出你的洞见：
        ### 🎯 痛点与核心机制 (SOTA对比)
        (穿透表象，一句话讲明它解决了哪个卡脖子问题？相比前人 Baseline 改了哪层架构？)
        ### ⚖️ 含金量与微观批评 (Critic)
        (严格评估：这篇工作是重大的范式突破，还是纯工程化的拼凑缝合？对于我们在贫民窟算力下能复现的概率有多少？是否潜藏着设限局限？)
        ### 🧩 析出“模块卡片” (Knowledge Extract)
        (榨干它的价值！提取出全文最硬核的1个无需大算力的独立创新 trick 或组件，定义为一块“模块积木”，简述此模块的输入输出原理)
        ### 💡 跨界Idea缝合驱动 (Failure-Driven Innovation)
        (必须执行跨界迁移尝试！将你刚析出的这块积木，强制与我的方向如“GUI Agent产生幻觉时的状态反思机制”或“RepE在极少样本下的内部干预控制”融合，头脑风暴出一个轻量级、有可能发顶会的具体可落地的实验Idea！)
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**论文评审失败：** {e}"

# --- 模块六：微信推送 ---
def push_to_wechat(token: str, title: str, content: str):
    print("正在推送到微信...")
    url = "http://www.pushplus.plus/send"
    if len(content) > 15000:
         content = content[:15000] + "\n\n(正文受到平台字数限制已被截断)"
    data = {"token": token, "title": title, "content": content, "template": "markdown"}
    try:
        res = requests.post(url, json=data)
        if res.json().get("code") == 200: print("✅ 推送成功！")
        else: print(f"❌ 推送驳回: {res.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

# --- 主执行链路 ---
if __name__ == "__main__":
    gemini_key = os.environ.get("GEMINI_API_KEY")
    push_token = os.environ.get("PUSHPLUS_TOKEN")

    if not gemini_key or not push_token:
        print("❌ 环境变量 GEMINI_API_KEY 或 PUSHPLUS_TOKEN 未配置")
    else:
        genai.configure(api_key=gemini_key)
        
        report = f"# 🚀 科研工作流 每日简报\n📅 {time.strftime('%Y-%m-%d')}\n\n"
        
        report += "## 🎓 顶会级前沿论文解析 (核心区)\n"
        papers = fetch_arxiv_papers(target_count=3)  # 固定抓取前3名高权重论文
        if papers:
            for idx, p in enumerate(papers):
                res = analyze_paper_with_gemini(p)
                report += f"### {idx+1}. {p['title']}\n"
                report += f"👨‍🔬 作者: {', '.join(p['authors'][:3])}等 | 🔗 [PDF原文]({p['url']})\n\n"
                report += res + "\n\n---\n\n"
                
        report += "## 📰 行业前沿文章扫描\n"
        articles = fetch_jqzj_articles(max_articles=2)
        if articles:
            for idx, art in enumerate(articles):
                content = get_article_content(art['url'])
                res = summarize_with_gemini(art['title'], content)
                report += f"### {idx+1}. {art['title']}\n🔗 [原文]({art['url']})\n\n{res}\n\n"
                
        report += "---\n\n## 💻 GitHub AI 高价值基座 (Weekly)\n"
        repos = fetch_github_trending(top_n=1)
        if repos:
            repo = repos[0]
            res = analyze_project_with_gemini(repo)
            report += f"### 🚀 {repo['name']} (⭐ {repo['stars']})\n🔗 [仓库地址]({repo['url']})\n\n{res}\n"

        push_to_wechat(push_token, f"🔔 核心研报: {time.strftime('%m-%d')} 前沿与Idea生成", report)




















