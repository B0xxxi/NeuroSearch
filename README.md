# Console Search Summarizer

Консольное приложение для поиска и суммаризации информации по заданной теме с использованием различных поисковых систем и Gemini API.

## Возможности

- Поиск информации через Google Programmable Search Engine, Яндекс или DuckDuckGo
- Извлечение текста из найденных веб-страниц
- Суммаризация информации с помощью Gemini API
- Работа полностью в консольном режиме

## Требования

- Python 3.8 или выше
- Google Chrome (для работы Selenium)
- API ключ Gemini
- API ключ Google Programmable Search Engine и ID поисковой системы

## Установка

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/yourusername/console-search-summarizer.git
   cd console-search-summarizer
   ```

2. Создайте и активируйте виртуальное окружение:
   ```
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` на основе `.env.example` и заполните его своими API ключами:
   ```
   cp .env.example .env
   # Отредактируйте файл .env, добавив свои ключи API
   ```

## Использование

Базовое использование:
```
python main.py "ваш поисковый запрос"
```

Выбор поисковой системы:
```
python main.py "ваш поисковый запрос" --engine google
python main.py "ваш поисковый запрос" --engine yandex
python main.py "ваш поисковый запрос" --engine duckduckgo
```

Сокращенная форма:
```
python main.py "ваш поисковый запрос" -e google
```

## Получение API ключей

### Gemini API

1. Перейдите на [Google AI Studio](https://ai.google.dev/)
2. Создайте аккаунт или войдите в существующий
3. Перейдите в раздел API Keys и создайте новый ключ
4. Скопируйте ключ в файл `.env`

### Google Programmable Search Engine

1. Перейдите на [Programmable Search Engine](https://programmablesearchengine.google.com/about/)
2. Создайте новую поисковую систему
3. Получите ID поисковой системы (cx) и скопируйте его в файл `.env`
4. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
5. Создайте новый проект
6. Включите Custom Search API
7. Создайте ключ API и скопируйте его в файл `.env`

## Примечания

- Приложение сохраняет HTML-страницы и скриншоты для отладки
- При использовании Selenium может потребоваться установка ChromeDriver, но webdriver-manager должен сделать это автоматически
- Для работы с Яндексом и DuckDuckGo используется Selenium, что может быть медленнее, чем API Google

## Лицензия

MIT 