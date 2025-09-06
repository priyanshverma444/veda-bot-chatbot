import os
import logging
from typing import Optional, List
from huggingface_hub import InferenceClient
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# Configure logging
logging.basicConfig(level=logging.ERROR)

DB_FAISS_PATH = 'vectorstore/db_faiss'

# Custom Ayurvedic prompt
custom_prompt_template = """
You are an Ayurveda Advisor. Use the following information to answer the user's question in detail:
- Include remedies, precautions, and exceptions where necessary.
- Do **not** include any reference sections.
- Always convert follow-up questions into standalone questions while keeping context.
- Format your response in markdown with **bold**, _italics_, and bullet points where needed.
- If the answer exceeds 120 tokens, structure it into clear points.

Context: {context}
Question: {question}
"""

# ---- Custom LangChain-compatible LLM ---- #
class HuggingFaceConversationalLLM(LLM):
    client: InferenceClient
    max_new_tokens: int = 512
    temperature: float = 0.1

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Send the prompt to HuggingFace for conversational generation."""
        try:
            response = self.client.chat_completion(
                model=self.client.model,
                messages=[
                    {"role": "system", "content": "You are a helpful Ayurveda advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_new_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message["content"].strip()
        except Exception as e:
            logging.error(f"Generation failed: {str(e)}")
            return "⚠️ Error generating response."

    @property
    def _identifying_params(self):
        return {"model": self.client.model}

    @property
    def _llm_type(self):
        return "huggingface_conversational"

# ---- Helper functions ---- #
def set_custom_prompt():
    return PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])

def load_llm():
    """Load the Hugging Face Inference Client."""
    api_token = os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN")
    if not api_token:
        raise ValueError("HUGGINGFACEHUB_ACCESS_TOKEN is not set. Add it to your environment variables.")
    
    try:
        client = InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=api_token)
        print("✅ LLaMA 3 model loaded successfully!")
        return HuggingFaceConversationalLLM(client=client)
    except Exception as e:
        logging.error(f"❌ Failed to load model: {str(e)}")
        raise RuntimeError("Model loading failed. Check your token or network.")

def retrieval_qa_chain(llm, prompt, db):
    """Create RetrievalQA chain."""
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 2}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

def create_chat_bot_chain():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    llm = load_llm()
    qa_prompt = set_custom_prompt()
    return retrieval_qa_chain(llm, qa_prompt, db)

def handle_query(question):
    """Handle user queries."""
    try:
        qa_chain = create_chat_bot_chain()
        response = qa_chain.invoke({"query": question})
        return response
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        return {"result": "⚠️ Oops! There was an issue processing your question. Please try again."}

if __name__ == "__main__":
    query = "What are common Ayurveda remedies for headache?"
    print("🔍 Query:", query)
    print("🤖 Answer:", handle_query(query))
