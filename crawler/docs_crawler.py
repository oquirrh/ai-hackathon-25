import os

from dotenv import load_dotenv
from phi.tools.crawl4ai_tools import Crawl4aiTools
from langchain.text_splitter import CharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec


class DocsCrawler:
    """
    A class for scraping, processing, and indexing documentation in Pinecone.

    This class scrapes documentation from a list of URLs, splits the content into chunks, generates embeddings
    using a specified model, and stores the embeddings in a Pinecone index.

    Args:
        pinecone_api_key (str): The API key to authenticate with Pinecone service.
        doc_urls (list): A list of URLs from which documentation or content will be scraped.
        embedding_model (str): The name of the pre-trained embedding model to use for generating embeddings
                                for the scraped documents.

    Attributes:
        pinecone_api_key (str): The API key to authenticate with Pinecone service.
        doc_urls (list): A list of URLs for scraping documentation.
        scraper (Crawl4aiTools): Instance of Crawl4aiTools used for scraping content from URLs.
        text_splitter (CharacterTextSplitter): Instance of CharacterTextSplitter used for splitting the scraped text into smaller chunks.
        model (SentenceTransformer): Instance of SentenceTransformer used for generating embeddings from the split text.
    """

    def __init__(self, pinecone_api_key, doc_urls, embedding_model):
        """
        Initializes the DocsCrawler class with the given configuration.

        Args:
            pinecone_api_key (str): The API key to authenticate with Pinecone service.
            doc_urls (list): A list of URLs from which documentation or content will be scraped.
            embedding_model (str): The name of the pre-trained embedding model to use for generating embeddings
                                    for the scraped documents.
        """
        self.pinecone_api_key = pinecone_api_key
        self.doc_urls = doc_urls
        self.scraper = Crawl4aiTools(max_length=None)
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        self.model = SentenceTransformer(embedding_model)

    def __fetch_docs(self, url):
        """
        WARNING: Internal method, do not call directly.

        This method scrapes the documentation at the specified URL and returns the content as a string.

        Args:
            url (str): The URL to scrape the documentation from.

        Returns:
            str: The scraped content from the URL.

        Raises:
            ValueError: If no content is retrieved from the URL.
        """
        print(f"Scraping {url} ...")
        content = self.scraper.web_crawler(url)

        if not content.strip():
            raise ValueError(f"Failed to retrieve content from {url}.")
        return content

    def __process_docs(self, content):
        """
        WARNING: Internal method, do not call directly.

        This method splits the scraped content into smaller chunks and generates embeddings for each chunk.

        Args:
            content (str): The content of the scraped documentation.

        Returns:
            tuple: A tuple containing two elements:
                - documents (list): The split document chunks.
                - embeddings (list): The embeddings generated for each document chunk.
        """
        documents = self.text_splitter.split_text(content)
        embeddings = self.model.encode(documents)
        return documents, embeddings

    def __store_in_pinecone(self, documents, embeddings):
        """
        WARNING: Internal method, do not call directly.

        This method stores the embeddings of the documents in a Pinecone index.

        Args:
            documents (list): A list of document chunks.
            embeddings (list): A list of embeddings corresponding to the document chunks.
        """
        pc = Pinecone(api_key=self.pinecone_api_key)
        index_name = "terraform-docs"

        # Create index if it doesn't exist
        if index_name not in pc.list_indexes():
            print("Creating Pinecone index...")
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        # Connect to Pinecone index
        index = pc.Index(index_name)

        # Prepare and upsert data
        upsert_data = [
            {"id": str(i), "values": embeddings[i].tolist(), "metadata": {"text": documents[i]}}
            for i in range(len(embeddings))
        ]
        index.upsert(vectors=upsert_data)
        print("Documents indexed successfully!")

    def crawl_and_index(self):
        """
        Scrapes documentation from multiple URLs, processes the content into embeddings, and stores them in Pinecone.

        This method loops through the provided `doc_urls`, scrapes each URL, processes the content into document chunks,
        generates embeddings, and stores them in a Pinecone index.
        """
        for url in self.doc_urls:
            content = self.__fetch_docs(url)
            documents, embeddings = self.__process_docs(content)
            self.__store_in_pinecone(documents, embeddings)


# example usage:

# def main():
#     # Load API keys
#     load_dotenv()
#     pinecone_api_key = os.getenv("PINECONE_API_KEY")
#
#     if not pinecone_api_key:
#         raise ValueError("Missing PINECONE_API_KEY in environment variables")
#
#     # List of URLs to scrape
#     doc_urls = [
#         "https://developer.hashicorp.com/terraform/docs",
#         # Add more URLs here as needed
#     ]
#
#     # Initialize the DocsCrawler class and run the process
#     crawler = DocsCrawler(pinecone_api_key, doc_urls, "all-MiniLM-L6-v2")
#     crawler.crawl_and_index()
#
#
# # Run the function
# if __name__ == "__main__":
#     main()

