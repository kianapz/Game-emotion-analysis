from pymongo import MongoClient
import os
from dotenv import load_dotenv
from flair.data import Sentence
from flair.nn import Classifier
from textblob import TextBlob


# Load environment variables
load_dotenv()
MONGO_ConnectionString = os.getenv("MONGO_ConnectionString")
MONGO_URI = f"mongodb+srv://{MONGO_ConnectionString}"
DB_NAME = os.getenv("MONGO_DBNAME")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["Game"]  # Use existing collection "Game"

# Load Flair sentiment classifier
sentiment_model = Classifier.load('sentiment')

# Define aspects to analyze
ASPECTS = ["cost", "graphics", "platform", "storyline", "gameplay"]

def extract_aspects(review):
    """
    Extract relevant aspects (cost, graphics, platform, storyline, gameplay) from a game review.
    """
    review_blob = TextBlob(review)
    extracted_aspects = {}

    for aspect in ASPECTS:
        if aspect in review.lower():
            extracted_aspects[aspect] = review_blob.sentences
    
    return extracted_aspects

def analyze_sentiment(text):
    """
    Perform sentiment analysis using Flair NLP.
    """
    sentence = Sentence(text)
    sentiment_model.predict(sentence)
    label = sentence.labels[0]
    return label.value, label.score  # POSITIVE/NEGATIVE & confidence score

def aspect_based_sentiment(review):
    """
    Perform aspect-based sentiment analysis.
    """
    aspects = extract_aspects(review)
    
    if not aspects:
        print("⚠️ No relevant aspects found in this review.")
        return {}

    aspect_sentiments = {}

    print("\n🔍 Extracted Aspects:", list(aspects.keys()))
    for aspect, sentences in aspects.items():
        total_score = 0
        num_sentences = len(sentences)

        print(f"\n🔍 Analyzing Aspect: {aspect}")
        for sentence in sentences:
            sentiment, score = analyze_sentiment(str(sentence))
            print(f"  ➡️ Sentence: {sentence}\n     Sentiment: {sentiment}, Score: {score}")
            total_score += (1 if sentiment == "POSITIVE" else -1) * score

        avg_score = total_score / num_sentences if num_sentences > 0 else 0
        aspect_sentiments[aspect] = "POSITIVE" if avg_score > 0 else "NEGATIVE"

    print(f"✅ Final Aspect Sentiment Scores: {aspect_sentiments}")
    return aspect_sentiments

# Process each review in the database
for doc in collection.find():
    review_text = doc["review"]
    print("\n=====================================")
    print(f"📌 Processing Review for '{doc['game_title']}':")
    print(f"📝 Review: {review_text}")

    aspect_sentiments = aspect_based_sentiment(review_text)

    # Ensure _id is properly formatted
    document_id = ObjectId(doc["_id"]) if isinstance(doc["_id"], str) else doc["_id"]

    # Update existing document with aspect sentiments
    if aspect_sentiments:
        update_result = collection.update_one(
            {"_id": document_id},
            {"$set": {"aspect_sentiments": aspect_sentiments}}
        )
        if update_result.modified_count > 0:
            print(f"✅ Aspect Sentiments Updated in MongoDB for document {document_id}")
        else:
            print(f"⚠️ No document updated for {document_id} (Check if _id exists)")
    else:
        print("⚠️ No aspects found, skipping database update.")

print("\n✅ Aspect-based sentiment analysis completed and updated in MongoDB!")