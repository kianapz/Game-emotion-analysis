from collections import defaultdict
from pymongo import MongoClient
from flair.data import Sentence
from flair.nn import Classifier
from dotenv import load_dotenv
from textblob import TextBlob
from nltk.util import ngrams
import nltk
import sys
import os

# Download necessary NLTK resources
nltk.download("punkt")
nltk.download('punkt_tab')

# Initialize statistics variables
total_reviews = 0
platform_count = defaultdict(int)  # Track review count per genre
aspect_sentiment_counts = defaultdict(lambda: {"positive": 0, "negative": 0, "total": 0})
aspect_mention_counts = defaultdict(int)  # Count how often each aspect is mentioned
overall_sentiment_counts = {"positive": 0, "negative": 0}


# Load environment variables
load_dotenv()
MONGO_ConnectionString = os.getenv("MONGO_ConnectionString")
MONGO_URL = f"mongodb+srv://{MONGO_ConnectionString}"
DB_NAME = os.getenv("MONGO_DBNAME")

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
collection = db["Game"]  # Use existing collection "Game"

# Load Flair sentiment classifier
sentiment_model = Classifier.load("en-sentiment")

# Define aspects to analyze
ASPECTS = {
    "value": ["cost", "price", "affordability", "expensive", "cheap", "discount", "pricing", "value"],
    "visuals": ["graphics", "visuals", "art", "resolution", "textures", "design", "art style", "detail", "rendering", "clarity", "HD", "4K", "realism", "performance", "animation", "aesthetics"],
    "platform": ["platform", "device", "system", "console", "pc", "cross-platform", "exclusive", "device compatibility", "hardware", "software environment"],
    "narrative": ["storyline", "plot", "narrative", "characters", "dialogue", "writing", "script", "backstory", "lore", "depth", "twist", "theme", "world-building", "story"],
    "interaction": ["gameplay", "mechanics", "controls", "interaction", "combat", "exploration", "level design", "user experience", "playability", "fluidity", "pace", "challenge", "variety", "immersion", "customization", "user interaction"],
    "audio": ["music", "sound", "soundtrack", "audio", "bgm", "voice acting", "atmosphere", "sound design", "melody", "rhythm", "instrumental", "vocals", "audio design"],
    "challenge": ["difficult", "challenge", "skill level", "difficulty curve", "hard", "easy", "moderate", "intense", "frustrating", "beginner", "expert", "progressive", "complexity"],
    "social": ["multiplayer", "co-op", "online", "matchmaking", "pvp", "team", "competitive", "social", "cooperative", "lobby", "community","group play", "collaboration"],
    "performance": ["performance", "lag", "frame rate", "fps", "optimization", "stability", "smoothness", "load time", "render time", "glitch", "drop", "frame drops", "buffering", "scalability", "speed", "efficiency", "system performance"],
    "engagement": ["replayability", "replay value", "longevity", "endgame", "post game", "replay options", "multiple endings", "progression", "game duration", "content depth"]
}

# def normalize_text(text):
#     """
#     Normalize text by replacing different spellings with a "standard" name.
#     """
#     for standard_aspect, variations in ASPECTS.items():
#         for variation in variations:
#             text = text.replace(variation, standard_aspect)  # Replace variations with the standard term
#     return text
def normalize_text(text):
    """
    Normalize text by replacing different spellings with a 'standard' name.
    This function analyzes the text as single words and two-word compounds (bigrams).
    """
    words = nltk.word_tokenize(text)  # Tokenize text into words
    bigrams = list(ngrams(words, 2))  # Tokenize text into two-word compounds
    bigram_strings = [' '.join(bigram) for bigram in bigrams]

    # Create a lookup dictionary of variations to standard aspects
    variation_to_aspect = {}
    for standard_aspect, variations in ASPECTS.items():
        for variation in variations:
            variation_to_aspect[variation.lower()] = standard_aspect  # Ensure case insensitivity

    # Process single words
    for i, word in enumerate(words):
        word_lower = word.lower()
        if word_lower in variation_to_aspect:
            words[i] = variation_to_aspect[word_lower]  # Replace word with standard aspect

    # Process bigrams (check before replacing)
    for i in range(len(bigrams)):
        bigram_text = bigram_strings[i].lower()
        if bigram_text in variation_to_aspect:
            words[i] = variation_to_aspect[bigram_text]  # Replace first word of bigram
            words[i+1] = ''  # Remove second word (to avoid duplicates)

    # Reconstruct text
    normalized_text = ' '.join(filter(None, words))  # Remove empty strings and join words

    return normalized_text

def extract_aspects(review):
    """
    Extract relevant aspects (cost, graphics, platform, storyline, gameplay) from a game review.
    """
    normalized_review = normalize_text(review.lower())  # Normalize text before processing
    review_blob = TextBlob(normalized_review)
    extracted_aspects = {}

    for aspect in ASPECTS.keys():  # Use standardized aspect names
        if aspect in normalized_review:
            extracted_aspects[aspect] = [str(sentence) for sentence in review_blob.sentences]
    
    return extracted_aspects

def analyze_sentiment(text):
    """
    Perform sentiment analysis using Flair NLP.
    """
    sentence = Sentence(text)
    sentiment_model.predict(sentence)
    if sentence.labels:
        label = sentence.labels[0]
        return label.value, label.score
    return "NEUTRAL", 0.0

