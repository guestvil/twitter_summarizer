from playwright.sync_api import sync_playwright, Page
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import json
import markdown2
from fpdf import FPDF


def get_credentials():
    load_dotenv()
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    google_key = os.getenv('GOOGLE_KEY')
    return username, password, google_key


def login(playwright_page: Page, twitter_url: str, username: str, password: str):
    '''Playwright page: an instance of playwright page
    twitter_url: the twitter landing page
    username: tw username
    password: tw password

    Returns: nothing, it just makes playwright log into twitter'''
    print('Login into X...')
    playwright_page.goto(twitter_url)
    playwright_page.get_by_role('link', name='Sign in').click()
    playwright_page.get_by_role('textbox').fill(username)
    playwright_page.get_by_role('button', name='Next').click()
    # If you hit X servers to often it will ask you to solve a captcha, this is easily solvable but I'm not getting paid for this
    # playwright_page.pause()
    playwright_page.get_by_role('textbox', name='Password').fill(password)
    playwright_page.get_by_role('button', name='Log in').click()
    return None


def get_twitter_info(playwright_page: Page, twwets_number: int):
    '''playwright_page: an instance of a playwright page
    twwets_number: int, the number of tweets it's desired to scann
    
    Returns: a dictionary with 2 keys, each contaning the corresponding tweets from the feed: 
    { 
        "For you": [this is a tweet, this is another tweet]
        "Following:" ["this is a tweet", "this is another tweet"]    
    }'''
    print('Getting individual tweets information...')
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
                clickable_tweets.click()
                # When opened in a single window there can be  more than one instace of tweets because of the replies, so this store only the first one -the main tweet
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
                    print('This tweet was found twice \n', each_tweet.inner_text(), '\n')
                    continue
                tweets.append(each_tweet.inner_text())
                print('Tweet added: \n', each_tweet.inner_text(), '\n')
            # Scroll 5000 pixels if the number of tweets is not met yet
            playwright_page.mouse.wheel(0, 5000)
            playwright_page.wait_for_timeout(5000)
            # Hard-coded limit to avoid an infinite cycle
            if scroll_counter > 20:
                break
        # Add all the tweets from the section into the list
        raw_info[section] = tweets
        # Store the info as a json file in case testing is needed without launching playwright
        with open('raw_info.json', 'w', encoding='utf-8') as file:
            json.dump(raw_info, file, ensure_ascii=False, indent=4)
    # return twitter_info
    return raw_info


def temporal_dictionary(json_file_path: str):
    '''Temporal function that will use the json file store locally and convert it back to a python dictionary to use it while developing the code. 
    I don't want to run the code that often so that twitter dectects it and starts placing a captcha''' 
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file) 
    return data


