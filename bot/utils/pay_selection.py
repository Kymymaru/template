import asyncio
import hmac
import json

import aiohttp

from contextlib import suppress
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Optional
from uuid import uuid4
import loguru

from bot.config import config

log = loguru.logger


class Bill(object):

    def __init__(self, bill_id: int, bill_url: str, amount: int, price: int):
        self.id = bill_id
        self.url = bill_url
        self.amount = amount
        self.price = price


class PaySelectionError(Exception):

    def __init__(self, response: dict) -> None:
        self.code = response['Code']
        self.description = response['Description']
        self.details = response['AddDetails']

        super().__init__(self.code)


class PaySelectionAPI(object):
    _session: Optional[aiohttp.ClientSession] = None

    def __init__(self, project_id: int, project_secret: str, webhook_url: str) -> None:

        self.project_id = str(project_id)
        self.project_secret = project_secret
        self.webhook_url = webhook_url

    def session(self) -> aiohttp.ClientSession:

        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()

        return self._session

    def get_headers(self, method: str, endpoint: str, body: str) -> dict:

        request_id = str(uuid4())
        signature_string = '\n'.join([
            method,
            endpoint.split('.com', 1)[1],
            self.project_id,
            request_id,
            body,
        ])
        signature = hmac.new(
            key=self.project_secret.encode(),
            msg=signature_string.encode(),
            digestmod=sha256,
        ).hexdigest()

        return {
            'X-SITE-ID': self.project_id,
            'X-REQUEST-ID': request_id,
            'X-REQUEST-SIGNATURE': signature,
            'Content-Type': 'application/json',
        }

    async def request(self, method: str, endpoint: str, data: dict) -> dict:

        body = json.dumps(data)
        async with self.session().request(
                method=method,
                url=endpoint,
                headers=self.get_headers(
                    method=method,
                    endpoint=endpoint,
                    body=body,
                ),
                data=body,
        ) as response:
            response = await response.json()

        log.info(response)

        if isinstance(response, dict) and response.get('Code'):
            raise PaySelectionError(response)

        return response

    async def get_link(self, offset: int, amount: float, user_id: int) -> str:

        next_charge = datetime.utcnow() + timedelta(days=offset)
        print(f'{amount:.2f}', )
        response = await self.request(
            method='POST',
            endpoint='https://webform.payselection.com/webpayments/create',
            data={
                'PaymentRequest': {
                    'OrderId': str(uuid4()),
                    'Amount': f'{amount:.2f}',
                    'Currency': 'RUB',
                    'Description': 'Оплата VIP-подписки',
                    'RebillFlag': True,
                    'ExtraData': {'WebhookUrl': self.webhook_url + '/stat/%s' % user_id},
                },
                'RecurringData': {
                    'Amount': "299.00",
                    'WebhookUrl': self.webhook_url + '/recurring/%i' % user_id,
                    'Currency': 'RUB',
                    'AccountId': str(user_id),
                    'StartDate': next_charge.strftime('%Y-%m-%dT%H:%M+0000'),
                    'Interval': '3',
                    'Period': 'day',
                },
            },
        )
        return response

    async def cancel_subs(self, user_id: int, rebill_id: str) -> dict:

        subs = await self.request(
            method='POST',
            endpoint='https://gw.payselection.com/payments/recurring/search',
            data={'AccountId': str(user_id)},
        )

        for sub in subs:
            with suppress(PaySelectionError):
                await self.request(
                    method='POST',
                    endpoint='https://gw.payselection.com/payments/recurring/unsubscribe',
                    data={'RecurringId': sub['RecurringId']},
                )

        await self.request(
            method='POST',
            endpoint='https://gw.payselection.com/payments/unsubscribe',
            data={'RebillId': rebill_id},
        )

    async def charge_daily_sub(self, rebill_id: str, user_id: int) -> dict:

        return await self.request(
            method='POST',
            endpoint='https://gw.payselection.com/payments/requests/rebill',
            data={
                'RebillId': rebill_id,
                'OrderId': str(uuid4()),
                'Amount': '99.00',
                'Currency': 'RUB',
                'WebhookUrl': self.webhook_url + '/rebill/%s' % user_id,
            },
        )

    def __del__(self) -> None:

        if not self._session or self._session.closed:
            return

        asyncio.get_event_loop() \
            .create_task(self._session.close())


payment = PaySelectionAPI(
    config.pay_selection.project_id,
    config.pay_selection.project_secret,
    f'http://{config.pay_selection.ip}:{config.pay_selection.port}',
)
