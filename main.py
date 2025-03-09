import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import random
import time
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
import argparse

# Импортируем библиотеки Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Загружаем переменные окружения из файла .env
load_dotenv()

# API ключи и идентификаторы
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Параметры для управления частотой запросов
THROTTLE_DELAY = 2.0  # задержка между запросами в секундах
LAST_REQUEST_TIME = 0  # время последнего запроса

# Проверка наличия необходимых API ключей
if not GOOGLE_API_KEY:
    raise ValueError("Не найден API ключ Gemini. Убедитесь, что он установлен в переменных окружения или файле .env.")
if not GOOGLE_CSE_API_KEY:
    raise ValueError(
        "Не найден API ключ Google Programmable Search Engine. Убедитесь, что он установлен в переменных окружения или файле .env.")
if not GOOGLE_CSE_ID:
    raise ValueError(
        "Не найден ID поисковой системы Google Programmable Search Engine. Убедитесь, что он установлен в переменных окружения или файле .env.")

# Настройка Gemini API
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

# Список User-Agent для рандомизации
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1'
]


def get_random_user_agent():
    """Возвращает случайный User-Agent из списка"""
    return random.choice(USER_AGENTS)


def log_message(message, log_type="info"):
    """Логирует сообщение в консоль с временной меткой"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{log_type.upper()}] {message}")


def throttle_request():
    """Ограничивает частоту запросов путем добавления задержки"""
    global LAST_REQUEST_TIME
    current_time = time.time()
    time_since_last_request = current_time - LAST_REQUEST_TIME

    if time_since_last_request < THROTTLE_DELAY:
        wait_time = THROTTLE_DELAY - time_since_last_request
        log_message(f"Задержка запроса на {wait_time:.2f} сек для предотвращения блокировки", "info")
        time.sleep(wait_time)

    LAST_REQUEST_TIME = time.time()


def create_webdriver():
    """Создает и настраивает экземпляр WebDriver для Selenium"""
    log_message("Инициализация WebDriver для браузера...")

    options = Options()
    options.add_argument("--headless")  # Запуск в фоновом режиме без GUI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={get_random_user_agent()}")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Скрываем автоматизацию
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7")
    options.add_argument("--window-size=1920,1080")  # Устанавливаем размер окна

    # Установка и использование Chrome через webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Устанавливаем таймаут для явного ожидания элементов
    driver.implicitly_wait(10)

    # Добавляем скрипт для дополнительной маскировки автоматизации
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    log_message("WebDriver успешно инициализирован")
    return driver


def search_relevant_urls_yandex_selenium(topic, num_results=5):
    """Поиск в Яндексе с использованием Selenium"""
    log_message(f"Поиск через Яндекс (Selenium) по запросу: '{topic}'")
    driver = None
    try:
        driver = create_webdriver()

        # Загружаем страницу поиска Яндекса
        url = f"https://yandex.ru/search/?text={requests.utils.quote(topic)}"
        log_message(f"Открытие URL: {url}")
        driver.get(url)

        # Ждем загрузки результатов поиска
        log_message("Ожидание загрузки результатов поиска...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".serp-item"))
        )

        # Добавляем случайную паузу для имитации пользователя
        time.sleep(random.uniform(1.0, 3.0))

        # Проверка на наличие капчи
        if "captcha" in driver.page_source.lower() or "капча" in driver.page_source.lower():
            log_message("Обнаружена капча на странице Яндекса. Сохранение скриншота...", "warning")
            driver.save_screenshot("yandex_captcha.png")
            log_message("Скриншот сохранен как 'yandex_captcha.png'", "warning")
            return []

        # Прокручиваем страницу для загрузки всех результатов
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # Сохраняем страницу для отладки
        with open("yandex_search_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log_message("Страница поиска сохранена в 'yandex_search_page.html' для анализа")

        # Извлекаем ссылки из результатов поиска
        # Яндекс использует атрибут href в элементе a внутри элемента .serp-item
        results = []
        search_results = driver.find_elements(By.CSS_SELECTOR, ".serp-item .organic__url")

        log_message(f"Найдено {len(search_results)} элементов-результатов поиска")

        for result in search_results:
            try:
                href = result.get_attribute("href")
                if href and not href.startswith("https://yandex.ru/") and not href.startswith("/"):
                    # Исключаем служебные ссылки Яндекса и рекламу
                    results.append(href)
                    log_message(f"Добавлен URL: {href}")
                    if len(results) >= num_results:
                        break
            except (StaleElementReferenceException, Exception) as e:
                log_message(f"Ошибка при извлечении ссылки: {e}", "warning")
                continue

        log_message(f"Найдено {len(results)} результатов в Яндексе")
        return results

    except TimeoutException:
        log_message("Таймаут при ожидании загрузки результатов поиска Яндекса", "error")
        if driver:
            driver.save_screenshot("yandex_timeout.png")
            log_message("Скриншот сохранен как 'yandex_timeout.png'", "warning")
        return []
    except Exception as e:
        log_message(f"Ошибка при выполнении поиска в Яндексе через Selenium: {e}", "error")
        if driver:
            driver.save_screenshot("yandex_error.png")
            log_message("Скриншот сохранен как 'yandex_error.png'", "warning")
        return []
    finally:
        if driver:
            driver.quit()
            log_message("WebDriver закрыт")


def search_relevant_urls_duckduckgo_selenium(topic, num_results=5):
    """
    Поиск в DuckDuckGo с использованием Selenium
    
    DuckDuckGo часто меняет структуру своей страницы и селекторы, что может вызывать проблемы.
    Эта функция использует несколько различных селекторов и стратегий для извлечения результатов.
    """
    log_message(f"Поиск через DuckDuckGo (Selenium) по запросу: '{topic}'")
    driver = None
    try:
        driver = create_webdriver()

        # Загружаем страницу поиска DuckDuckGo
        url = f"https://duckduckgo.com/?q={requests.utils.quote(topic)}&t=h_&ia=web"
        log_message(f"Открытие URL: {url}")
        driver.get(url)

        # Ждем загрузки результатов поиска с увеличенным таймаутом
        log_message("Ожидание загрузки результатов поиска...")
        
        # Пробуем разные селекторы, так как DuckDuckGo может менять их
        selectors = [
            ".result", 
            ".result__body", 
            ".react-results--main .result", 
            ".react-results--main a", 
            ".nrn-react-div"
        ]
        
        # Ждем появления хотя бы одного из селекторов
        for selector in selectors:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                log_message(f"Найден селектор: {selector}")
                break
            except TimeoutException:
                continue
        
        # Добавляем случайную паузу для имитации пользователя
        time.sleep(random.uniform(2.0, 4.0))
        
        # Прокручиваем страницу для загрузки всех результатов
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Сохраняем страницу для отладки
        with open("duckduckgo_search_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log_message("Страница поиска сохранена в 'duckduckgo_search_page.html' для анализа")

        # Извлекаем ссылки из результатов поиска, пробуя разные селекторы
        results = []
        
        # Список возможных селекторов для ссылок
        link_selectors = [
            ".result__a", 
            ".result__url", 
            ".result__snippet a",
            ".react-results--main .result a[href]",
            ".nrn-react-div a[href]",
            "article a[href]",
            "a[data-testid='result-title-a']"
        ]
        
        for selector in link_selectors:
            try:
                search_results = driver.find_elements(By.CSS_SELECTOR, selector)
                if search_results:
                    log_message(f"Найдено {len(search_results)} элементов по селектору {selector}")
                    break
            except Exception:
                continue
        
        # Если не нашли результаты по селекторам, попробуем найти все ссылки и отфильтровать
        if not search_results:
            log_message("Не удалось найти результаты по стандартным селекторам, ищем все ссылки", "warning")
            search_results = driver.find_elements(By.TAG_NAME, "a")

        log_message(f"Найдено {len(search_results)} элементов-результатов поиска")

        for result in search_results:
            try:
                href = result.get_attribute("href")
                # Фильтруем только внешние ссылки
                if (href and 
                    href.startswith("http") and 
                    not "duckduckgo.com" in href and 
                    not "duck.co" in href and
                    not "javascript:" in href):
                    results.append(href)
                    log_message(f"Добавлен URL: {href}")
                    if len(results) >= num_results:
                        break
            except (StaleElementReferenceException, Exception) as e:
                log_message(f"Ошибка при извлечении ссылки: {e}", "warning")
                continue

        # Удаляем дубликаты
        results = list(dict.fromkeys(results))
        
        log_message(f"Найдено {len(results)} уникальных результатов в DuckDuckGo")
        return results

    except TimeoutException:
        log_message("Таймаут при ожидании загрузки результатов поиска DuckDuckGo", "error")
        if driver:
            driver.save_screenshot("duckduckgo_timeout.png")
            log_message("Скриншот сохранен как 'duckduckgo_timeout.png'", "warning")
        return []
    except Exception as e:
        log_message(f"Ошибка при выполнении поиска в DuckDuckGo через Selenium: {e}", "error")
        if driver:
            driver.save_screenshot("duckduckgo_error.png")
            log_message("Скриншот сохранен как 'duckduckgo_error.png'", "warning")
        return []
    finally:
        if driver:
            driver.quit()
            log_message("WebDriver закрыт")


def search_relevant_urls_google(topic, api_key, cse_id, num_results=5):
    """Ищем URL-адреса в Google Programmable Search Engine."""
    try:
        log_message(f"Поиск через Google CSE по запросу: '{topic}'")
        throttle_request()
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=topic, cx=cse_id, num=num_results).execute()
        results = [item['link'] for item in res.get('items', [])]
        log_message(f"Найдено {len(results)} результатов в Google")
        return results
    except Exception as e:
        error_msg = f"Ошибка при выполнении поискового запроса к Google CSE: {e}"
        log_message(error_msg, "error")
        return []


def fetch_html_content_selenium(url):
    """Загрузка страницы и получение HTML-контента с помощью Selenium"""
    log_message(f"Загрузка страницы (Selenium): {url}")
    driver = None
    try:
        driver = create_webdriver()

        # Устанавливаем таймаут загрузки страницы
        driver.set_page_load_timeout(20)

        log_message(f"Открытие URL: {url}")
        driver.get(url)

        # Ждем, пока страница загрузится полностью
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Добавляем случайную паузу для имитации пользователя
        time.sleep(random.uniform(0.5, 2.0))

        # Прокручиваем страницу для загрузки ленивого контента
        driver.execute_script(
            "window.scrollTo(0, Math.floor(document.body.scrollHeight / 3));"
        )
        time.sleep(1)
        driver.execute_script(
            "window.scrollTo(0, Math.floor(document.body.scrollHeight * 2 / 3));"
        )
        time.sleep(1)
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        time.sleep(1)

        html_content = driver.page_source
        log_message(f"Страница успешно загружена: {url} ({len(html_content)} байт)")
        return html_content

    except Exception as e:
        log_message(f"Ошибка при загрузке страницы {url} через Selenium: {e}", "error")
        if driver:
            driver.save_screenshot(f"error_{url.replace('://', '_').replace('/', '_').replace(':', '_')[:50]}.png")
        return None
    finally:
        if driver:
            driver.quit()
            log_message("WebDriver закрыт")


def fetch_html_content(url):
    """Парсим HTML-контент по заданному URL (через requests)."""
    try:
        log_message(f"Загрузка страницы (requests): {url}")
        throttle_request()
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        log_message(f"Страница успешно загружена: {url} ({len(response.text)} байт)")
        return response.text
    except requests.exceptions.RequestException as e:
        log_message(f"Ошибка при загрузке страницы {url}: {e}", "error")
        # Если не удалось загрузить через requests, пробуем через Selenium
        log_message(f"Попытка загрузки через Selenium...", "info")
        return fetch_html_content_selenium(url)


def extract_text_from_html(html_content, url):
    """Извлекаем текст из HTML-контента, удаляя теги."""
    if not html_content:
        log_message(f"Нет HTML контента для извлечения из {url}", "warning")
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Удаляем скрипты, стили и другие ненужные элементы
    for element in soup(["script", "style", "header", "footer", "nav", "aside", "iframe", "noscript", "svg", "button"]):
        element.decompose()

    # Получаем текст, разбиваем на строки и удаляем лишние пробелы
    text = ' '.join(soup.stripped_strings)

    # Если текст слишком длинный, обрезаем его
    max_length = 100000  # Максимальная длина текста для обработки
    if len(text) > max_length:
        log_message(f"Текст слишком длинный ({len(text)} символов), обрезаем до {max_length} символов", "info")
        text = text[:max_length]

    log_message(f"Извлечено {len(text)} символов текста из {url}")
    return text


def summarize_with_gemini(text, topic):
    """Отправляем текст в Gemini API для получения сводки."""
    if not text.strip():
        log_message("Не удалось извлечь значимый текст для обработки.", "warning")
        return "Не удалось извлечь значимый текст для обработки."

    log_message(f"Отправка запроса в Gemini API для анализа текста ({len(text)} символов)")
    prompt = f"""Пожалуйста, составьте краткую сводку информации по теме '{topic}', основываясь на следующем тексте:

