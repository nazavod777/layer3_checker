import asyncio
from random import choice

import aiohttp
from eth_abi import encode
from eth_account import Account
from eth_account.account import LocalAccount
from loguru import logger
from web3.auto import w3
from invisible_captcha_bypasser import solve_captcha

from utils import append_file
from utils import get_proxy
from utils import loader


class Checker:
    def __init__(self,
                 client: aiohttp.ClientSession,
                 address: str):
        self.client: aiohttp.ClientSession = client
        self.address: str = address

    async def check_eligible(self) -> float:
        while True:
            proxy: str | None = get_proxy()

            response_text: None = None

            try:
                r: aiohttp.ClientResponse = await self.client.get(
                    url=f'https://8zr8yl9lzb.execute-api.eu-central-1.amazonaws.com//eligibility',
                    proxy=proxy,
                    params={
                        'address': self.address,
                        'skipCaptcha': 'true'
                    }
                )
                response_text: str = await r.text()
                response_json: dict = await r.json(content_type=None)

                if not response_json.get('allocation'):
                    logger.error(f'{self.address} | Wrong Response When Checking Eligible: {response_text}')
                    continue

                return int(response_json['allocation']) / 10 ** 18

            except Exception as error:
                if response_text:
                    logger.error(f'{self.address} | Unexpected Error When Checking Eligible: {error}, '
                                 f'response: {response_text}')

                else:
                    logger.error(f'{self.address} | Unexpected Error When Checking Eligible: {error}')

    async def check_account(self) -> None:
        allocation: float = await self.check_eligible()

        if allocation <= 0:
            logger.error(f'{self.address} | Not Eligible')
            return

        async with asyncio.Lock():
            await append_file(
                file_path='result/eligible.txt',
                file_content=f'{self.address}\n'
            )

        logger.success(f'{self.address} | {allocation}')


async def check_account(
        client: aiohttp.ClientSession,
        address: str
) -> None:
    async with loader.semaphore:
        try:
            address: str = w3.to_checksum_address(value=address)

        except ValueError:
            logger.error(f'{address} | Invalid Address')
            return

        checker: Checker = Checker(
            client=client,
            address=address
        )
        await checker.check_account()
