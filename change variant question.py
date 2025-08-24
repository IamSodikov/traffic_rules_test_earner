import json
import re
import os

# JSON fayllar saqlangan papka
folder = "updated_json"

# 1 dan 113 gacha fayllarni ko‘rib chiqamiz
for i in range(1, 114):
    filename = os.path.join(folder, f"{i}_bilet.json")

    if not os.path.exists(filename):
        print(f"❌ Fayl topilmadi: {filename}")
        continue

    # Faylni o‘qib olish
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ {filename} faylida xatolik: {e}")
            continue

    # Har bir savolni ko‘rib chiqamiz
    for item in data:
        new_answers = []
        for idx, answer in enumerate(item['answers']):
            label = f"F{idx + 1}"

            # Boshlanishdagi F1, A), B., A ) kabi belgilarning har qanday kombinatsiyasini tozalaymiz
            cleaned = re.sub(r'^(F\d+|[A-EА-Е])[\.\:\)\s]+', '', answer).strip()

            # Yangi formatda belgilaymiz
            updated_answer = f"{label}: {cleaned}"
            new_answers.append(updated_answer)

        item['answers'] = new_answers

    # Yangilangan ma'lumotni o‘z joyiga yozib qo‘yamiz
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ Yangilandi: {filename}")
