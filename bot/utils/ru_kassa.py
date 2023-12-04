import httpx

from bot.config import config


class Bill(object):

    def __init__(self, bill_id: int, bill_url: str, amount: int, price: int):
        self.id = bill_id
        self.url = bill_url
        self.amount = amount
        self.price = price


class RuKassaAPI:

    def __init__(self, api_key: str, shop_id: int):
        self.api_key = api_key
        self.shop_id = shop_id
        self.session = httpx.AsyncClient()

    async def create_bill(self, amount: int, bill_id: str, desc: str = 'Покупка баланса') -> Bill:

        payment_data = {
            "shop_id": self.shop_id,
            "amount": amount,
            "order_id": bill_id,
            "token": self.api_key
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = (await self.session.get("https://lk.rukassa.pro/api/v1/create",
                                           params=payment_data, headers=headers)).json()

        if 'error' not in response.keys():
            return Bill(int(response['id']), str(response['url']), 1, amount)
        else:
            return None

    async def check_payment(self, payment_id: str) -> bool:
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        payment_data = {
            'id': payment_id,
            'shop_id': self.shop_id,
            'token': self.api_key
        }

        response = (await self.session.get("https://lk.rukassa.pro/api/v1/getPayInfo",
                                           params=payment_data, headers=headers)).json()
        if 'status' in response.keys():
            return response['status'] == 'PAID'
        else:
            return False


payment = RuKassaAPI(
    config.ru_kassa.api_key,
    config.ru_kassa.shop_id
)
