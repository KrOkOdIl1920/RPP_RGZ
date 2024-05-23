from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from decimal import Decimal


from bot.keyboards.inline import operation_type_keyboard, currency_keyboard
from bot.utils.utils import get_currency_rate
from bot.states.states import Registration, AddOperation
from bot.db.cur import conn


router = Router()


@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Я бот для учёта финансов. Используй команду /reg, чтобы использовать мой функционал!")


@router.message(Command("reg"))
async def cmd_reg(message: Message, state: FSMContext):
    chat_id = message.chat.id
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
        user = cur.fetchone()
        if user:
            await message.answer("Вы уже зарегистрированы!")
        else:
            await message.answer("Введите ваш логин:")
            await state.set_state(Registration.waiting_for_name)


@router.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text
    chat_id = message.chat.id

    if len(name) > 50:
        await message.answer("Логин не может превышать 50 символов! Придумайте новый!")
        return

    with conn.cursor() as cur:
        cur.execute("INSERT INTO users (chat_id, name, date) VALUES (%s, %s, %s)",
                    (chat_id, name, datetime.now().date()))
        conn.commit()
    await message.answer(f"Вы успешно зарегистрированы. Ваш логин: {name}")
    await state.clear()


@router.message(Command("add_operation"))
async def cmd_add_operation(message: Message):
    chat_id = message.chat.id
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
        user = cur.fetchone()
        if not user:
            await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь с помощью команды /reg.")
            return

        await message.answer("Выберите тип операции:", reply_markup=operation_type_keyboard)


@router.callback_query(F.data.startswith("type:"))
async def process_operation_type(callback: CallbackQuery, state: FSMContext):
    operation_type = callback.data.split(":")[1]
    await state.update_data(type=operation_type)
    await callback.message.answer("Введите сумму операции в рублях:")
    await state.set_state(AddOperation.waiting_for_amount)
    await callback.answer()


@router.message(AddOperation.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount_str = message.text.replace(",", ".")
        amount = float(amount_str)

    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму в рублях.")
        return

    await state.update_data(amount=amount)
    await message.answer("Введите дату операции в формате ДД.ММ.ГГГГ:")
    await state.set_state(AddOperation.waiting_for_date)


@router.message(AddOperation.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    try:
        operation_date = datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")
        return

    data = await state.get_data()
    operation_type = data["type"]
    amount = data["amount"]
    chat_id = message.chat.id

    with conn.cursor() as cur:
        cur.execute("INSERT INTO operations (date, sum, chat_id, type_operation) VALUES (%s, %s, %s, %s)",
                    (operation_date, amount, chat_id, operation_type))
        conn.commit()

    await message.answer("Операция успешно добавлена!")
    await state.clear()


@router.message(Command("operations"))
async def cmd_operations(message: Message):
    chat_id = message.chat.id
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
        user = cur.fetchone()
        if not user:
            await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь с помощью команды /reg.")
            return

        await message.answer("Выберите валюту для просмотра операций:", reply_markup=currency_keyboard)


@router.callback_query(F.data.startswith("currency:"))
async def process_currency(callback: CallbackQuery):
    currency = callback.data.split(":")[1]

    if currency in ["EUR", "USD"]:
        rate = await get_currency_rate(currency)
        if rate is None:
            await callback.message.answer("Произошла ошибка при получении курса валюты. Попробуйте еще раз позже.")
            await callback.answer()
            return
    else:
        rate = Decimal(1)

    chat_id = callback.message.chat.id
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM operations WHERE chat_id = %s", (chat_id,))
        operations = cur.fetchall()

    if not operations:
        await callback.message.answer("У вас пока нет операций.")
    else:
        operations_text = "Ваши операции:\n"
        for operation in operations:
            operation_date = operation[1].strftime("%d.%m.%Y")
            amount = operation[2] / Decimal(rate)
            amount = round(amount, 2)
            operation_type = operation[4]
            operations_text += f"{operation_date} - {amount} {currency} ({operation_type})\n"

        await callback.message.answer(operations_text)

    await callback.answer()


@router.message(Command("lk"))
async def cmd_lk(message: Message):
    chat_id = message.chat.id
    with conn.cursor() as cur:
        try:
            cur.execute("ROLLBACK")  # Завершаем текущую транзакцию
            cur.execute("SELECT name, date FROM users WHERE chat_id = %s", (chat_id,))
            user = cur.fetchone()
            if not user:
                await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь с помощью команды /reg.")
                return

            name, date = user
            date = date.strftime("%d.%m.%Y")

            cur.execute("SELECT COUNT(*) FROM operations WHERE chat_id = %s", (chat_id,))
            operations_count = cur.fetchone()[0]
        except Exception as e:
            print(f"Error: {e}")
            await message.answer("Произошла ошибка при получении информации о пользователе.")
            return

    lk_text = f"Информация о пользователе:\n" \
              f"Логин: {name}\n" \
              f"Дата регистрации: {date}\n" \
              f"Количество добавленных операций: {operations_count}"

    await message.answer(lk_text)
