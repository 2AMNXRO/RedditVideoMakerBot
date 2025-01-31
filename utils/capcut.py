import json
import time
import os

from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import asyncio

from bs4 import BeautifulSoup

from utils import settings

from datetime import datetime, timedelta

# Utils
def check_similarity(video_title, text):
        video_title_words = set(video_title.lower().split())
        text_words = set(text.lower().split())

        common_words = text_words.intersection(video_title_words)

        return len(common_words) / len(text_words) >= 0.6

COOKIE_FILE_PATH = "./utils/capcut_data/login_data.json"

def load_cookies(context):
    os.makedirs(os.path.dirname(COOKIE_FILE_PATH), exist_ok=True)
    if os.path.exists(COOKIE_FILE_PATH):
        with open(COOKIE_FILE_PATH, "r") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict) and "cookies" in data and "timestamp" in data:
                    expiration_date = datetime.fromtimestamp(data["timestamp"]) + timedelta(days=3)
                    if datetime.now() < expiration_date:
                        context.add_cookies(data["cookies"])
                        print("Logged in with cookies data.")
                        return True
                    else:
                        print("Cookies expired, redirecting to login page.")
            except json.JSONDecodeError:
                pass
    else:
        os.makedirs(os.path.dirname(COOKIE_FILE_PATH), exist_ok=True)
        with open(COOKIE_FILE_PATH, "w") as file:
            json.dump({"cookies": [], "timestamp": 0}, file, indent=4)
    return False

def save_cookies(context):
    cookies = context.cookies()
    data = {
        "cookies": cookies,
        "timestamp": time.time()
    }
    os.makedirs(os.path.dirname(COOKIE_FILE_PATH), exist_ok=True)
    with open(COOKIE_FILE_PATH, "w") as file:
        json.dump(data, file, indent=4)
    print("Login data saved, will last 3 days.")

