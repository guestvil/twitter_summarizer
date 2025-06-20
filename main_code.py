from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import re
import json

def get_credentials():
    load_dotenv()
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    return username, password

def login(playwright_page: Page, twitter_url: str, username: str, password: str):
    '''Playwright page: an instance of playwright page
    twitter_url: the twitter landing page
    username: tw username
    password: tw password

    Returns: nothing, it just makes playwright log into twitter'''
    playwright_page.goto(twitter_url)
    playwright_page.get_by_role('link', name='Sign in').click()
    playwright_page.get_by_role('textbox').fill(username)
    playwright_page.get_by_role('button', name='Next').click()
    playwright_page.pause()
    playwright_page.get_by_role('textbox', name='Password').fill(password)
    playwright_page.get_by_role('button', name='Log in').click()
    return None


def get_twitter_info(playwright_page: Page, twwets_number: int):
    '''playwright_page: an instance of a playwright page
    twwets_number: int, the number of tweets it's desired to scann
    
    Returns: a list of dictionaries, each:
        {username: @username
        name: name
        tweet: the_tweet_here}'''
    twitter_sections = ['For you', 'Following']
    raw_info = {}
    twitter_info = []
    for section in twitter_sections:
        playwright_page.get_by_role('tab', name=section).click()
        scroll_counter = 0
        tweets = []
        # We will scroll until the desired amount of twweets is reached. Next method measures the length of the list containing the locator that matches all tweets
        while len(tweets) <= twwets_number:
            print('Detected number of tweets:', len(playwright_page.locator('[data-testid="cellInnerDiv"]').all()))
            # Open the twwets that are not completely displayed in the feed
            # First create a locator to limit the search of 'Show more' to the feed, as there are other instances elsewhere in the page
            feed_locator = playwright_page.get_by_label('Home Timeline')
            # if feed_locator.get_by_role('link', name='Show more').is_visible():
            # This method is better than using .is_visible(), as it is strict-mode violation proof: 
            for clickable_tweets in feed_locator.get_by_role('link', name='Show more').all():
                print('Show more tweet detected, opening...------------- \n')
                clickable_tweets.click()
                # When opened in a single window there can be  more than one instace of tweets because of the replies, so this store only the first one -the main tweet
                print('Long tweet added:________________ \n', playwright_page.locator('[data-testid="cellInnerDiv"]').first.inner_text())
                tweets.append(playwright_page.locator('[data-testid="cellInnerDiv"]').first.inner_text())
                # Go back to the main feed, either by clicking 'close' for images or 'back' for text-only tweets
                if playwright_page.get_by_role('button', name='Close').is_visible():
                    playwright_page.get_by_role('button', name='Close').click()
                if playwright_page.get_by_role('button', name='Back').is_visible():
                    playwright_page.get_by_role('button', name='Back').click()
            # Add the new loaded tweets to the list
            for each_tweet in playwright_page.locator('[data-testid="cellInnerDiv"]').all():
                # Check that this tweet is not alrady stored in the list, as scrolling can change the tweet's index returned by the locator. The "any" function will return true if the comparison in the generator returns True for any element
                if any(each_tweet.inner_text()[:30] == sliced_tweet[:30] for sliced_tweet in tweets):
                    print('This tweet has been excluded: \n', each_tweet.inner_text())
                    continue
                tweets.append(each_tweet.inner_text())
            print('----------------- END_OF_A_SINGLE_BACH_OF_TWEETS----------------\n')
            # Scroll 5000 pixels if the number of tweets is not met yet
            playwright_page.mouse.wheel(0, 5000)
            playwright_page.wait_for_timeout(5000)
            # Hard-coded limit to avoid an infinite cycle
            if scroll_counter > 20:
                break
        # Add all the tweets from the section into the list
        raw_info[section] = tweets

        # tuits = playwright_page.get_by_label('Timeline: Your Home Timeline')
        # info = tuits.inner_text()
        # list_text = info.split('\n')
        # twitter_info.append(list_text)
        with open('raw_info.json', 'w', encoding='utf-8') as file:
            json.dump(raw_info, file, ensure_ascii=False, indent=4)
    # return twitter_info
    print(raw_info)
    return raw_info


def clean_information(list_of_tuits: list):
    cleaned_list_text = []  
    flag = False
    for indexing in range(len(list_of_tuits)):
        print(list_of_tuits[indexing])
        print(list_of_tuits[indexing].startswith('@'))
        print(list_of_tuits[indexing] == '·')
        if list_of_tuits[indexing].startswith('@') and list_of_tuits[indexing+1] == '·':
            print('FLAG SET TO TRUE -------------- ')
            flag = True
            indexing += 3
            continue
        while flag == True:
            cleaned_list_text.append(list_of_tuits[indexing])
            # TEMPORAL CODE JUST TO PREVENT IT FROM ADDING EVERYTHING TO THE LIST, DELETE TOMORROW
            if list_of_tuits[indexing].startswith('@') and list_of_tuits[indexing+1] == '·':
                break
    print(cleaned_list_text)
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
        twitter_info = get_twitter_info(playwright_page=page, twwets_number=20)
    print(twitter_info)
    return None


if __name__=='__main__':
    main()