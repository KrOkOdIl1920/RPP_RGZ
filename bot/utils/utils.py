import aiohttp


async def get_currency_rate(currency: str) -> float | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://195.58.54.159:8000/rate?currency={currency}") as response:
            if response.status == 200:
                data = await response.json()
                return data["rate"]
            else:
                return None