# Runthrough
def generate_captions(file_path, title):
    with sync_playwright() as playwright:
        
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        page = context.new_page()
        page.goto("https://www.capcut.com/")
        email = settings.config["capcut"]["email"]
        password = settings.config["capcut"]["password"]
        subtitle_language = settings.config["capcut"]["capcut_caption_language"]
        video_title = title.lower()
        video_file_name = title.replace(" ", "_")

        if not load_cookies(context):
            email = settings.config["capcut"]["email"]
            password = settings.config["capcut"]["password"]

            print("Logging in")
            page.goto("https://www.capcut.com/login")

            page.fill("//input[@class='lv-input lv-input-size-default lv_sign_in_panel_wide-input']", email)
            page.click("//span[normalize-space()='Continue']")
            page.fill("//input[@type='password']", password)
            page.click("//span[contains(text(),'Sign in')]")
            page.wait_for_timeout(10000)
            save_cookies(context)
        try:
            page.click("//div[@class='skip--kncMC']", timeout=3000)
        except:
            pass

        page.goto(f"https://www.capcut.com/my-cloud/{str(settings.config['capcut']['cloud_id'])}?start_tab=video&enter_from=page_header&from_page=work_space&tab=all")

        try:
            page.click("//span[contains(text(),'Decline all')]", timeout=3000)
        except:
            pass

        if page.is_visible("//div[@class='guide-modal-close-icon']"):
            page.click("//div[@class='guide-modal-close-icon']")

        print("Trying to remove old video")
        removing_videos = True

        while removing_videos:
            try:
                items = page.locator("//div[@data-selectable-item-id]")
                count = items.count()
                print(f"Found {count} videos")

                if count > 0:
                    for i in range(count):
                        item = items.nth(0)

                        if item.is_visible():
                            item.hover()
                            page.click("//*[@width='16']")
                            page.click("//div[contains(text(),'Move to Trash')]")
                            page.click("//span[contains(text(),'Confirm')]")
                            time.sleep(2)
                else:
                    removing_videos = False
            except:
                removing_videos = False
                pass

        page.goto("https://www.capcut.com/editor?enter_from=create_new&current_page=landing_page&from_page=work_space&start_tab=video&__action_from=my_draft&position=my_draft&scenario=youtube_ads&scale=9%3A16")

        print("Uploading video")
        if page.is_visible("//div[@class='guide-close-icon-f8J9FZ']//*[name()='svg']"):
            page.click("//div[@class='guide-close-icon-f8J9FZ']//*[name()='svg']")

        if page.is_visible("//div[@class='guide-placeholder-before-OsTdXF']"):
            page.click("//div[@class='guide-placeholder-before-OsTdXF']")

        if page.is_visible("//div[@class='guide-close-icon-f8J9FZ']//*[name()='svg']"):
            page.click("//div[@class='guide-close-icon-f8J9FZ']//*[name()='svg']")

        if page.is_visible("//div[@class='guide-close-icon-Gtxdju']//*[name()='svg']"):
            page.click("//div[@class='guide-close-icon-Gtxdju']//*[name()='svg']")

        if page.is_visible("//div[@class='guide-close-icon-Gtxdju']"):
            page.click("//div[@class='guide-close-icon-Gtxdju']")

        if page.is_visible("//div[@class='guide-close-icon-Gtxdju'][1]"):
            page.click("//div[@class='guide-close-icon-Gtxdju'][1]")

        if page.is_visible("//div[@class='guide-close-icon-OwPlMC']"):
            page.click("//div[@class='guide-close-icon-OwPlMC']")

        while True:
            try:
                page.click("div[class^='guide-close-icon-']", timeout=1000)
            except:
                break


        page.set_input_files("(//input[@type='file'])[1]", file_path)

        page.wait_for_timeout(1000)

        page.evaluate(""" 
            setInterval(() => {
                const messageBox = document.querySelector('.lv-trigger-position-right');
                if (messageBox) {
                    const firstDiv = messageBox.querySelector('div');
                    if (firstDiv) {
                        const secondDiv = firstDiv.querySelector('div');
                        if (secondDiv) {
                            secondDiv.click();
                        }
                    }
                }
            }, 2000);
        """)

        time.sleep(2)

        uploading = False
        progress_upload = False
        transcoding = False
        while not (uploading and progress_upload and transcoding):
            try:
                if page.locator("//div[@class='lv-progress-circle-wrapper']").is_visible():
                    progress_upload = False
                else:
                    progress_upload = True
                    if page.locator("//div[contains(text(),'Uploading')]").is_visible():
                        uploading = False
                    else:
                        uploading = True
                        if page.locator("//div[contains(text(),'Transcoding')]").is_visible():
                            transcoding = False
                        else:
                            page.locator('.header-title-bar-render-compoents [data-id="titlebarSaveStatus"]').hover()
                            page.wait_for_timeout(500)
                            page.mouse.move(0, 0)
                            transcoding = True
                            print("Video upload complete")
            except:
                pass
            time.sleep(10)

        page.click("//div[@class='tools-YTEuDt']", timeout=3000000)
        page.click("(//li[@role='option'])[5]")

        time.sleep(5)

        page.click("//div[@id='siderMenuCaption']//div[@class='menu-inner-box']//*[name()='svg']")

        page.wait_for_timeout(2000)

        try:
            page.click("//div[@id='text-intelligent-detect-text']", timeout=8000)
        except:
            pass

        video_ready = False
        while not video_ready:
            page.wait_for_timeout(2000)
            page.evaluate(f""" 
                const inputElement = document.querySelector(
                    '.text-intelligent-item.text-intelligent-detect.text-intelligent-item__active input'
                );
                inputElement.click();
                setTimeout(() => {{
                    const popupElement = document.getElementById('lv-select-popup-2');
                    if (popupElement) {{
                        const targetLi = Array.from(popupElement.querySelectorAll('li')).find(li => {{
                            const signDiv = li.querySelector('.group-content-sign');
                            return signDiv && signDiv.textContent.trim() === '{subtitle_language.upper()}';
                        }});
                        if (targetLi) {{
                            targetLi.click();
                        }}
                    }}
                }}, 200);
            """)
            page.wait_for_timeout(500)
            page.click("//footer[@class='active-panel']//span[contains(text(),'Generate')]")
            try:
                if page.locator("//div[@class='lv-message lv-message-error']").is_visible():
                    video_ready = False
                else:
                    video_ready = True
            except:
                pass

            time.sleep(10)

        print("Changing settings")

        page.click("//div[@id='workbench-tool-bar-toolbarTextPreset']")

        time.sleep(10)

        page.click(
            "//div[contains(@class, 'lv-tabs-header-nav-horizontal') and contains(@class, 'lv-tabs-header-nav-top')]"
            "//div[contains(@class, 'lv-tabs-header-wrapper')]"
            "//div[contains(@class, 'lv-tabs-header-title') and not(contains(@class, 'lv-tabs-header-title-active'))]"
            "[.//span[contains(text(), 'Templates')]]"
        )

        time.sleep(1)

        page.click(f"(//img[@class='image-H3DQKC'])[{str(settings.config['capcut']['preset_number'])}]")

        time.sleep(2)

        page.click("//div[@id='workbench-tool-bar-toolbarTextBasic']//div[@class='tool-bar-icon']//*[name()='svg']")

        time.sleep(2)

        page.fill("//input[@value='-672']", "0")

        time.sleep(1)

        page.fill("//input[@value='100' and @aria-valuemax='500']", "150")

        time.sleep(2)

        print("Cleaning up title captions")

        for _ in range(10):
            element = page.query_selector("//div[@class='subtitle-list-content']/section[1]")
            html_code = page.evaluate("element => element.innerHTML", element)
            soup = BeautifulSoup(html_code, 'html.parser')
            textarea = soup.find('textarea', {'class': 'lv-textarea'})
            text = textarea.text.lower()

            if check_similarity(video_title.lower(), text.lower()):
                page.click("//section[@class='subtitle-list-item']")
                page.click("//button[@class='lv-btn lv-btn-text lv-btn-size-default lv-btn-shape-square']//*[name()='svg']")
            else:
                break

        print("Exporting video")

        page.click("//div[contains(@data-id,'titlebarExport')]//div[contains(@style,'position: relative;')]")

        visible_button = page.locator("//div[contains(text(), 'Download')]").first
        visible_button.click()

        page.fill("//input[@id='form-video_name_input']", video_file_name )

        page.click("//span[contains(text(),'720p')]")

        page.click("//span[contains(text(),'1080p')]")

        page.click("//span[contains(text(),'Recommended quality')]")

        page.click("//li[contains(text(),'High quality')]")

        page.click("//span[contains(text(),'30fps')]")

        page.click("//li[contains(text(),'60fps')]")

        time.sleep(2)

        page.click("//button[@id='export-confirm-button']")
        print("Waiting for video to export")

        time.sleep(35)

        with page.expect_download() as download_info:
            print("Downloading exported video...")
            download = download_info.value

        print("Video downloaded, proceeding")

        working_dir_path = os.getcwd()

        os.makedirs(os.path.join(working_dir_path, "capcut_results", "videos"), exist_ok=True)

        final_path = os.path.join(working_dir_path, "capcut_results", "videos", video_file_name + ".mp4")
        download.save_as(final_path)
        browser.close()
