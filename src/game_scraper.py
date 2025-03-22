import os
import time
import requests
import pandas as pd
import praw
import re
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv() # load keys

# GAME LIST
GAMES = {
    "RPG": {
        "Baldur's Gate 3": "1086940",
        "Elden Ring": "1245620",
        "Cyberpunk 2077": "1091500"
    },
    "Shooter": {
        "Call of Duty: Modern Warfare 3": "2512980",
        "Overwatch 2": "2357570"
    },
    "Survival": {
        "ARK: Survival Evolved": "346110",
        "Palworld": "1623730"
    },
    "Open-World": {
        "Cyberpunk 2077": "1091500"
    },
    "Strategy": {
        "Age of Empires IV": "1466860",
        "Total War: Warhammer III": "1142710"
    },
    "Action": {
        "The Last of Us Part I": "1888930",
        "The Last of Us Part II": None,
        "Death Stranding": "1190460",
        "Red Dead Redemption 2": "1174180",
        "Detroit: Become Human": "1222140",
        "God of War Ragnarok": None 
    },
    "Adventure": {
        "Stray": "1332010",
    },
    "Puzzle": {
        "Inside": "304430",
        "Limbo": "48000",
        "Little Nightmares": "424840",
        "It Takes Two": "1426210"
    }
}
# KEYS
REDDIT_CREDENTIALS = { # Get Reddit credentials
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "user_agent": os.getenv("REDDIT_USER_AGENT")
}
TWITTER_CREDENTIALS = { # Get Twitter credentials
    "bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
    "username": os.getenv("TWITTER_USERNAME")
}
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # Get Youtube credential
# VALIDATION FUNCTIONS
def validate_reddit(): # Make sure reddit credential are valid
    try:
        reddit = praw.Reddit(**REDDIT_CREDENTIALS)
        reddit.user.me()
        return True
    except Exception as e:
        print(f"Reddit API error: {e}")
        return False
def validate_youtube(): # Make sure youtube credential are valid
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        youtube.search().list(q="test", part="snippet", maxResults=1).execute()
        return True
    except Exception as e:
        print(f"YouTube API error: {e}")
        return False
    
def clean_text(text):
    """This function removes extra spaces while preserving new lines correctly."""
    text = text.lower().strip()  # Convert to lowercase
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = re.sub(r"[ \t]+", " ", text)  # Replace multiple spaces/tabs with a single space
    text = re.sub(r"\n\s+", " ", text)  # Remove spaces at the beginning of a new line
    text = re.sub(r'[^a-zA-Z0-9.,!?\'\s]', '', text)  # Remove non-alphanumeric except punctuation
    return text.strip()  # Remove any leading/trailing spaces

# SCRAPING FUNCTIONS
def scrape_reddit(genre, game, directory):
    """This function searches for Reddit reviews for a specific game."""
    try:
        reddit = praw.Reddit(**REDDIT_CREDENTIALS)
        subreddit = reddit.subreddit("gaming")
        posts = subreddit.search(game, limit=50, time_filter="all")
        data = []
        for post in posts:
            time.sleep(3)
            post.comments.replace_more(limit=20)  # Load top-level comments
            for comment in post.comments.list():
                if isinstance(comment, praw.models.MoreComments):  
                    continue  # Skip 'MoreComments' objects
                comment_date = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d')
                comment = clean_text(comment.body)
                data.append([genre, game, comment_date, comment])
        # Save to CSV if data exists ( post.score, comment.score)
        if data:
            df = pd.DataFrame(data, columns=["genre", "game", "commented_date", "comment"])
            df.to_csv(f"{directory}/reddit_comments_{game}.csv", index=False)
            print(f"\tReddit {len(data)} data for {game} saved!")
        else:
            print(f"\tNo Reddit data for {game}.")
    except Exception as e:
        print(f"\tError scraping Reddit for {game}..: {e}")

def scrape_youtube(genre, game, directory):
    """This function searches for YouTube reviews for a specific game."""
    try:
        youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))
        search_request = youtube.search().list(
            q=game,
            part="snippet",
            maxResults=100,  # Search for top 50 videos related to the game
            type="video"
        )
        search_response = search_request.execute()
        all_comments = []
        
        for item in search_response.get("items", []):
            video_id = item["id"].get("videoId")
            
            if not video_id:
                print(f"Skipping video due to missing videoId: {item['snippet']['title']}")
                continue  # Skip if the videoId is missing   
            # try:  # Check if comments are enabled for this video
            #     comments_request = youtube.commentThreads().list(
            #         part="snippet",
            #         videoId=video_id,
            #         textFormat="plainText",
            #         maxResults=1  # Just to check if comments are enabled
            #     ).execute()
            # except Exception as e:
            #     if "commentsDisabled" in str(e):
            #         continue  # Skip this video if comments are disabled
            #     else:
            #         raise
            
            comments = []
            next_page_token = None
            max_comment_count = 100
            while len(comments) < max_comment_count:  # Fetch up to 500 comments for this video
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    order="relevance",
                    maxResults=min(max_comment_count, max_comment_count - len(comments)),  # Fetch remaining comments
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get("items", []):
                    comment_data = item["snippet"]["topLevelComment"]["snippet"]
                    comment_date = datetime.fromisoformat(comment_data["publishedAt"].replace("Z", "+00:00")).strftime('%Y-%m-%d')
                    comment = clean_text(comment_data["textDisplay"])
                    comments.append([
                        genre,
                        game,
                        comment_date,
                        comment,
                    ])
                    if len(comments) >= max_comment_count:
                        break  # Stop when we have enough comments
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break  # No more pages left
            
            # Add to total comments list
            all_comments.extend(comments)
        
        # Save data if comments exist
        if all_comments:
            df = pd.DataFrame(all_comments, columns=["genre", "game",  "commented_date", "comment"])
            df.to_csv(f"{directory}/youtube_comments_{game}.csv", index=False)
            print(f"\tYoutube data for {game} saved!")
        else:
            print(f"\tNo Youtube data for {game}.")
    
    except Exception as e:
        print(f"\tError scraping YouTube for {game}: {e}")
    
