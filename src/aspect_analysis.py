import pandas as pd
from textblob import TextBlob

# Define aspects to analyze
ASPECTS = {
    "cost": ["cost", "price", "affordability", "expensive", "cheap", "discount", "pricing", "value"],
    "graphics": ["graphics", "visuals", "art", "resolution", "textures", "design", "art style", "detail", "rendering", "clarity", "HD", "4K", "realism", "performance", "animation", "aesthetics"],
    "platform": ["platform", "device", "system", "console", "pc", "cross-platform", "exclusive", "device compatibility", "hardware", "software environment"],
    "storyline": ["storyline", "plot", "narrative", "characters", "dialogue", "writing", "script", "backstory", "lore", "depth", "twist", "theme", "world-building", "story"],
    "gameplay": ["gameplay", "mechanics", "controls", "interaction", "combat", "exploration", "level design", "user experience", "playability", "fluidity", "pace", "challenge", "variety", "immersion", "customization", "user interaction"],
    "soundtrack": ["music", "sound", "soundtrack", "audio", "bgm", "voice acting", "atmosphere", "sound design", "melody", "rhythm", "instrumental", "vocals", "audio design"],
    "difficulty": ["difficult", "challenge", "skill level", "difficulty curve", "hard", "easy", "moderate", "intense", "frustrating", "beginner", "expert", "progressive", "complexity"],
    "collaboration": ["multiplayer", "co-op", "online", "matchmaking", "pvp", "team", "competitive", "social", "cooperative", "lobby", "community", "group play", "collaboration"],
    "performance": ["performance", "lag", "frame rate", "fps", "optimization", "stability", "smoothness", "load time", "render time", "glitch", "drop", "frame drops", "buffering", "scalability", "speed", "efficiency", "system performance"],
    "replayability": ["replayability", "replay value", "longevity", "endgame", "post game", "replay options", "multiple endings", "progression", "game duration", "content depth"]
}

def calculate_sentiment(text):
    """
    Perform sentiment analysis using TextBlob.
    Returns polarity (-1 to 1) which is used to classify sentiment.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "positive"
    elif polarity < 0:
        return "negative"
    else:
        return "neutral"

def extract_aspects(review):
    """
    Extract relevant aspects from a game review.
    Each aspect is tracked if mentioned in the review.
    """
    extracted_aspects = {aspect: "none" for aspect in ASPECTS}  # Initialize all aspects with "none"
    # Tokenize the review
    review = review.lower()
    for aspect, keywords in ASPECTS.items():
        for keyword in keywords:
            if keyword in review:
                # Ensures we don't miss a aspect "adjective"
                extracted_aspects[aspect] = "mentioned"  # Mark the aspect as mentioned
                break
    return extracted_aspects

def aspect_based_sentiment(review):
    """
    Perform aspect-based sentiment analysis using TextBlob.
    Returns a dictionary of aspect sentiments (positive, negative, or neutral).
    """
    aspects = extract_aspects(review)
    aspect_sentiments = {aspect: "none" for aspect in aspects}  # Initialize all aspects with "none"
    for aspect in aspects.keys():
        if aspects[aspect] == "mentioned":  # Only analyze if aspect is mentioned
            sentiment = calculate_sentiment(review)
            aspect_sentiments[aspect] = sentiment

    return aspect_sentiments

def process_reviews_from_csv(csv_file, output_file):
    """
    Process reviews from a CSV file and perform aspect-based sentiment analysis.
    """
    df = pd.read_csv(csv_file)
    # Create new columns for each aspect, explicitly setting dtype to 'object' (supports string values)
    for aspect in ASPECTS.keys():
        df[aspect] = "none"  # Initialize all aspect columns with "none"
    df['overall_sentiment'] = "none"  # Initialize overall sentiment column with "none"

    # Analyze each review
    for index, row in df.iterrows():
        comment = row['comment']  # Assuming 'comment' column exists
        aspect_sentiments = aspect_based_sentiment(comment)

        # Update aspect columns with the sentiment values
        for aspect, sentiment in aspect_sentiments.items():
            if sentiment != "none":  # Only assign sentiment if aspect is mentioned
                df.at[index, aspect] = sentiment

    # Convert all string-based sentiment values to lowercase
    df = df.apply(lambda x: x.str.lower() if x.dtype == "object" else x)
    df.to_csv(output_file, index=False)
    print(f"Processed reviews saved to '{output_file}'.")

def main():
    csv_file = "../data/final_comment_dataset.csv"
    output_file = "../data/processed_reviews.csv"
    process_reviews_from_csv(csv_file, output_file)
    
    df = pd.read_csv(output_file)
    num_comments = df['commented'].value_counts()
    print(f"Count of {num_comments}")

if __name__ == "__main__":
    main()