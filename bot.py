import asyncio
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramRetryAfter

BOT_TOKEN = "your token"  
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BASE_DELAY = 2.5 

async def safe_send_poll(chat_id, *args, **kwargs):
    while True:
        try:
            return await bot.send_poll(chat_id, *args, **kwargs)
        except TelegramRetryAfter as e:
            print(f"Telegram flood limit. Kutilyapti: {e.retry_after} sek.")
            await asyncio.sleep(e.retry_after + 0.5)
        except Exception as ex:
            print(f"Poll xatolik: {ex}")
            break

async def safe_send_message(chat_id, *args, **kwargs):
    while True:
        try:
            return await bot.send_message(chat_id, *args, **kwargs)
        except TelegramRetryAfter as e:
            print(f"Telegram flood limit. Kutilyapti: {e.retry_after} sek.")
            await asyncio.sleep(e.retry_after + 0.5)
        except Exception as ex:
            print(f"Message xatolik: {ex}")
            break

async def safe_send_photo(chat_id, *args, **kwargs):
    while True:
        try:
            return await bot.send_photo(chat_id, *args, **kwargs)
        except TelegramRetryAfter as e:
            print(f"Telegram flood limit. Kutilyapti: {e.retry_after} sek.")
            await asyncio.sleep(e.retry_after + 0.5)
        except Exception as ex:
            print(f"Photo xatolik: {ex}")
            break

@dp.message()
async def send_range(message: Message):
    if message.text and message.text.startswith('/range_'):
        if message.chat.type not in ["group", "supergroup"]:
            await message.answer("Bu komanda faqat guruhda ishlaydi!")
            return

        try:
            _, start, end = message.text.split('_')
            start, end = int(start), int(end)
            assert start <= end
        except Exception:
            await message.answer("To‘g‘ri format: /range_1_113")
            return

        await safe_send_message(message.chat.id, f"{start} dan {end} gacha bo‘lgan biletlar yuboriladi. Bu vaqt oladi.")
        await asyncio.sleep(BASE_DELAY)

        for bilet_number in range(start, end + 1):
            file_path = os.path.join("updated_json", f"{bilet_number}_bilet.json")
            if not os.path.exists(file_path):
                await safe_send_message(message.chat.id, f"{bilet_number}-bilet topilmadi, o‘tkazib yuborildi.")
                await asyncio.sleep(BASE_DELAY)
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                ticket = json.load(f)

            await safe_send_message(message.chat.id, f"{bilet_number}-bilet")
            await asyncio.sleep(BASE_DELAY)

            for question in ticket:
                answers = question['answers']
                # (correct) qayerda ekanini topamiz
                correct_idx = None
                for i, a in enumerate(answers):
                    if "(correct)" in a:
                        correct_idx = i
                        break
                answers_clean = [a.replace(" (correct)", "").replace("(correct)", "") for a in answers]
                variantlar_uzun = any(len(a) > 100 for a in answers_clean)
                if variantlar_uzun:
                    poll_options = [f"F{i+1}" for i in range(len(answers_clean))]
                    # pollda correct F1/F2/... bo'ladi, mapping 0->0, 1->1
                    poll_correct_idx = correct_idx
                else:
                    poll_options = answers_clean  # F1: ... F2: ... tarzida
                    poll_correct_idx = correct_idx
                savol_matni = question['question']
                image_path = question['image']

                if image_path:
                    if variantlar_uzun:
                        caption = f"{savol_matni}\n" + "\n".join(answers_clean)
                    else:
                        caption = savol_matni
                    try:
                        await safe_send_photo(
                            message.chat.id,
                            photo=FSInputFile(image_path),
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        await safe_send_message(
                            message.chat.id,
                            f"(Rasm yuborishda xatolik: {e})\n{caption}"
                        )
                    await asyncio.sleep(BASE_DELAY)
                    await safe_send_poll(
                        message.chat.id,
                        question="Javoblardan birini tanlang:",
                        options=poll_options,
                        is_anonymous=False,
                        type="quiz",
                        correct_option_id=poll_correct_idx if poll_correct_idx is not None else 0
                    )
                    await asyncio.sleep(BASE_DELAY)
                else:
                    if variantlar_uzun:
                        text = f"{savol_matni}\n" + "\n".join(answers_clean)
                    else:
                        text = savol_matni
                    await safe_send_message(message.chat.id, text)
                    await asyncio.sleep(BASE_DELAY)
                    await safe_send_poll(
                        message.chat.id,
                        question="Javoblardan birini tanlang:",
                        options=poll_options,
                        is_anonymous=False,
                        type="quiz",
                        correct_option_id=poll_correct_idx if poll_correct_idx is not None else 0
                    )
                    await asyncio.sleep(BASE_DELAY)

            await safe_send_message(message.chat.id, f"{bilet_number}-bilet yakunlandi ✅")
            await asyncio.sleep(BASE_DELAY)
        return

    # /bilet_1 va boshqa komandalar uchun xuddi shu mantikda ishlatishingiz mumkin

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)
