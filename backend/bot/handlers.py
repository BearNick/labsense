# bot/handlers.py
from aiogram import F, Dispatcher
from aiogram.types import Message, Document, CallbackQuery
from aiogram.fsm.context import FSMContext
import os
from pathlib import Path                  # ✅
from uuid import uuid4                    # ✅

from bot.states import Form
from bot.keyboards import language_keyboard, gender_keyboard, dual_pay_keyboard
from bot.config import (
    UPLOAD_FOLDER,
    MAX_PDF_PAGES,
    CRYPTO_ASSET, CRYPTO_PRICE,
    STRIPE_PAY_URL, STRIPE_PRICE_USD,
    # приватность:
    STORE_UPLOADS,                        # ✅
)
from parser.translations import translations
from interpreter.analyze import generate_interpretation

from parser.source_selection import select_and_extract_lab_data

# Крипта (инвойс создаём «мягко» — без падений UX)
from bot.crypto_pay import create_invoice


# ──────────────────────────
# Вспомогалки
# ──────────────────────────

def _fmt_amount(val, currency: str) -> str:
    """Красивое форматирование сумм по валюте."""
    if val is None:
        return ""
    try:
        v = float(val)
    except Exception:
        return ""
    if currency == "RUB":
        return f"{int(round(v))} ₽"
    if currency == "USD":
        return f"{v:.2f} $"
    if currency == "EUR":
        return f"{v:.2f} €"
    if currency.upper() == "USDT":
        return f"{v:.2f} USDT"
    return f"{v:.2f} {currency}"


def _translated_metrics(lab_data: dict, lang: str) -> str:
    """Перевод меток и вывод только числовых значений."""
    tr = translations.get(lang, translations["ru"])
    lines = []
    for k, v in lab_data.items():
        if v is None:
            continue
        label = tr.get(k, k)
        lines.append(f"{label}: {v}")
    return "\n".join(lines) if lines else ""


# ──────────────────────────
# Диалоги
# ──────────────────────────

# /start — выбор языка
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🌐 Выберите язык / Choose language / Elige idioma:",
        reply_markup=language_keyboard()
    )
    await state.set_state(Form.waiting_for_language)


# Выбор языка
async def set_language(message: Message, state: FSMContext):
    lang_input = message.text.strip()
    lang_map = {
        "🇷🇺 Русский": "ru",
        "🇺🇸 English": "en",
        "🇪🇸 Español": "es",
    }

    if lang_input not in lang_map:
        await message.answer("❌ Пожалуйста, выберите язык из предложенных.")
        return

    lang = lang_map[lang_input]
    await state.update_data(language=lang)

    prompts = {
        "ru": "Укажи свой возраст:",
        "en": "Please enter your age:",
        "es": "Por favor, ingresa tu edad:",
    }
    await message.answer(prompts[lang])
    await state.set_state(Form.waiting_for_age)


# Ввод возраста
async def ask_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("🔢 Пожалуйста, укажи возраст числом.")
        return

    await state.update_data(age=int(message.text))
    data = await state.get_data()
    lang = data.get("language", "ru")

    prompts = {
        "ru": "Укажи пол:",
        "en": "Select your gender:",
        "es": "Selecciona tu género:",
    }
    await message.answer(prompts[lang], reply_markup=gender_keyboard(lang))
    await state.set_state(Form.waiting_for_gender)


# Ввод пола
async def ask_gender(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "ru")

    gender_map = {
        "ru": ["мужской", "женский"],
        "en": ["male", "female"],
        "es": ["masculino", "femenino"],
    }
    if message.text.lower() not in gender_map[lang]:
        errs = {
            "ru": "❌ Пожалуйста, выбери пол из кнопок.",
            "en": "❌ Please choose your gender from the buttons.",
            "es": "❌ Por favor, selecciona tu género de los botones.",
        }
        await message.answer(errs[lang])
        return

    await state.update_data(gender=message.text.lower())

    prompts = {
        "ru": "📄 Теперь отправь PDF с анализами.",
        "en": "📄 Now send your lab results as a PDF file.",
        "es": "📄 Ahora envía tus análisis en formato PDF.",
    }
    await message.answer(prompts[lang])
    await state.set_state(Form.waiting_for_file)