{text}

Сводка должна быть написана на человеческом языке, содержать ключевые моменты и быть структурированной.
Если в тексте есть противоречивая информация, укажите на это.
"""
    try:
        throttle_request()
        response = model.generate_content(prompt)
        log_message("Получен ответ от Gemini API")
        return response.text
    except Exception as e:
        error_msg = f"Ошибка при обращении к Gemini API: {e}"
        log_message(error_msg, "error")
        return "Произошла ошибка при обработке текста с помощью Gemini."


def search_and_summarize(topic, engine='google'):
    """Основная функция для поиска и суммаризации информации"""
    log_message(f"Новый запрос: '{topic}' (поисковик: {engine})")

    if engine == 'google':
        relevant_urls = search_relevant_urls_google(topic, GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID)
    elif engine == 'duckduckgo':
        # Используем Selenium для DuckDuckGo
        relevant_urls = search_relevant_urls_duckduckgo_selenium(topic)
    elif engine == 'yandex':
        # Используем Selenium для Яндекса
        relevant_urls = search_relevant_urls_yandex_selenium(topic)
    else:
        log_message(f"Неизвестный поисковый движок: {engine}", "error")
        return "Ошибка: Неизвестный поисковый движок"

    if not relevant_urls:
        log_message("Не удалось найти релевантные URL-адреса", "error")
        return "Ошибка: Не удалось найти релевантные URL-адреса"
    else:
        all_extracted_text = ""
        for url in relevant_urls:
            html_content = fetch_html_content(url)  # Это теперь может использовать Selenium как резервный вариант
            if html_content:
                text = extract_text_from_html(html_content, url)
                all_extracted_text += f"\n\n=== Источник: {url} ===\n\n{text}"

        if all_extracted_text.strip():
            log_message("Отправка извлеченного текста для анализа в Gemini...")
            summary = summarize_with_gemini(all_extracted_text, topic)
            log_message("Анализ завершен")
            return summary
        else:
            log_message("Не удалось извлечь текст из страниц", "error")
            return "Ошибка: Не удалось извлечь текст из страниц"


def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(description='Поиск и суммаризация информации по заданной теме')
    parser.add_argument('topic', type=str, help='Тема для поиска и суммаризации')
    parser.add_argument('--engine', '-e', type=str, choices=['google', 'yandex', 'duckduckgo'], 
                        default='google', help='Поисковый движок (по умолчанию: google)')
    
    args = parser.parse_args()
    
    # Проверяем доступность ChromeDriver
    try:
        log_message("Проверка доступности ChromeDriver...")
        driver = create_webdriver()
        driver.quit()
        log_message("ChromeDriver успешно проверен")
    except Exception as e:
        log_message(f"Ошибка при проверке ChromeDriver: {e}", "error")
        log_message("Убедитесь, что Chrome установлен в системе", "error")
        return
    
    summary = search_and_summarize(args.topic, args.engine)
    print("\n" + "="*80 + "\n")
    print(f"СВОДКА ПО ТЕМЕ: {args.topic}\n")
    print(summary)
    print("\n" + "="*80)


if __name__ == "__main__":
    main() 