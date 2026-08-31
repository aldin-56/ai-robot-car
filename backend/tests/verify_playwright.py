import os
from playwright.sync_api import sync_playwright

os.makedirs("/home/jules/verification", exist_ok=True)

def run_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Landing Page
        page.goto("http://127.0.0.1:5173")
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/jules/verification/landing_page.png")

        # 2. Tools Registry Page
        page.click("text=AI Tools Registry")
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/jules/verification/tools_registry.png")

        # 3. New Goal Creator Page
        page.click("text=Create Goal")
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/jules/verification/task_creator.png")

        browser.close()

if __name__ == "__main__":
    run_playwright()
