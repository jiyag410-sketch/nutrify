from groq import Groq
from dotenv import load_dotenv
import os
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

# Load the same embedding model used to build the vector store
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to the existing vector store
client_db = chromadb.PersistentClient(path="./vectorstore")
collection = client_db.get_or_create_collection(name="health_nutrition")

# Connect to Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a nutrition and health information assistant with access to a curated database of recipes and public health guidelines (USDA, CDC, WHO, ICMR-NIN).

RULES:
1. Use retrieved context as your primary source when it directly answers the question.
2. If the context is only partially relevant, still answer using your own general nutrition knowledge, clearly noting which parts come from general knowledge vs. the provided sources.
3. If the user's question has a typo or unclear abbreviation (e.g., "ocos" likely means "PCOS", "diabetis" means "diabetes"), interpret their most likely intent and answer that question directly. Do not ask for clarification unless the question is genuinely ambiguous between multiple unrelated meanings.
4. Only refuse to answer if the question is entirely unrelated to food, nutrition, health, or recipes, or if it explicitly asks for a medical diagnosis or personalized treatment plan — in those cases, recommend consulting a healthcare professional.
5. Never say "I don't have information" for general food/nutrition facts (like "is X food alkaline" or "is X good for Y condition") — these are common knowledge questions you can answer directly, supplementing with retrieved context where relevant.

EXAMPLE:
User: "is avocado good for ocos"
Correct behavior: Recognize "ocos" as a likely typo for "PCOS", then answer using general knowledge about avocado's fiber/healthy fat content and its relevance to PCOS-friendly eating, connecting it to any retrieved PCOS guidance if available.
Incorrect behavior: Asking the user to clarify what "ocos" means.

Always end health-related answers with a brief reminder that this is general information, not medical advice."""
def retrieve_context(query, k=8):
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )
    return results["documents"][0]

def answer_query(query):
    context_chunks = retrieve_context(query)
    context = "\n\n---\n\n".join(context_chunks)

    user_message = f"""You have deep nutrition and food knowledge. A user asked: "{query}"

Here are some notes you jotted down earlier from a recipe/nutrition database that might be useful (ignore them completely if they're not relevant to this specific question):

{context}

Now answer the user's question directly and confidently, as a nutrition expert would. Do NOT say phrases like "the context doesn't include", "I don't have information", "based on what you provided", or similar — just answer using everything you know. If it's a food/nutrition/recipe question, you always have enough knowledge to give a helpful answer."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    print("Health & Nutrition Assistant (type 'quit' to exit)\n")
    while True:
        query = input("You: ")
        if query.lower() == "quit":
            break
        answer = answer_query(query)
        print(f"\nAssistant: {answer}\n") 
        