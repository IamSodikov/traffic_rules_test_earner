from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from action import generate_selector_with_number, is_element_present, swipe_up, generate_question_json, click_first_option
import time
import json

options = UiAutomator2Options()
options.set_capability("platformName", "Android")
options.set_capability("deviceName", "emulator-5554")
options.set_capability("automationName", "UiAutomator2")
options.set_capability("noReset", True)

driver = webdriver.Remote("http://localhost:4723", options=options)
driver.implicitly_wait(10)

# Biletlar oralig‘i
current_number = 1
target_number = 114

# Foydalaniladigan selectorlar
suffixes = ["A", "B", "C", "D", "E", "F"]
image_crop_selector = '//android.widget.ImageView[@resource-id="uz.ali.avto:id/questionImage"]'


while current_number <= target_number:
    print(f"📘 {current_number}-looking for...")

    selector = generate_selector_with_number(current_number)

    while not is_element_present(driver, AppiumBy.ANDROID_UIAUTOMATOR, selector):
        print(f"🔃 Scroll: {current_number} not found")
        swipe_up(driver)
        time.sleep(1)

    try:
        driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, selector).click()
        print(f"➡️  Entered: {selector}")
        time.sleep(1)

        if not is_element_present(driver, AppiumBy.XPATH, '//android.widget.ImageView[@resource-id="uz.ali.avto:id/favaurites"]'):
            print("❌ Test sahifasi ochilmadi")
            driver.back()
            time.sleep(1)
            current_number += 1
            continue

        all_questions = []

        for i in range(1, 11):  # 10 ta savol
            try:
                q_xpath = f'//android.widget.LinearLayout[@content-desc="{i}"]'
                if is_element_present(driver, AppiumBy.XPATH, q_xpath):
                    driver.find_element(AppiumBy.XPATH, q_xpath).click()
                    time.sleep(1)

                    # Har bir savol bo‘yicha ma’lumotlar
                    data = generate_question_json(
                        driver,
                        suffixes=suffixes,
                        crop_selector_for_image=image_crop_selector,
                    )

                    all_questions.append(data)
                    print(f"✅ {i}-savol o‘qildi")
                else:
                    print(f"⚠️ {i}-savol tugmasi topilmadi")

            except Exception as e:
                print(f"❌ {i}-savolda xato: {e}")
                continue

        # Bitta biletga tegishli json faylga yozamiz
        json_file = f"{current_number}-bilet.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=4)

        print(f"💾 Saqlandi: {json_file}")
        driver.back()
        time.sleep(1)
        current_number += 1

    except Exception as e:
        print(f"⚠️  Umumiy xatolik: {e}")
        break

print("🏁 Barcha biletlar to‘liq yakunlandi.")
