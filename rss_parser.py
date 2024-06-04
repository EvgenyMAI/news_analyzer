import os
import httpx
import hashlib
import asyncio
import feedparser
from newspaper import Article


output_dir_for_news = "news"
mentions_file = "mentions.txt"
companies_file = "companies.txt"


def load_companies_from_file(companies_file):
    """Считывает список компаний из файла."""
    if not os.path.isfile(companies_file):
        print(f"Companies file {companies_file} not found.")
        return []

    with open(companies_file, "r", encoding='utf-8') as file:
        companies = [line.strip() for line in file if line.strip()]

    return companies


async def fetch_article(httpx_client, url):
    """Извлекает полный текст статьи по URL."""
    try:
        response = await httpx_client.get(url)
        response.raise_for_status()
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except httpx.RequestError as e:
        print(f"Request error fetching RSS feed: {e}")
        return ''
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching RSS feed: {e}")
        return ''
    except Exception as e:
        print(f"Unknown error fetching RSS feed: {e}")
        return ''


def update_mentions_file(company):
    """Обновляет файл с упоминаниями компаний."""
    mentions = {}

    # Чтение текущих упоминаний из файла
    if os.path.isfile(mentions_file):
        with open(mentions_file, "r", encoding='utf-8') as file:
            for line in file:
                name, count = line.strip().split(": ")
                mentions[name] = int(count)

    # Обновление счетчика упоминаний
    if company in mentions:
        mentions[company] += 1
    else:
        mentions[company] = 1

    # Запись обновленных упоминаний обратно в файл
    with open(mentions_file, "w", encoding='utf-8') as file:
        for name, count in mentions.items():
            file.write(f"{name}: {count}\n")


async def rss_parser(httpx_client, rss_links):
    """Парсит RSS-ленты и сохраняет новости"""
    os.makedirs(output_dir_for_news, exist_ok=True)
    companies = load_companies_from_file(companies_file)

    while True:
        print("Starting to parse RSS feeds")
        count_parced_news = 0
        for rss_link in rss_links:
            try:
                response = await httpx_client.get(rss_link)
                response.raise_for_status()
            except httpx.RequestError as e:
                print(f"Request error fetching RSS feed: {e}")
                continue
            except httpx.HTTPStatusError as e:
                print(f"HTTP error fetching RSS feed: {e}")
                continue
            except Exception as e:
                print(f"Unknown error fetching RSS feed: {e}")
                continue

            feed = feedparser.parse(response.text)

            for entry in feed.entries[::-1]:
                title = entry.get('title', 'No title')
                link = entry.get('link', '')

                if not link:
                    continue

                news_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
                if os.path.isfile(os.path.join(output_dir_for_news, f"{news_hash}.txt")):
                    continue

                full_text = await fetch_article(httpx_client, link)
                if not full_text:
                    continue

                news_text = f'{title}\n{full_text}'

                # Генерация уникального имени файла для спаршенной новости
                filename = f"{news_hash}.txt"
                filepath = os.path.join(output_dir_for_news, filename)
                with open(filepath, "w", encoding='utf-8') as file:
                    file.write(news_text)

                # Проверка на упоминание компаний
                for company in companies:
                    if company in news_text:
                        update_mentions_file(company)

                count_parced_news += 1
                print(f"\n{count_parced_news}. Saving news: {title}\nlink: {link}")

        # Пятиминутное ожидание перед следующим циклом
        print(f"\n{count_parced_news} news from sources have been parced. Waiting for 5 minutes before next parsing...")
        await asyncio.sleep(300)


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

    httpx_client = httpx.AsyncClient()
    asyncio.run(rss_parser(httpx_client, rss_links))
