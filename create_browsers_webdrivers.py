from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time


def create_firefox():
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.set_preference("general.useragent.override",
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0")

    service = Service(executable_path=f"geckodriver")
    driver = webdriver.Firefox(options=options, service=service)
    return driver


def create_chrome():
    # from selenium import webdriver
    import undetected_chromedriver as webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    service = Service(executable_path=f"geckodriver")
    options.add_argument("--incognito")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-images")
    options.add_argument("--use_subprocess")
    driver = webdriver.Chrome(options=options)
    return driver