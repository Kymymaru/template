[<img src="https://img.shields.io/badge/Telegram-%40hexdevop_test_bot">](https://t.me/hexdevop_test_bot)
# Темплейт телеграмм бота

Темплейт с готовой админ панелью, мидлварями, фильтрами. Еще присутствует настройки логирования, включения вебхуков или поллинга, 4 платежные системы

## Технологии

* [aiogram](https://t.me/github.com/aiogram/aiogram) - Работа с Telegram Bot Api;
* [redis](https://redis.io) - Персистентное хранение данных (персистентность включается отдельно);
* [cachetools](https://cachetools.readthedocs.io/en/stable) - Реализация троттлинга для борьбы со флудом;
* Systemd

## Установка на Windows

Перед установкой бота нужно будет установить [MysqlServer](https://dev.mysql.com/downloads/mysql/) и [RedisServer](https://github.com/tporadowski/redis/releases)

```
git clone https://github.com/Kymymaru/template.git
python -m venv bot_venv
bot_venv\Scripts\activate
cd template
pip install -r requirements.txt
python -m bot
```

## Установка на Linux (Debian system)
```
apt install mysql-server redis-server python3-pip python3.10-venv
git clone https://github.com/Kymymaru/template.git
python3 -m venv bot_venv
source bot_venv\Scripts\activate
cd emplate
pip3 install -r requirements.txt
python3 -m bot
```

[<img src="https://img.shields.io/badge/Telegram-%40hexdevop">](https://t.me/hexdevop)
