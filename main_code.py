from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

def get_credentials():
    load_dotenv()
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    return username, password

def login(playwright_page: Page, twitter_url: str, username: str, password: str):
    playwright_page.goto(twitter_url)
    playwright_page.get_by_role('link', name='Sign in').click()
    playwright_page.get_by_role('textbox').fill(username)
    playwright_page.get_by_role('button', name='Next').click()
    playwright_page.get_by_role('textbox', name='Password').fill(password)
    playwright_page.get_by_role('button', name='Log in').click()
    return None


def get_twitter_info(playwright_page: Page):
    playwright_page.get_by_role('tab', name='Following').click()
    # tuits = playwright_page.locator('[data-testid="tweet"]')
    tuits = playwright_page.locator('[data-testid="cellInnerDiv"]')
    print(tuits)
    return None


def llm_call():
    return None


def get_pdf_report():
    return None


def send_report():
    return None


def main():
    url = 'https://x.com'
    x_username, x_password = get_credentials()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        login(playwright_page=page, twitter_url=url, username=x_username, password=x_password)
        get_twitter_info(playwright_page=page)
    return None


if __name__=='__main__':
    main()