def scrape_steam(genre, game, directory, steamID):
    """This function searches for Steam reviews for a specific game."""
    if steamID is None:  # Not released
        print(f"\tNo Steam data for {game}.")
        return
    
    url = f"https://store.steampowered.com/appreviews/{steamID}?json=1&num_per_page=100&filter=creation_date"  # Sort by creation date
    print(url)
    all_reviews = []
    cursor = "*"  # Initial cursor for the first page
    num_reviews = 1000  # Total number of reviews to scrap
    
    while len(all_reviews) < num_reviews:
        # Make the request with the current cursor
        response = requests.get(f"{url}&cursor={cursor}")
        data = response.json()
        
        # Check if 'reviews' are in the response
        if "reviews" not in data:
            print(f"Error fetching reviews for {game}.")
            break
        
        # Add the reviews from this page
        for review in data["reviews"]:
            comment_date = datetime.fromtimestamp(review["timestamp_created"], tz=timezone.utc).strftime('%Y-%m-%d')
            comment = clean_text(review["review"])
            all_reviews.append([
                genre,
                game, 
                comment_date,
                comment,
            ])
        
        # Check if there's a 'cursor' for the next page
        if "cursor" in data:
            cursor = data["cursor"]  # Update the cursor for the next page
        else:
            print(f"No more reviews for {game}.")
            break  # Stop if there are no more reviews
    
    # Limit to the requested number of reviews
    all_reviews = all_reviews[:num_reviews]
    
    # Save the reviews to a CSV
    df = pd.DataFrame(all_reviews, columns=["genre", "game",  "commented_date", "comment"])
    df.to_csv(f"{directory}/steam_comments_{game}.csv", index=False)
    print(f"\tSteam data for {game} saved!")

def scrape_metacritic(genre, game, directory):
    """This function searches for Metacritic reviews for a specific game."""
    # Sanitize game name for URL
    gameName = re.sub(r"[',:;]+", "", game.lower())  # Remove unwanted characters
    gameName = re.sub(r"\s+", "-", gameName)  # Replace spaces with '-'
    url = f"https://www.metacritic.com/game/pc/{gameName}/user-reviews"
    
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(2)  # Allow page to load
    print(url)
    
    # Scroll to load more reviews
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Allow time for new content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Stop scrolling when no new content loads
        last_height = new_height
    
    reviews = []
    try:
        review_blocks = driver.find_elements(By.CSS_SELECTOR, ".c-siteReview")
        # Loop through each review block and extract score, username, and quote
        for review in review_blocks:
            # Extract quote
            quote_element = review.find_element(By.CSS_SELECTOR, ".c-siteReview_quote span")
            quote = quote_element.text.strip() if quote_element else "No Quote"
            comment = clean_text(quote)
            # Extract date
            date_element = review.find_element(By.CSS_SELECTOR, ".c-siteReviewHeader_reviewDate")
            date_obj = datetime.strptime(date_element.text.strip(), "%b %d, %Y")
            formatted_date = date_obj.strftime('%Y-%m-%d')
            reviews.append([
                genre, 
                game,
                formatted_date,
                comment,
            ])
        driver.quit()
        # Save reviews to CSV if there are any
        if reviews:
            df = pd.DataFrame(reviews, columns=["genre", "game",  "commented_date", "comment"])
            df.to_csv(f"{directory}/metacritic_comments_{game}.csv", index=False)
            print(f"\tMetacritic data for {game} saved!")
        else:
            print(f"\tNo Metacritic data for {game}.")
    except Exception as e:
        print(f"\tError scraping Metacritic for {game}: {e}")
        driver.quit()

# Run scrappers for each game
def run_scraper():
    """Loops through the list of games for each genre, and calls scraping 
    functions to gather data from various platforms (Reddit, Steam, etc.)."""
    for genre, game_list in GAMES.items():
        directory = f"../data/{genre}"
        os.makedirs(directory, exist_ok=True)
        for game, steamID in game_list.items():
            print(f"Scraping data for: {game} ({genre})...")
            # get reddit comments
            if validate_reddit(): 
                scrape_reddit(genre, game, directory)
            # get youtube comments
            if validate_youtube():
                scrape_youtube(genre, game, directory)
            # get steam comments
            scrape_steam(genre, game, directory, steamID)
            # get metacritic comments
            scrape_metacritic(genre, game, directory)
        time.sleep(5)  # Avoid rate limits 

def main():
    run_scraper() # run scrapper
    
if __name__ == "__main__":
    main()  