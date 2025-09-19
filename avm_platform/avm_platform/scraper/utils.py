from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    # Add more for better rotation if needed later
]

BROWSERS = ['firefox']

def get_driver(headless=True):
    browser = random.choice(BROWSERS)
    print(f"Selected browser: {browser}")
    ua = random.choice(USER_AGENTS)
    
    if browser == 'firefox':
        options = FirefoxOptions()
        options.headless = headless
        options.set_preference("general.useragent.override", ua)
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    else:
        options = ChromeOptions()
        options.headless = headless
        options.add_argument(f'user-agent={ua}')
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    return driver
