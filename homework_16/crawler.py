import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Получение страницы с таймаутом
async def fetch_page(url, session):
    try:
        async with session.get(url, timeout=30) as response:  # Таймаут 30 секунд
            return await response.text()
    except asyncio.TimeoutError:
        print(f"Request to {url} timed out.")
    except aiohttp.ClientConnectorError:
        print(f"Cannot connect to {url}.")
    return None

# Получаем новости с главной страницы
async def parse_news(session, seen_articles, file):
    url = "https://news.ycombinator.com/"
    page = await fetch_page(url, session)
    if page is None:
        return  # Выход, если не удается загрузить страницу
    soup = BeautifulSoup(page, "html.parser")

    # Поиск всех <a> внутри <span class="titleline">
    links = soup.select("span.titleline a")[:30]  # Берём только первые 30 новостей

    file.write(f"Found {len(links)} links.\n")
    print(f"Found {len(links)} links.")  # Отладочный вывод в терминал

    for link in links:
        title = link.text
        href = urljoin(url, link["href"])  # Формируем полный URL новости

        if href not in seen_articles:
            seen_articles.add(href)
            await parse_article(href, session, file, title)

# Скачивание страницы новости и комментариев
async def parse_article(url, session, file, title):
    page = await fetch_page(url, session)
    if page is None:
        return  # Выход, если не удается загрузить страницу
    soup = BeautifulSoup(page, "html.parser")

    # Записываем основную статью в файл
    file.write(f"\nTitle: {title}\nURL: {url}\n")
    file.write("Article content:\n")
    file.write(str(soup))  # Записываем содержимое статьи в файл

    # Находим комментарии
    comments = soup.find_all("a", class_="comment-link")
    for comment in comments:
        comment_url = urljoin(url, comment["href"])  # Полный URL комментария
        file.write(f"Comment URL: {comment_url}\n")
        await fetch_comment_page(comment_url, session, file)  # Скачиваем комментарий

# Скачивание страницы комментария
async def fetch_comment_page(comment_url, session, file):
    page = await fetch_page(comment_url, session)
    if page is None:
        return  # Выход, если не удается загрузить страницу
    soup = BeautifulSoup(page, "html.parser")

    # Сохраняем комментарий в файл
    file.write("Comment content:\n")
    file.write(str(soup))  # Записываем содержимое комментариев в файл

# Основной цикл, обрабатывающий новости
async def main():
    seen_articles = set()  # Множество для отслеживания уже посещенных новостей

    # Открываем файл для записи
    with open("output.txt", "w", encoding="utf-8") as file:
        async with aiohttp.ClientSession() as session:
            while True:
                await parse_news(session, seen_articles, file)
                print("Cycle complete. Waiting for the next cycle...")
                await asyncio.sleep(60)  # Ожидание N секунд перед следующей итерацией

if __name__ == "__main__":
    asyncio.run(main())    