def clean_information(dict_of_tuits: dict):
    '''Receives: a dictionary with 2 keys, each contaning the corresponding tweets from the feed: 
    { 
        "For you": [this is a tweet, this is another tweet]
        "Following:" ["this is a tweet", "this is another tweet"]    
    }
    
    Outputs: a dictonary in the form: 
    {'For you': [
                {'name': 'User name',
                'handle': '@some_handle',
                'content': 'this is tweet'},
                
                {'name': 'another user',
                'handle': '@another_user',
                'content': 'this is another tweet}
                ...],

    'Following': [{'name': 'User name',
                'handle': '@some_handle',
                'content': 'this is tweet'},

                {'name': 'another user',
                'handle': '@another_user',
                'content': 'this is another tweet}
                  ...]'''
    print('\n Creating dictionary for LLM... \n')
    final_dictionary = {}
    flag = False
    # This loop iterates over each of the list of strings, with each individual string being a tweet
    for key, list_of_string_tuits in dict_of_tuits.items():
        final_tweet = []
        # Iterates over each individual string
        for each_string in list_of_string_tuits:
            # From each string a list is obtained unsing the \n as element separator
            single_tuit_list = each_string.split('\n')
            # This dictonary will store the name, username and text from the tweet, to be later added to a list.
            individual_tweet_dict = {}
            individual_tweet_content = []
            for indexing in range(len(single_tuit_list)):
                if single_tuit_list[indexing] == '':
                    continue
                # print(single_tuit_list[indexing])
                # print(single_tuit_list[indexing].startswith('@'))
                # print(single_tuit_list[indexing] == '·')
                # An individual tweet can be identified when there is an @ followed by a dot Why not use simply the second index? Because in reposts the second index IS NOT the username
                if single_tuit_list[indexing].startswith('@') and single_tuit_list[indexing+1] == '·':
                    # This marks the begining of the place in which we begin to store information and update the flag
                    flag = True
                    # The curren indexing is the handle and the previous one will be the nanme
                    individual_tweet_dict['name'] = single_tuit_list[indexing-1]
                    individual_tweet_dict['handle'] = single_tuit_list[indexing]
                    # From the handle index, the tweet's content will be 3 indexes ahead
                    indexing += 3
                    # The tweet's content will be first stored as a list of strings, since some tweet's contents can have '\n' inside of them and hence concatenating and deleting some strings will be necessary
                    individual_tweet_content.append(single_tuit_list[indexing])
                    # Continue to the next item as the current one is already stored
                    continue
                # After the flag has been set to TRUE all is stored , since some tweet's contents can have '\n' inside of them
                if flag == True:
                    # Tweet ending is signaled by a string with only numbers and no longer than 4 characters, as reply or retweets counts larger than 1000 will be abreviated to 1K and longer or 1M for counts in the millions
                    # Also, the index -4 elements should be different from 'Quote', as in many instances the quoted tweet will display its time as a single number that fulfills the aformentioned condition
                    if len(single_tuit_list[indexing])<=4 and single_tuit_list[indexing][0].isdigit() == True and single_tuit_list[indexing-4] != 'Quote':
                        tweet_full_text = ' '.join(individual_tweet_content)
                        individual_tweet_dict['content'] = tweet_full_text
                        flag = False
                        continue
                    individual_tweet_content.append(single_tuit_list[indexing])
            if individual_tweet_dict != {}:
                final_tweet.append(individual_tweet_dict)
        final_dictionary[key] = final_tweet
    return final_dictionary


def llm_call(twitter_dict: dict, system_instruction: str, key:str):
    '''Recieves the dictionary from clean information and parses it to google's LLM to create a summary in JSON format'''
    print('\n Calling LLM... \n')
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        config= types.GenerateContentConfig(
            system_instruction = system_instruction
        ),
        contents = twitter_dict)
    return response.text


def get_pdf_report(llm_output_markdown:str):
    # First transform the pure markdown formatting into html
    print('\n Creating PDF report... \n')
    html = markdown2.markdown(llm_output_markdown)
    # Then export the code as a formatted pdf
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(html)
    pdf.output('x_summary.pdf')
    return None


def send_report(pdf_path: str):
    print('\n Printing report... \n')
    os.system(f'lpr {pdf_path}')
    return None


def main():
    url = 'https://x.com'
    x_username, x_password, google_key = get_credentials()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        login(playwright_page=page, twitter_url=url, username=x_username, password=x_password)
        twitter_info = get_twitter_info(playwright_page=page, twwets_number=30)
    # Temporal json file to use instead of twitter info, to test the function without launching playwright 
    # twitter_info = temporal_dictionary('raw_info.json')
    cleaned_info = clean_information(twitter_info)
    # Retrieve the system instructions to be passed to the LLM
    with open('system_instructions.txt', 'r', encoding='utf-8') as file:
        system_instrucions = file.read()
    # Transform the dictionary into a Json formatted string that can be sent to the LLM
    cleaned_info_str = json.dumps(cleaned_info, ensure_ascii=False, indent=4)
    # Call the LLM and get the summary
    llm_output = llm_call(twitter_dict=cleaned_info_str, system_instruction=system_instrucions, key=google_key)
    print('LLM output: \n', llm_output)
    # Transform the summary into a PDF file
    get_pdf_report(llm_output_markdown = llm_output)
    # print the PDF file
    send_report('x_summary.pdf')
    return None


if __name__=='__main__':
    main()