import os
import asyncio
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from pinecone import Pinecone, ServerlessSpec
# Load API key
load_dotenv()
api_key = os.getenv("PINECONE_API_KEY")

async def main():
    # Initialize the web crawler
    crawler = AsyncWebCrawler(verbose=True)
    result = await crawler.arun(url="https://developer.hashicorp.com/terraform/docs")

    # Ensure we got a valid response
    if not result or not hasattr(result, "markdown"):
        print("Error: Unable to fetch markdown content.")
        return
    content = result.markdown
    # Split the text
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.split_text(content)
    # Embed the documents
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = [embedding_function.embed(doc) for doc in documents]  # Blocking, could be optimized
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    index_name = "quickstart"
    # Check if index exists before creating
    if index_name not in pc.list_indexes():
        print(f"Creating Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=384,  # Check if correct for your model
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    # Connect to Pinecone index
    index = pc.Index(index_name)
    upsert_data = [
        {"id": str(i), "values": embeddings[i]} for i in range(len(embeddings))
    ]
    index.upsert(vectors=upsert_data)
    print("Pinecone index populated with embeddings!")


# Run the async function
asyncio.run(main())
