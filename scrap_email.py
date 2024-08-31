from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re

options = Options()
options.add_argument("--disable-notifications")
driver = webdriver.Chrome(options=options)

driver.get('https://www.foodpanda.pk/city/multan')
page_source = driver.page_source

email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
emails = re.findall(email_pattern, page_source)
unique_emails = set(emails)

for email in unique_emails:
    print(email)

driver.quit()
