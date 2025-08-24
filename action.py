import time
import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.action_builder import ActionBuilder

def parse_bounds(bounds_str: str) -> Tuple[int, int, int, int]:
    parts = bounds_str.replace("[", "").replace("]", ",").split(",")
    return tuple(map(int, parts[:4]))

def is_element_present(driver, by, value) -> bool:
    try:
        driver.find_element(by, value)
        return True
    except NoSuchElementException:
        return False

def swipe_up(driver, duration=800):
    size = driver.get_window_size()
    start_y = int(size['height'] * 0.5)
    end_y = int(size['height'] * 0.2)
    x = int(size['width'] / 2)

    finger = PointerInput(kind="touch", name="finger")
    actions = ActionBuilder(driver, mouse=finger)

    actions.pointer_action.move_to_location(x, start_y)
    actions.pointer_action.pointer_down()
    actions.pointer_action.pause(duration / 1000)
    actions.pointer_action.move_to_location(x, end_y)
    actions.pointer_action.release()
    actions.perform()

def generate_selector_with_number(number: int) -> str:
    return f'new UiSelector().textContains("{number}")'

def click_first_option(driver, suffix="A"):
    try:
        element = driver.find_element(AppiumBy.ID, f"uz.ali.avto:id/answer{suffix}")
        element.click()
        print(f"✅ {suffix} variantga click qilindi.")
        time.sleep(0.5)
    except Exception as e:
        print(f"⚠️ {suffix} variantga click bo‘lmadi: {e}")

def extract_answer_texts_with_correct(driver, suffixes: List[str], screenshot_path: str, target_bgr=(76, 175, 80), tolerance=60) -> Tuple[List[str], Optional[str]]:
    img = cv2.imread(screenshot_path)
    if img is None:
        print(f"❌ {screenshot_path} ni ochib bo‘lmadi")
        return [], None

    lower = np.array([max(c - tolerance, 0) for c in target_bgr])
    upper = np.array([min(c + tolerance, 255) for c in target_bgr])

    answers = []
    correct_suffix = None

    for suffix in suffixes:
        try:
            container = driver.find_element("id", f"uz.ali.avto:id/answer{suffix}")
            text_el = driver.find_element("id", f"uz.ali.avto:id/answerText{suffix}")
            text = text_el.text.strip()

            bounds = container.get_attribute("bounds")
            x1, y1, x2, y2 = parse_bounds(bounds)

            region = img[y1:y2, x1:x2]
            mask = cv2.inRange(region, lower, upper)
            is_correct = cv2.countNonZero(mask) > 0

            if is_correct:
                correct_suffix = suffix

            answers.append((suffix, text))
        except Exception:
            continue

    formatted_answers = []
    for suffix, text in answers:
        if suffix == correct_suffix:
            formatted_answers.append(f"{suffix}) {text} (correct)")
        else:
            formatted_answers.append(f"{suffix}) {text}")

    return formatted_answers, correct_suffix


def generate_question_json(driver, suffixes: List[str], crop_selector_for_image: Optional[str] = None) -> dict:
    question_number_el = driver.find_element(AppiumBy.ID, "uz.ali.avto:id/bilet")
    question_number_text = question_number_el.text.strip()
    try:
        question_number = int(''.join(filter(str.isdigit, question_number_text)))
    except:
        question_number = question_number_text

    question_text = driver.find_element(AppiumBy.ID, "uz.ali.avto:id/questionText").text.strip()

    image_filename = None
    if crop_selector_for_image and is_element_present(driver, "xpath", crop_selector_for_image):
        element = driver.find_element("xpath", crop_selector_for_image)
        x1, y1, x2, y2 = parse_bounds(element.get_attribute("bounds"))
        image_filename = f"question_photos/{question_number}_savol.png"
        image_path = os.path.join(os.getcwd(), image_filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        driver.save_screenshot("full.png")
        full_img = cv2.imread("full.png")
        cropped_img = full_img[y1:y2, x1:x2]
        cv2.imwrite(image_path, cropped_img)

    click_first_option(driver)  # 🔘 A varianti bosiladi

    # ✅ Faqat javoblarni tahlil qilish uchun full.png ishlatiladi
    driver.save_screenshot("full.png")
    answers, _ = extract_answer_texts_with_correct(driver, suffixes, "full.png")

    if os.path.exists("full.png"):
        os.remove("full.png")  # 🧹 Faqat tahlildan keyin o‘chiriladi

    return {
        "question_number": question_number,
        "question": question_text,
        "image": image_filename,
        "answers": answers
    }


