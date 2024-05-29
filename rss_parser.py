import os
import httpx
import asyncio
import feedparser
from collections import deque
from newspaper import Article
import hashlib

async def fetch_article(httpx_client, url):
    """Fetch the full article text from the given URL."""
    try:
        response = await httpx_client.get(url)
        response.raise_for_status()
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error fetching article: {e}")
        return ''

async def rss_parser(httpx_client, posted_q, output_dir, rss_links):
    """RSS feed parser"""

    os.makedirs(output_dir, exist_ok=True)

    print("Starting to parse RSS feeds")
    while True:
        for rss_link in rss_links:
            try:
                response = await httpx_client.get(rss_link)
                response.raise_for_status()
            except Exception as e:
                print(f"Error fetching RSS feed: {e}")
                await asyncio.sleep(10)
                continue

            feed = feedparser.parse(response.text)

            for entry in feed.entries[::-1]:
                title = entry.get('title', 'No title')
                link = entry.get('link', '')

                if not link:
                    continue

                full_text = await fetch_article(httpx_client, link)
                if not full_text:
                    continue

                news_text = f'{title}\n{full_text}'

                # Проверка на дубликаты с помощью хеширования
                news_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
                if news_hash in posted_q:
                    continue

                # Генерация уникального имени файла
                filename = f"{news_hash}.txt"
                filepath = os.path.join(output_dir, filename)
                print(f"\nSaving news: {title}\nlink: {link}")

                # Сохранение в файл
                with open(filepath, "w", encoding='utf-8') as file:
                    file.write(news_text)

                posted_q.appendleft(news_hash)

        await asyncio.sleep(5)

if __name__ == "__main__":
    rss_links = [
        #"https://ru.investing.com/rss/news_301.rss",
        #"https://ru.investing.com/rss/stock_Technical.rss",
        #"https://ru.investing.com/rss/stock_Fundamental.rss",
        "https://ru.investing.com/rss/stock_Indices.rss",
        "https://ru.investing.com/rss/stock_Stocks.rss",
        "https://ru.investing.com/rss/bonds_Government.rss",
        "https://ru.investing.com/rss/bonds_Corporate.rss",
        "https://ru.investing.com/rss/news_301.rss"
    ]
    
    # Очередь из уже опубликованных постов, чтобы их не дублировать
    posted_q = deque(maxlen=60)

    output_dir = "news"

    httpx_client = httpx.AsyncClient()

    asyncio.run(rss_parser(httpx_client, posted_q, output_dir, rss_links))
