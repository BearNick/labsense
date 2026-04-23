from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from typing import Optional

# 1) Выбор языка
def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇺🇸 English")],
            [KeyboardButton(text="🇪🇸 Español")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# 2) Выбор пола (локализовано)
def gender_keyboard(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        buttons = [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]
    elif lang == "en":
        buttons = [KeyboardButton(text="Male"), KeyboardButton(text="Female")]
    elif lang == "es":
        buttons = [KeyboardButton(text="Masculino"), KeyboardButton(text="Femenino")]
    else:
        buttons = [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]

    return ReplyKeyboardMarkup(
        keyboard=[buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# 3) Объединённая клавиатура: RUB + USDT в первой строке, и широкой кнопкой "Я оплатил" снизу.
#    Можно передать label_amounts (например "999 ₽" / "9.99 USDT") — тогда появятся на кнопках.
def dual_pay_keyboard(
    lang: str,
    rub_url: Optional[str],
    crypto_url: Optional[str],
    label_amount_rub: Optional[str] = None,
    label_amount_usdt: Optional[str] = None
) -> InlineKeyboardMarkup:
    base_labels = {
        "ru": ("💳 USD/EUR", "💸 Оплата USDT", "✅ Я оплатил"),
        "en": ("💳 USD/EUR", "💸 Pay in USDT", "✅ I’ve paid"),
        "es": ("💳 USD/EUR", "💸 Pagar en USDT", "✅ He pagado"),
    }
    rub_lbl, usdt_lbl, paid_lbl = base_labels.get(lang, base_labels["ru"])

    # если передали суммы — добавим их в текст кнопок
    if label_amount_rub:
        rub_lbl = f"{rub_lbl} · {label_amount_rub}"
    if label_amount_usdt:
        usdt_lbl = f"{usdt_lbl} · {label_amount_usdt}"

    rows: list[list[InlineKeyboardButton]] = []

    row1: list[InlineKeyboardButton] = []
    if rub_url:
        row1.append(InlineKeyboardButton(text=rub_lbl, url=rub_url))
    if crypto_url:
        row1.append(InlineKeyboardButton(text=usdt_lbl, url=crypto_url))
    if row1:
        rows.append(row1)

    # широкая нижняя кнопка "Я оплатил" — всегда добавляем
    rows.append([InlineKeyboardButton(text=paid_lbl, callback_data="paid_any")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
