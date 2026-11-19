import re
from playwright.sync_api import Playwright, sync_playwright, expect
import os
import requests
import time
import subprocess


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    try:
        page.goto("https://www.internazionale.it/podcast/il-mondo-cultura")

        most_recent_episode_url = page.locator('.episode-details').first.locator('a').get_attribute('href')
        page.goto(most_recent_episode_url)

        most_recent_episode_url = page.locator("audio").get_attribute("src")
        print(f"Found mp3 url: {most_recent_episode_url}")

        response = requests.get(most_recent_episode_url)
        response.raise_for_status()

        os.makedirs("podcasts", exist_ok=True)
        with open(os.path.join("podcasts", "IlMondoCultura.mp3"), "wb") as f:
            f.write(response.content)
    except:
        print("Something went wrong")
    

if __name__ == "__main__":
    with sync_playwright() as playwright:
        result = run(playwright)