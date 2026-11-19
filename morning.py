import re
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv
from datetime import datetime
import os
import requests
import time
import subprocess

load_dotenv()

username = os.getenv("ILPOST_USER")
password = os.getenv("ILPOST_PASSWORD")

def send_to_log(string):
    print(f'[INFO] "{datetime.now()} {string}"')

def error_to_log(string = None):
    print(f'[ERROR] "{datetime.now()} {string or "An error occurred."}"')

def run(playwright: Playwright) -> bool:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://abbonati.ilpost.it/mio-account/")

    print()
    send_to_log("Starting up...")

    # Close the cookies notice
    try:
        send_to_log("Dismiss cookies window")
        cookie_btn = page.get_by_role("button", name="Accetta e chiudi")
        cookie_btn.wait_for(state="visible", timeout=10000)
        cookie_btn.click()

        page.wait_for_timeout(2000)  # waits 2 seconds

        cookie_btn = page.get_by_role("button", name="Accetta e chiudi")
        cookie_btn.wait_for(state="visible", timeout=10000)
        cookie_btn.click()
        send_to_log("Cookies window closed")
    except:
        error_to_log()

    # Login with email and password
    try:
        send_to_log("Logging in with username and password...")
        page.get_by_role("textbox", name="Indirizzo email").click()
        page.get_by_role("textbox", name="Indirizzo email").fill(username)
        page.get_by_role("button", name="Continua").click()
        page.get_by_placeholder("Inserisci una password").fill(password)
        page.get_by_role("button", name="Accedi").click()
    except:
        error_to_log("Couldn't log in.")
        exit(1)

    # Go to Morning page
    try:
        send_to_log("Browsing to Morning page...")
        page.wait_for_timeout(2000)  # waits 2 seconds
        page.goto("https://www.ilpost.it/podcasts/morning")
    except:
        error_to_log()

    # Get most recent item
    try:
        episode_url = page.locator("[class^='_episode-item_'] a").first.get_attribute("href")
        send_to_log(f"Found most recent episode: {episode_url}")
        page.goto(episode_url)
        page.wait_for_timeout(2000)  # waits 2 seconds

        episode_url = page.locator("audio").get_attribute("src")
        send_to_log(f"Found mp3 url: {episode_url}")
    except:
        error_to_log("Error finding episode url, quitting...")
        exit(1)

    # Check if this episode has been downloaded already
    if os.path.isfile("lastMorning.txt"):
        with open("lastMorning.txt", "r") as f:
            lastMorning = f.read().strip()
        if lastMorning == episode_url:
            send_to_log("This mp3 is not new")
            return False

    send_to_log("New episode found! Downloading...")
    response = requests.get(episode_url)
    response.raise_for_status()

    os.makedirs("podcasts", exist_ok=True)
    with open(os.path.join("podcasts", "Morning.mp3"), "wb") as f:
        f.write(response.content)

    with open("lastMorning.txt", "w") as f:
        f.write(episode_url)
    
    send_to_log("Done!")
    return True

    # ---------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    close_time = time.time() + 60 * 60  # 1 hour
    while time.time() < close_time:
        with sync_playwright() as playwright:
            result = run(playwright)
        if result:
            send_to_log("New episode downloaded, sending notification...")
            subprocess.run([
                'curl',
                '-u', 'nedo:rutles',
                '-d', 'New episode of Morning is ready',
                'https://ntfy.542646.xyz/newPodcast'
            ], capture_output=True, text=True)
            break
        else:
            send_to_log("No new episode found yet, trying again in 5 minutes...")
            time.sleep(300)  # wait 5 minutes before retrying
    else:
        send_to_log("No new episode found after 1 hour, giving up.")
