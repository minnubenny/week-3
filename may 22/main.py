import asyncio
import chromadb
from chromadb.config import Settings
import google.generativeai as genai

# ------------------ Load Gemini API Key ------------------

def load_gemini_api_key(path="/home/minnu/Desktop/week 3/may 22/env4.txt"):
    with open(path, "r") as f:
        return f.read().strip()

# ------------------ Initialize Tools ------------------

class ChromaTool:
    def __init__(self):
        import chromadb
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="faq_collection")

    def add_documents(self, docs):
        for i, doc in enumerate(docs):
            self.collection.add(documents=[doc], ids=[str(i)])

    async def query(self, text, n_results=3):
        results = self.collection.query(query_texts=[text], n_results=n_results)
        return results["documents"][0]


class GeminiTool:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def generate(self, prompt):
        response = await asyncio.to_thread(self.model.generate_content, prompt)
        return response.text

# ------------------ Agents ------------------

class RAGRetriever:
    def __init__(self, chroma_tool):
        self.chroma = chroma_tool

    async def run(self, query):
        relevant_docs = await self.chroma.query(query)
        return relevant_docs

class QueryHandler:
    def __init__(self, retriever, gemini_tool):
        self.retriever = retriever
        self.gemini = gemini_tool

    async def run(self, query):
        context = await self.retriever.run(query)
        full_prompt = f"Answer the following question using this context:\n\nContext:\n{context}\n\nQuestion: {query}"
        response = await self.gemini.generate(full_prompt)
        return response

# ------------------ RoundRobinGroupChat Simulation ------------------

async def round_robin_chat(query_handler, query):
    response = await query_handler.run(query)
    return response

# ------------------ Main Program ------------------

async def main():
    # Load Gemini API Key
    gemini_api_key = load_gemini_api_key()

    # Initialize Tools
    chroma_tool = ChromaTool()
    gemini_tool = GeminiTool(gemini_api_key)

    # Populate ChromaDB with sample FAQ
    faqs = [
        "You can reset your password by going to the settings page.",
        "Our support hours are 9am to 5pm Monday through Friday.",
        "Refunds can be requested within 30 days of purchase."
    ]
    chroma_tool.add_documents(faqs)

    # Initialize Agents
    retriever = RAGRetriever(chroma_tool)
    handler = QueryHandler(retriever, gemini_tool)

    # Ask a sample question
    user_question = "How can I get a refund?"
    answer = await round_robin_chat(handler, user_question)
    print(f"💬 Answer: {answer}")

if __name__ == "__main__":
    asyncio.run(main())
