import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import logging
import argparse
import matplotlib.pyplot as plt
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, init
from datetime import datetime
import time

# =====================================
# INIT
# =====================================
init(autoreset=True)

# =====================================
# LOGGING
# =====================================
logging.basicConfig(
    filename="news_aggregator.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =====================================
# DATABASE
# =====================================
conn = sqlite3.connect("news.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    source TEXT,
    url TEXT,
    timestamp TEXT
)
""")

conn.commit()

# =====================================
# SOURCES
# =====================================
SOURCES = {
    "HackerNews": "https://news.ycombinator.com/",
    "BBC": "https://www.bbc.com/news",
    "TechCrunch": "https://techcrunch.com/"
}

# =====================================
# FETCH PAGE
# =====================================
def fetch_page(url):

    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        return response.text

    except Exception as e:

        logging.error(str(e))

        return None

# =====================================
# SAVE NEWS
# =====================================
def save_news(title, source, url):

    cursor.execute("""
    INSERT INTO news(title, source, url, timestamp)
    VALUES (?, ?, ?, ?)
    """, (
        title,
        source,
        url,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()

# =====================================
# SCRAPE HN
# =====================================
def scrape_hackernews():

    html = fetch_page(
        SOURCES["HackerNews"]
    )

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    headlines = []

    for item in soup.select(".titleline a"):

        title = item.text.strip()

        link = item.get("href")
        
        if "from?site=" in str(link):
            continue

        headlines.append({
            "title": title,
            "source": "HackerNews",
            "url": link
        })

    return headlines

# =====================================
# SCRAPE BBC
# =====================================
def scrape_bbc():

    html = fetch_page(
        SOURCES["BBC"]
    )

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    headlines = []

    for item in soup.select("h2"):

        title = item.text.strip()

        if len(title) < 20:
            continue

        headlines.append({
            "title": title,
            "source": "BBC",
            "url": SOURCES["BBC"]
        })

    return headlines

# =====================================
# SCRAPE TECHCRUNCH
# =====================================
def scrape_techcrunch():

    html = fetch_page(
        SOURCES["TechCrunch"]
    )

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    headlines = []

    for item in soup.select("h3"):

        title = item.text.strip()

        if len(title) < 20:
            continue

        headlines.append({
            "title": title,
            "source": "TechCrunch",
            "url": SOURCES["TechCrunch"]
        })

    return headlines

# =====================================
# AGGREGATE
# =====================================
def aggregate_news():

    print(
        Fore.BLUE +
        "\n🌐 NEWS AGGREGATOR ULTRA X\n"
    )

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        results = list(executor.map(
            lambda func: func(),
            [
                scrape_hackernews,
                scrape_bbc,
                scrape_techcrunch
            ]
        ))

    all_news = []

    for result in results:
        all_news.extend(result)

    unique_titles = set()

    cleaned_news = []

    for news in all_news:

        if news["title"] not in unique_titles:

            unique_titles.add(
                news["title"]
            )

            cleaned_news.append(news)

            save_news(
                news["title"],
                news["source"],
                news["url"]
            )

    return cleaned_news

# =====================================
# DISPLAY
# =====================================
def display_news(news_data):

    for i, news in enumerate(
        news_data[:20],
        start=1
    ):

        print(
            Fore.GREEN +
            f"{i}. {news['title']}"
        )

        print(
            Fore.YELLOW +
            news["url"]
        )

        print(
            Fore.CYAN +
            news["source"]
        )

        print("-" * 60)

# =====================================
# EXPORT CSV
# =====================================
def export_csv():

    df = pd.read_sql_query(
        "SELECT * FROM news",
        conn
    )

    df.to_csv(
        "news_report.csv",
        index=False
    )

    print(
        Fore.GREEN +
        "\n✔ Exported CSV"
    )

# =====================================
# EXPORT EXCEL
# =====================================
def export_excel():

    df = pd.read_sql_query(
        "SELECT * FROM news",
        conn
    )

    df.to_excel(
        "news_report.xlsx",
        index=False
    )

    print(
        Fore.GREEN +
        "\n✔ Exported Excel"
    )

# =====================================
# EXPORT JSON
# =====================================
def export_json():

    df = pd.read_sql_query(
        "SELECT * FROM news",
        conn
    )

    df.to_json(
        "news_report.json",
        orient="records",
        indent=4
    )

    print(
        Fore.GREEN +
        "\n✔ Exported JSON"
    )

# =====================================
# ANALYTICS
# =====================================
def analytics():

    df = pd.read_sql_query(
        "SELECT * FROM news",
        conn
    )

    print(
        Fore.MAGENTA +
        "\n===== NEWS ANALYTICS ====="
    )

    print(
        f"Total Headlines : {len(df)}"
    )

    print(
        "\nSource Distribution:"
    )

    print(
        df["source"].value_counts()
    )

# =====================================
# WORD CLOUD ANALYTICS
# =====================================
def word_frequency():

    df = pd.read_sql_query(
        "SELECT * FROM news",
        conn
    )

    words = []

    for title in df["title"]:

        words.extend(
            title.lower().split()
        )

    common = Counter(words).most_common(10)

    labels = [x[0] for x in common]
    values = [x[1] for x in common]

    plt.figure(figsize=(8, 6))

    plt.bar(labels, values)

    plt.title("Trending Keywords")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        "keyword_trends.png"
    )

    print(
        Fore.GREEN +
        "\n📊 Keyword Trends Saved"
    )

# =====================================
# SEARCH
# =====================================
def search_news(keyword):

    df = pd.read_sql_query(
        "SELECT * FROM news",
        conn
    )

    results = df[
        df["title"].str.contains(
            keyword,
            case=False
        )
    ]

    print(
        Fore.CYAN +
        "\n===== SEARCH RESULTS =====\n"
    )

    print(results)

# =====================================
# MAIN
# =====================================
def main():

    parser = argparse.ArgumentParser(
        description="News Aggregator Ultra X"
    )

    parser.add_argument(
        "--export",
        action="store_true"
    )

    parser.add_argument(
        "--excel",
        action="store_true"
    )

    parser.add_argument(
        "--json",
        action="store_true"
    )

    parser.add_argument(
        "--analytics",
        action="store_true"
    )

    parser.add_argument(
        "--trends",
        action="store_true"
    )

    parser.add_argument(
        "--search"
    )

    args = parser.parse_args()

    news_data = aggregate_news()

    display_news(news_data)

    if args.export:
        export_csv()

    if args.excel:
        export_excel()

    if args.json:
        export_json()

    if args.analytics:
        analytics()

    if args.trends:
        word_frequency()

    if args.search:
        search_news(args.search)

# =====================================
# START
# =====================================
if __name__ == "__main__":
    main()
