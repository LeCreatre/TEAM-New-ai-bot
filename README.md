# TEAM University — AI Admissions Bot (Telegram + OpenAI + aiogram)

Бот отвечает на вопросы ТОЛЬКО о TEAM University и показывает 3 быстрые кнопки:
**3D Кампус Тур**, **Контакты**, **Чат с Admissions**.

## Быстрый старт

1) Установите Python 3.10+
2) Перейдите в папку проекта:
   ```bash
   cd team_ai_admissions_bot
   ```
3) Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
4) Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
5) Скопируйте `.env.example` в `.env` и заполните:
   - `BOT_TOKEN` — токен Telegram-бота от @BotFather
   - `OPENAI_API_KEY` — ключ OpenAI
   - `ALLOWED_CHATS` — список chat_id через запятую (необязательно)
6) Запустите бота:
   ```bash
   python main.py
   ```

## Как это работает
- Быстрый офф-топ фильтр по ключевым словам (до обращения к модели).
- Контекст для модели: системный промпт + `knowledge_base.md`.
- Тон ответов — дружелюбный и конкретный; при нехватке данных бот направляет в Admissions.

## Кнопки
- **3D Кампус Тур** — ссылка на Matterport.
- **Контакты** — показывает телефон, сайт, ссылку на чат Admissions.
- **Чат с Admissions** — прямая ссылка в Telegram.

## Расширение базы знаний
- Обновляйте `knowledge_base.md` — бот автоматически подмешивает её в контекст.

## Продакшен‑заметки
- Запускайте как systemd‑сервис или в Docker.
- На первом этапе включите ALLOWED_CHATS для тестирования.
- Добавьте логирование и мониторинг таймаутов/ошибок OpenAI.
