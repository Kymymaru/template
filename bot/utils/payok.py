from bot.config import config
import random
from urllib.parse import urlencode
from hashlib import md5
from typing import Optional
import httpx


class Bill(object):

    def __init__(self, bill_id: int, bill_url: str, amount: int, price: int):
        self.id = bill_id
        self.url = bill_url
        self.amount = amount
        self.price = price


class PayOk:
    def __init__(self, api_id: str, api_key: str, project_id: int, project_secret: str):
        self.api_id = api_id,
        self.api_key = api_key
        self.shop_id = project_id
        self.shop_secret = project_secret
        self.session = httpx.AsyncClient()

    async def create_bill(
            self,
            amount: float,
            user_id: int,
            desc: Optional[str] = 'Description',
    ) -> Bill:
        payment_id = f'{user_id}{random.randint(1000, 9999)}'

        if not self.shop_secret:
            raise Exception('Secret key is empty')

        params = {
            'amount': amount,
            'payment': payment_id,
            'shop': self.shop_id,
            'currency': 'RUB',
            'desc': desc,
        }

        for key, value in params.copy().items():
            if value is None:
                del params[key]

        sign_params = '|'.join(map(
            str,
            [amount, payment_id, self.shop_id, 'RUB', desc, self.shop_secret]
        )).encode('utf-8')
        sign = md5(sign_params).hexdigest()
        params['sign'] = sign

        url = 'https://payok.io/pay?' + urlencode(params)
        return Bill(int(payment_id), str(url), 1, amount)

    async def check_payment(self, payment_id: int) -> bool:
        url = 'https://payok.io/api/transaction'
        data = {
            'API_ID': self.api_id,
            'API_KEY': self.api_key,
            'shop': self.shop_id
        }
        if payment:
            data['payment'] = payment_id

        response = await self.session.post(url=url, data=data)
        response_data = response.json()
        if response_data['status'] == 'success':
            return bool(int(response_data['1']['transaction_status']))
        else:
            try:
                return response_data['error_text']
            except:
                return response_data['text']


payment = PayOk(
    config.payok.api_id,
    config.payok.key,
    config.payok.shop_id,
    config.payok.secret
)
