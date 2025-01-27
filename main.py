import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Annotated
from dotenv import load_dotenv
import requests
import chromadb
from chromadb.config import Settings
from langgraph.graph import Graph, StateGraph
# from langgraph.prelude import *
import openai
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize ChromaDB
chroma_client = chromadb.Client(Settings(allow_reset=True))
collection = chroma_client.create_collection(name="executive_orders")

class Document(BaseModel):
    id: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class State(BaseModel):
    documents: List[Document] = Field(default_factory=list)
    summary: str = ""

class FederalRegisterAPI:
    BASE_URL = "https://www.federalregister.gov/api/v1"

    @staticmethod
    def fetch_executive_orders(days_back: int = 7) -> List[Document]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        url = f"{FederalRegisterAPI.BASE_URL}/documents"
        params = {
            "conditions[type][]": "PRESDOCU",
            "conditions[presidential_document_type][]": "executive_order",
            "conditions[publication_date][gte]": start_date.strftime("%Y-%m-%d"),
            "conditions[publication_date][lte]": end_date.strftime("%Y-%m-%d"),
            "per_page": 20,
            "order": "newest"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        documents = []
        for item in data.get("results", []):
            # Safely handle None values for abstract and body_html
            abstract = item.get("abstract", "") or ""
            body_html = item.get("body_html", "") or ""
            
            doc = Document(
                id=str(item["document_number"]),
                title=item["title"],
                content=abstract + "\n\n" + body_html,
                metadata={
                    "publication_date": item["publication_date"],
                    "document_number": item["document_number"],
                    "type": "executive_order"
                }
            )
            documents.append(doc)
        
        return documents

def fetch_orders(state: State) -> State:
    api = FederalRegisterAPI()
    state.documents = api.fetch_executive_orders()
    return state

def store_documents(state: State) -> State:
    for doc in state.documents:
        collection.add(
            documents=[doc.content],
            metadatas=[doc.metadata],
            ids=[doc.id]
        )
    return state

def generate_summary(state: State) -> State:
    if not state.documents:
        state.summary = "No new executive orders found in the specified time period."
        return state
    
    summaries = []
    print(len(state.documents))
    for doc in state.documents:
        prompt = f"""Please provide a concise summary of the following executive order:
Title: {doc.title}

Content:
{doc.content[:8000]}  # Truncate to avoid token limits

Please include:
1. The main purpose of the order
2. Key provisions
3. Potential impact
Limit the summary to 3-4 sentences."""

        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes executive orders clearly and concisely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        summaries.append(f"Executive Order: {doc.title}\n{response.choices[0].message.content}\n")
    
    state.summary = "\n".join(summaries)
    return state

def create_workflow() -> Graph:
    # Create a new state graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("fetch", fetch_orders)
    workflow.add_node("store", store_documents)
    workflow.add_node("summarize", generate_summary)
    
    # Create edges
    workflow.add_edge("fetch", "store")
    workflow.add_edge("store", "summarize")
    
    # Set entry point
    workflow.set_entry_point("fetch")
    
    # Compile the graph
    return workflow.compile()

def main():
    # Create and run the workflow
    workflow = create_workflow()
    result = workflow.invoke(State())
    
    print("\nExecutive Orders Summary:")
    print("-" * 50)
    print(result)

def test_federal_register_api():
    try:
        api = FederalRegisterAPI()
        documents = api.fetch_executive_orders(days_back=30)  # Test with last 30 days
        
        print("\nFederal Register API Test Results:")
        print("-" * 50)
        print(f"Found {len(documents)} executive orders")
        
        for doc in documents:
            print(f"\nTitle: {doc.title}")
            print(f"Document ID: {doc.id}")
            print(f"Publication Date: {doc.metadata['publication_date']}")
            print("-" * 30)
        
        return len(documents) > 0
    except Exception as e:
        print(f"Error testing Federal Register API: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the API first
    if test_federal_register_api():
        print("\nAPI test successful! Running main workflow...\n")
        main()
    else:
        print("\nAPI test failed. Please check your connection and try again.") 