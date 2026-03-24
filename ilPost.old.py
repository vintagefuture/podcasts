from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import re, subprocess, os.path, time
from datetime import datetime

def get_podcast_mp3_url():
    # Setup Chrome options with logging enabled
    chrome_options = Options()
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")

    # Enable performance logging to capture network requests
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # Connect to the Docker Selenium container
    driver = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=chrome_options
    )

    try:
        send_to_log("Navigating to login page...")
        driver.get("https://abbonati.ilpost.it/mio-account")
        send_to_log("Accepting cookies")
        driver.find_element_by_xpath('//button[text()="Accetta e chiudi"]').click()



        send_to_log("Navigating to Il Post podcast page...")
        driver.get("https://www.ilpost.it/podcasts/morning/")

        wait = WebDriverWait(driver, 15)

        send_to_log("Searching for audio elements and MP3 URLs...")
        mp3_urls = []

        # Look for any URLs containing MP3 in the page source
        send_to_log("Searching page source for MP3 URLs...")
        page_source = driver.page_source

        # Simple pattern to find URLs ending with .mp3
        mp3_pattern = r'https?://[^\s"\'<>]+\.mp3'
        matches = re.findall(mp3_pattern, page_source, re.IGNORECASE)

        if matches:
            first_mp3_url = matches[0]
            send_to_log(f"\n=== FOUND MP3 URL ===")

            # Check if this episode has been downloaded already
            if os.path.isfile("/home/nedo/lastMorning.txt"):
                with open("lastMorning.txt", "r") as f:
                    lastMorning = f.read()
                if lastMorning == first_mp3_url:
                    return None

            send_to_log(first_mp3_url)
            with open("lastMorning.txt", "w") as f:
                f.write(first_mp3_url)
            subprocess.run(["/usr/bin/wget", "-q", first_mp3_url, "-O", "./podcasts/Morning.mp3"])
            return first_mp3_url
        else:
            send_to_log("No MP3 URLs found in page source")
            return None

    except Exception as e:
        send_to_log(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

def send_to_log(string):
    print(f'{datetime.now()} {string}')

if __name__ == "__main__":
    close_time = time.time() + 60 * 60  # 1 hour later
    while time.time() < close_time:
        result = get_podcast_mp3_url()
        if result:
            send_to_log(f"Found a new episode: {result}")
            subprocess.run([
                'curl', 
                '-u', 'nedo:rutles',
                '-d', "New episode of Morning is ready",
                'https://ntfy.542646.xyz/newPodcast'
            ], capture_output=True, text=True)
            break
        else:
            send_to_log("No new episode found yet, trying again...")
    else: # This 'else' block executes if the while loop finishes without a 'break'
        send_to_log("Not found a new episode, giving up.")
