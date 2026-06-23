# MAX → Telegram Notify

Уведомления из одного MAX-чата в Telegram. При входящем сообщении бот пишет в указанную беседу: `📨 Имя: текст`.

## Требования

- Python 3.11+
- Telegram-бот, добавленный в беседу с правами отправки сообщений
- Аккаунт MAX

---

## Развёртывание на сервере

### 1. Клонировать репозиторий

```bash
git clone https://github.com/<твой_ник>/max-tg-notify.git /root/max-tg-notify
cd /root/max-tg-notify
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Настроить переменные окружения

```bash
cp .env.example .env
nano .env
```

| Переменная     | Пример              | Описание                                           |
|----------------|---------------------|----------------------------------------------------|
| `MAX_PHONE`    | `+79990000000`      | Номер телефона MAX-аккаунта                        |
| `MAX_CHAT_ID`  | `123456789`         | ID чата MAX, который слушаем                       |
| `TG_BOT_TOKEN` | `1234567890:AAF...` | Токен бота ([@BotFather](https://t.me/BotFather)) |
| `TG_CHAT_ID`   | `-1001234567890`    | ID Telegram-беседы для уведомлений                 |

**Как узнать TG_CHAT_ID:** добавь бота в беседу, напиши любое сообщение, открой в браузере:
```
https://api.telegram.org/bot<TG_BOT_TOKEN>/getUpdates
```
Найди `"chat": {"id": ...}` — это и есть `TG_CHAT_ID`.

### 4. Первый запуск — авторизация в MAX

Запусти один раз вручную, чтобы ввести код подтверждения из MAX:

```bash
source venv/bin/activate
python3 main.py
```

Введи код, дождись строки `watching chat ...` — затем `Ctrl+C`.

Сессия сохраняется в `cache/session.db`, повторная авторизация не нужна.

### 5. Создать systemd-сервис

```bash
nano /etc/systemd/system/max-tg-notify.service
```

Содержимое:

```ini
[Unit]
Description=MAX to Telegram Notify
After=network.target

[Service]
WorkingDirectory=/root/max-tg-notify
ExecStart=/root/max-tg-notify/venv/bin/python3 main.py
Restart=on-failure
RestartSec=10
EnvironmentFile=/root/max-tg-notify/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 6. Запустить и включить автозапуск

```bash
sudo systemctl daemon-reload
sudo systemctl enable max-tg-notify
sudo systemctl start max-tg-notify
```

Проверить статус:

```bash
sudo systemctl status max-tg-notify
sudo journalctl -u max-tg-notify -f
```

---

## Обновление

```bash
cd /root/max-tg-notify
git pull
sudo systemctl restart max-tg-notify
```

---

## Файлы состояния

| Путь               | Содержимое                                           |
|--------------------|------------------------------------------------------|
| `cache/session.db` | Сессия MAX (не удалять — потребует переавторизации) |
