from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import re

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
    playwright_page.mouse.wheel(0, 5000)
    playwright_page.wait_for_timeout(5000)
    # tuits = playwright_page.locator('[data-testid="tweet"]')
    # tuits = playwright_page.locator('[data-testid="cellInnerDiv"]')
    # for tuits in playwright_page.locator('div.css-175oi2r.r-1adg3ll.r-1ny4l3l').all():
      #  text += tuits.inner_text()
    # tuits = playwright_page.get_by_role('Region', name='Your Home Timeline')
    tuits = playwright_page.get_by_label('Timeline: Your Home Timeline')
    text = tuits.inner_html()
    info = tuits.inner_text()
    list_text = info.split('\n')
    cleaned_list_text = []
    flag = False
    for indexing in range(len(list_text)):
        print(list_text[indexing])
        print(list_text[indexing].startswith('@'))
        print(list_text[indexing] == '·')
        if list_text[indexing].startswith('@') and list_text[indexing+1] == '·':
            print('FLAG SET TO TRUE -------------- ')
            flag = True
            indexing += 3
            continue
        while flag == True:
            cleaned_list_text.append(list_text[indexing])
            # TEMPORAL CODE JUST TO PREVENT IT FROM ADDING EVERYTHING TO THE LIST, DELETE TOMORROW
            if list_text[indexing].startswith('@') and list_text[indexing+1] == '·':
                break
    print(cleaned_list_text)
    with open('html.txt', 'w', encoding='utf-8') as file:
        file.write(text)
    with open('text.txt', 'w', encoding='utf-8') as file:
        file.write(info)
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