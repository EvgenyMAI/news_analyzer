import httpx
import asyncio
import feedparser
import re
import os
import hashlib
from collections import deque
from newspaper import Article



def load_companies(file_path, encoding='utf-8'):
    with open(file_path, "r", encoding=encoding) as file:
        companies = file.read().splitlines()
    return companies


def find_russian_companies(text, companies_file):

    companies = load_companies(companies_file)

    pattern = r'[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*'
    matches = re.findall(pattern, text)

    relevant_companies = [match for match in matches if match in companies]

    return relevant_companies

async def fetch_article(httpx_client, url):
    try:
        response = await httpx_client.get(url)
        response.raise_for_status()
        article = Article(url)
        article.download()
        article.parse()

        # Получаем текст статьи
        article_text = article.text

        # Разбиваем текст на предложения
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', article_text)

        # Оставляем только первое предложение и удаляем абзацы
        first_sentence = sentences[0]
        remaining_text = ' '.join(sentences[1:]) if len(sentences) > 1 else ''

        # Склеиваем первое предложение и оставшуюся часть текста
        article_text_processed = f"{first_sentence}. {remaining_text}"

        return article_text_processed
    except Exception as e:
        print(f"Error fetching article: {e}")
        return ''

async def rss_parser(httpx_client, posted_q, output_dir, rss_links, companies_file):
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

                news_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
                if news_hash in posted_q:
                    continue

                filename = f"{news_hash}.txt"
                filepath = os.path.join(output_dir, filename)
                print(f"\nSaving news: {title}\nlink: {link}")

                with open(filepath, "w", encoding='utf-8') as file:
                    file.write(news_text)

                companies = find_russian_companies(news_text, companies_file)
                if companies:
                    company_count = {company: companies.count(company) for company in set(companies)}
                    with open(os.path.join(output_dir, f"{news_hash}_companies.txt"), "w", encoding='utf-8') as file:
                        for company, count in company_count.items():
                            file.write(f"{company}: {count}\n")

                posted_q.appendleft(news_hash)

if __name__ == "__main__":
    rss_links = [
        # "https://ru.investing.com/rss/news_301.rss",
        # "https://ru.investing.com/rss/stock_Technical.rss",
        # "https://ru.investing.com/rss/stock_Fundamental.rss",
        "https://ru.investing.com/rss/stock_Indices.rss",
        "https://ru.investing.com/rss/stock_Stocks.rss",
        "https://ru.investing.com/rss/bonds_Government.rss",
        "https://ru.investing.com/rss/bonds_Corporate.rss",
        "https://ru.investing.com/rss/news_301.rss"
    ]

    posted_q = deque(maxlen=60)

    output_dir = "news"

    companies_file = "companies.txt"


    httpx_client = httpx.AsyncClient()
    asyncio.run(rss_parser(httpx_client, posted_q, output_dir, rss_links, companies_file))
