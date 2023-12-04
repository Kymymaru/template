from dataclasses import dataclass


@dataclass
class Bot:
    token = '6689906797:AAEKnJ1WtL7oiZGFnNd50tpHTsstXtcOvzM'
    use_redis = True
    skip_updates = False

    logging = False
    logs_folder_name = 'bot_logs'

    throttling_time = 2
    admins = [491264374, 2098533627]
    mailing_speed = 25

    polling = True
    BASE_URL = 'https://0ee4-213-230-88-151.ngrok.io'
    WEB_SERVER_HOST = "127.0.0.1"
    WEB_SERVER_PORT = 8080
    MAIN_BOT_PATH = "/webhook"


@dataclass
class Database:
    user = 'root'
    password = '1234'

    host = 'localhost'
    database = 'database'

    debug = True


@dataclass
class Payok:
    api_id = 2817
    key = 'B184E62051062F406903E4966668789D-8AF92711C7DE1D225B2A6F85FACC0777-D9A84CC222144ADA8035AF4F9ADAD147'

    shop_id = 6492
    secret = '329cdf9593d24b96ebd437691ea812b1'


@dataclass
class PaySelection:
    project_id = 21188
    project_secret = 'CtFTs7Pem5rRSrtW'

    ip = '86.107.197.41'
    port = 8080


@dataclass
class Config:
    bot = Bot()
    database = Database()
    pay_selection = PaySelection()
    payok = Payok()


config = Config()
