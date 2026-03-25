import re
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv
import os
import requests

load_dotenv()

username = os.getenv("ILPOST_USER")
password = os.getenv("ILPOST_PASSWORD")


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://abbonati.ilpost.it/mio-account/")
    

    # Close the cookies notice
    cookie_btn = page.get_by_role("button", name="Accetta e chiudi")
    cookie_btn.wait_for(state="visible", timeout=10000)
    cookie_btn.click()

    page.wait_for_timeout(2000)  # waits 2 seconds

    cookie_btn = page.get_by_role("button", name="Accetta e chiudi")
    cookie_btn.wait_for(state="visible", timeout=10000)
    cookie_btn.click()

    # Login with email and password
    page.get_by_role("textbox", name="Indirizzo email").click()
    page.get_by_role("textbox", name="Indirizzo email").fill(username)
    page.get_by_role("button", name="Continua").click()
    page.get_by_placeholder("Inserisci una password").fill(password)
    page.get_by_role("button", name="Accedi").click()

    # Go to Morning page
    page.wait_for_timeout(2000)  # waits 2 seconds
    page.goto("https://www.ilpost.it/podcasts/morning")

    # Get most recent item
    episode_url = page.locator("[class^='_episode-item_'] a").first.get_attribute("href")

    page.goto(episode_url)
    page.wait_for_timeout(2000)  # waits 2 seconds

    episode_url = page.locator("audio").get_attribute("src")
    print(episode_url)
    
    # Check if this episode has been downloaded already
    if os.path.isfile("lastMorning.txt"):
        with open("lastMorning.txt", "r") as f:
            lastMorning = f.read()
        if lastMorning == episode_url:
            return None

    with open("lastMorning.txt", "w") as f:
        f.write(episode_url)

    response = requests.get(episode_url)
    with open("Morning.mp3", "wb") as f:
        f.write(response.content)


    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
