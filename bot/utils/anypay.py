import httpx
import hashlib
import random

from bot.config import config


class AnyPayError(Exception):

    def __init__(self, error: dict):
        super().__init__(
            f"[{error['code']}] AnyPay API Exception: {error['message']}."
        )


class Bill(object):

    def __init__(self, bill_id: int, bill_url: str, amount: int, price: int):
        self.id = bill_id
        self.url = bill_url
        self.amount = amount
        self.price = price


class AnyPay:

    def __init__(self, api_id: str, api_key: str, project_id: int, project_secret: str):

        self.api_id = api_id
        self.api_key = api_key

        self.project_id = project_id
        self.project_secret = project_secret

        self.baseurl = 'https://anypay.io/merchant'
        self.apiurl = f'https://anypay.io/api/payments/{api_id}'

        self.session = httpx.AsyncClient()
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'multipart/form-data',
        }

        signature = hashlib.sha256(
            f'balance{api_id}{api_key}'.encode()
        )
        response = httpx.get(
            f'https://anypay.io/api/balance/{api_id}',
            params={'sign': signature.hexdigest()}
        ).json()

        if 'error' in response:
            raise AnyPayError(response['error'])

    async def create_bill(self, amount: int, bill_id: int, desc: str = 'Покупка VIP-статуса') -> Bill:

        signature = hashlib.md5(
            f'RUB:{amount}:{self.project_secret}:{self.project_id}:{bill_id}'.encode('utf-8')
        )

        params = {
            'merchant_id': self.project_id,
            'pay_id': bill_id,
            'amount': amount,
            'desc': desc,
            'sign': signature.hexdigest()
        }
        bill_url = await self.session.get(
            self.baseurl,
            params=params
        )

        return Bill(int(bill_id), str(bill_url.url), 1, amount)

    async def check_payment(self, bill_id: int) -> bool:

        signature = hashlib.sha256(
            f'payments{self.api_id}{self.project_id}{self.api_key}'.encode('utf-8')
        )
        params = {
            'sign': signature.hexdigest(),
            'project_id': self.project_id,
            'pay_id': bill_id
        }

        response = (await self.session.get(
            self.apiurl,
            headers=self.headers,
            params=params
        )).json()

        if 'error' in response:

            try:

                raise AnyPayError(response['error'])

            finally:

                return False

        data = response['result']['payments']

        if data:
            return next(iter(data.values()))['status'] == 'paid'

        return False


class Debug:
    async def create_bill(self, **kwargs):
        pass

    async def check_payment(self, **kwargs):
        return True


# payment = AnyPay(
#     config.anypay.api_id,
#     config.anypay.api_key,
#     config.anypay.project_id,
#     config.anypay.project_secret
# )

payment = Debug()
