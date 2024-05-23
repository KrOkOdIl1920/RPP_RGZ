from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

operation_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="РАСХОД",
            callback_data="type:РАСХОД"
        )
    ],
    [
        InlineKeyboardButton(
            text="ДОХОД",
            callback_data="type:ДОХОД"
        )
    ]
])

currency_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="RUB",
            callback_data="currency:RUB"
        )
    ],
    [
        InlineKeyboardButton(
            text="EUR",
            callback_data="currency:EUR"
        )
    ],
    [
        InlineKeyboardButton(
            text="USD",
            callback_data="currency:USD"
        )
    ]
])