def aspect_based_sentiment(review):
    """
    Perform aspect-based sentiment analysis.
    """
    aspects = extract_aspects(review)
    
    if not aspects:
        print("No relevant aspects found in this review.")
        return {}

    aspect_sentiments = {}
    print("\nExtracted Aspects:", list(aspects.keys()))
    
    for aspect, sentences in aspects.items():
        total_score = 0
        num_sentences = len(sentences)

        print(f"\nAnalyzing Aspect: {aspect}")
        for sentence in sentences:
            sentiment, score = analyze_sentiment(str(sentence))
            print(f"Sentence: {sentence}\n     Sentiment: {sentiment}, Score: {score}")
            total_score += (1 if sentiment == "POSITIVE" else -1) * score

        avg_score = total_score / num_sentences if num_sentences > 0 else 0
        aspect_sentiments[aspect] = "POSITIVE" if avg_score > 0 else "NEGATIVE"
    
    print(f"Final Aspect Sentiment Scores: {aspect_sentiments}")
    return aspect_sentiments

def save_statistics():
    """
    Save and print the final analysis statistics.
    """
    print("\n===== FINAL STATISTICS =====")

    # Total reviews processed
    print(f"Total Reviews Processed: {total_reviews}")

    # Reviews per platform
    print("\nReviews per Platform:")
    for platform, count in platform_count.items():
        print(f"  {platform}: {count} reviews")

    # Most mentioned aspects
    print("\nMost Mentioned Aspects:")
    sorted_aspects = sorted(aspect_mention_counts.items(), key=lambda x: x[1], reverse=True)
    for aspect, count in sorted_aspects:
        print(f"  {aspect}: {count} mentions")

    # Average sentiment per aspect
    print("\nAverage Sentiment Per Aspect:")
    for aspect, counts in aspect_sentiment_counts.items():
        total = counts["total"]
        positive_ratio = counts["positive"] / total if total > 0 else 0
        sentiment_label = "POSITIVE" if positive_ratio > 0.5 else "NEGATIVE"
        print(f"  {aspect}: {sentiment_label} ({counts['positive']} positive, {counts['negative']} negative)")

    # Overall sentiment
    total_positive = overall_sentiment_counts["positive"]
    total_negative = overall_sentiment_counts["negative"]
    positive_percentage = (total_positive / total_reviews) * 100 if total_reviews > 0 else 0
    negative_percentage = (total_negative / total_reviews) * 100 if total_reviews > 0 else 0

    print("\nOverall Sentiment:")
    print(f"  Positive Reviews: {positive_percentage:.2f}%")
    print(f"  Negative Reviews: {negative_percentage:.2f}%")

    # Save statistics to a file
    with open("review_statistics.txt", "w", encoding="utf-8") as f:
        f.write("===== FINAL STATISTICS =====\n")
        f.write(f"Total Reviews Processed: {total_reviews}\n\n")

        f.write("Reviews per Platform:\n")
        for platform, count in platform_count.items():
            f.write(f"  {platform}: {count} reviews\n")

        f.write("\nMost Mentioned Aspects:\n")
        for aspect, count in sorted_aspects:
            f.write(f"  {aspect}: {count} mentions\n")

        f.write("\nAverage Sentiment Per Aspect:\n")
        for aspect, counts in aspect_sentiment_counts.items():
            total = counts["total"]
            positive_ratio = counts["positive"] / total if total > 0 else 0
            sentiment_label = "POSITIVE" if positive_ratio > 0.5 else "NEGATIVE"
            f.write(f"  {aspect}: {sentiment_label} ({counts['positive']} positive, {counts['negative']} negative)\n")

        f.write("Overall Sentiment:\n")
        f.write(f"  Positive Reviews: {positive_percentage:.2f}%\n")
        f.write(f"  Negative Reviews: {negative_percentage:.2f}%\n")

    print("Statistics saved to 'review_statistics.txt'")

def process_review(doc):
    """
    Process and analyze a single review document.
    """
    review_text = doc["review"]
    print("\n=====================================")
    print(f"Processing Review for '{doc['game_title']}':")
    print(f"Review: {review_text}")
    global total_reviews

    aspect_sentiments = aspect_based_sentiment(review_text) # get aspect sentiments

    # Always overwrite aspect_sentiments
    update_result = collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"aspect_sentiments": aspect_sentiments}}
    )

    if update_result.modified_count > 0:
        print(f"Aspect Sentiments Updated in MongoDB for document {doc['_id']}")
    else:
        print(f"No changes made for {doc['_id']} (Data may already be identical)")

    # Update statistics
    total_reviews += 1
    platform_count[doc.get("platform", "Unknown")] += 1  # Count per platform

    for aspect, sentiment in aspect_sentiments.items():
        aspect_mention_counts[aspect] += 1
        aspect_sentiment_counts[aspect]["total"] += 1
        if sentiment == "POSITIVE":
            aspect_sentiment_counts[aspect]["positive"] += 1
        else:
            aspect_sentiment_counts[aspect]["negative"] += 1

    # Track overall review sentiment
    if any(sent == "POSITIVE" for sent in aspect_sentiments.values()):
        overall_sentiment_counts["positive"] += 1
    else:
        overall_sentiment_counts["negative"] += 1

def main():
    sys.stdout = open("output_log.txt", "w", encoding="utf-8")
    batch_size = 500
    skip = 0

    while True:
        docs = list(collection.find().skip(skip).limit(batch_size))
        if not docs:
            break  # Stop if no more documents
        for doc in docs:
            process_review(doc)  # Process each review
        skip += batch_size  # Move to the next batch
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    # Save and print final statistics
    save_statistics()

if __name__ == "__main__":
    main()