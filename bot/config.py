from dataclasses import dataclass


@dataclass
class Bot:
    token: str = '6689906797:AAEKnJ1WtL7oiZGFnNd50tpHTsstXtcOvzM'
    use_redis: bool = True
    skip_updates: bool = False

    logging: bool = False
    logs_folder_name: str = 'bot_logs'

    throttling_time: int = 2
    admins = [491264374, 2098533627]
    mailing_speed: int = 25

    polling: bool = True
    BASE_URL: str = 'https://0ee4-213-230-88-151.ngrok.io'
    WEB_SERVER_HOST: str = "127.0.0.1"
    WEB_SERVER_PORT: int = 8080
    MAIN_BOT_PATH: str = "/webhook"


@dataclass
class DB:
    user: str = 'root'
    password: str = '1234'

    host: str = 'localhost'
    database: str = 'database'

    debug: bool = True


@dataclass
class Config:
    bot = Bot()
    database = DB()


config = Config()