# Обработка PDF-файла — ОГРАНИЧЕНИЕ: 1 файл на сессию
async def handle_pdf(message: Message, state: FSMContext):
    document: Document | None = message.document
    data = await state.get_data()
    lang = data.get("language", "ru")

    # 🔒 Блок повторной загрузки в одной сессии
    if data.get("file_uploaded"):
        msgs = {
            "ru": "⚠️ В этой сессии уже обработан 1 файл.\nЧтобы загрузить новый — начни заново командой /start.",
            "en": "⚠️ One file has already been processed in this session.\nTo upload another, please restart with /start.",
            "es": "⚠️ Ya se procesó 1 archivo en esta sesión.\nPara enviar otro, reinicia con /start.",
        }
        await message.answer(msgs[lang])
        return

    if not document or not document.file_name.lower().endswith(".pdf"):
        errs = {
            "ru": "⚠️ Пожалуйста, отправь файл в формате PDF.",
            "en": "⚠️ Please send a PDF file.",
            "es": "⚠️ Por favor, envía un archivo PDF.",
        }
        await message.answer(errs[lang])
        return

    # ✅ безопасное имя файла (без пользовательского оригинала)
    upload_dir = Path(UPLOAD_FOLDER)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}.pdf"
    file_path = upload_dir / safe_name

    try:
        # Сразу ставим флаг, чтобы параллельные/дублирующие попытки в этой сессии блокировались
        await state.update_data(file_uploaded=True)

        # 1) Скачиваем PDF
        file_info = await message.bot.get_file(document.file_id)
        await message.bot.download_file(file_info.file_path, destination=str(file_path))

        # Сообщение «получено, обрабатываю»
        saved = {
            "ru": "✅ Данные получены, обрабатываю...",
            "en": "✅ Data received, processing...",
            "es": "✅ Datos recibidos, procesando...",
        }
        await message.answer(saved[lang])

        # 2) Парсинг: автоматически выбираем лучший источник
        parse_result = select_and_extract_lab_data(str(file_path), language=lang, max_pages=MAX_PDF_PAGES)
        lab_data = parse_result.raw_values

        if not lab_data or all(v is None for v in lab_data.values()):
            errs = {
                "ru": "⚠️ Не удалось извлечь данные из PDF. Попробуй более чёткий скан/оригинал.",
                "en": "⚠️ Failed to extract data from the PDF. Please try a clearer scan/original.",
                "es": "⚠️ No se pudieron extraer datos del PDF. Intenta con un escaneo más claro/original.",
            }
            await message.answer(errs[lang])
            # Разрешим повтор через /start — явно подскажем
            hint = {
                "ru": "Чтобы попробовать снова, начни заново командой /start.",
                "en": "To try again, please restart with /start.",
                "es": "Para intentarlo de nuevo, reinicia con /start.",
            }
            await message.answer(hint[lang])
            await state.clear()
            return

        # 3) Показать извлечённые значения (локализованные метки)
        extracted_text = _translated_metrics(lab_data, lang)
        if extracted_text:
            heads = {
                "ru": "📊 Извлечённые показатели:",
                "en": "📊 Extracted values:",
                "es": "📊 Valores extraídos:",
            }
            await message.answer(f"{heads[lang]}\n{extracted_text}")

        # 4) Интерпретация (учитывает age/gender/language + значения)
        interpretation = generate_interpretation({**data, **lab_data})
        await message.answer(interpretation)

        # 5) Оплата: создаём инвойс CryptoBot (если токен задан), плюс Stripe
        crypto_url = None
        try:
            payload = f"user:{message.from_user.id}"
            desc_map = {
                "ru": "Поддержка бота и развитие проекта",
                "en": "Support the bot & project development",
                "es": "Apoya el bot y el desarrollo del proyecto",
            }
            invoice = create_invoice(
                amount=CRYPTO_PRICE,
                asset=CRYPTO_ASSET,
                description=desc_map[lang],
                payload=payload,
            )
            if invoice:
                crypto_url = invoice.get("pay_url")
        except Exception:
            crypto_url = None  # тихо продолжаем

        # 6) Меню оплаты (USDT + «Я оплатил»)
        usd_line = _fmt_amount(STRIPE_PRICE_USD, "USD")
        usdt_line = _fmt_amount(CRYPTO_PRICE, "USDT")

        pay_text = {
            "ru": f"Поддержите проект:\n• USD: {usd_line}\n• USDT: {usdt_line}",
            "en": f"Support the project:\n• USD: {usd_line}\n• USDT: {usdt_line}",
            "es": f"Apoya el proyecto:\n• USD: {usd_line}\n• USDT: {usdt_line}",
        }[lang]

        await message.answer(
            pay_text,
            reply_markup=dual_pay_keyboard(lang, STRIPE_PAY_URL, crypto_url),
        )

        # Можно сохранить контекст
        await state.update_data(last_lab_data=lab_data)

        # Явно подсказка, что для нового файла нужен /start
        done_hint = {
            "ru": "✅ Готово! Чтобы загрузить новый PDF, начни заново командой /start.",
            "en": "✅ All set! To upload another PDF, please restart with /start.",
            "es": "✅ ¡Listo! Para enviar otro PDF, reinicia con /start.",
        }
        await message.answer(done_hint[lang])

    except Exception as e:
        errs = {
            "ru": f"❌ Ошибка при обработке файла: {e}",
            "en": f"❌ Error processing file: {e}",
            "es": f"❌ Error al procesar el archivo: {e}",
        }
        await message.answer(errs[lang])
        await state.clear()

    finally:
        # ✅ Авто-удаление файла после обработки, если STORE_UPLOADS = False
        try:
            if 'file_path' in locals() and not STORE_UPLOADS and file_path.exists():
                file_path.unlink()
        except Exception:
            pass


# Коллбэк «Я оплатил» — просто спасибо (без автопроверки)
async def cb_paid_any(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "ru")
    thanks = {
        "ru": "✅ Спасибо за поддержку! Это помогает развивать бота 🙌",
        "en": "✅ Thanks for your support! It helps a lot 🙌",
        "es": "✅ ¡Gracias por tu apoyo! Nos ayuda mucho 🙌",
    }[lang]
    await call.message.answer(thanks)
    await call.answer("OK")


# Регистрация хендлеров
def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, F.text == "/start")
    dp.message.register(set_language, Form.waiting_for_language)
    dp.message.register(ask_age, Form.waiting_for_age)
    dp.message.register(ask_gender, Form.waiting_for_gender)
    dp.message.register(handle_pdf, Form.waiting_for_file, F.document)

    # Одна универсальная кнопка «Я оплатил»
    dp.callback_query.register(cb_paid_any, F.data == "paid_any")
