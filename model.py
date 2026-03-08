import logging
import os
from typing import List, Optional

from huggingface_hub import InferenceClient
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

try:
    # LangChain <= 0.1.x
    from langchain.llms.base import LLM
except ImportError:
    # LangChain >= 0.2.x / 1.x
    from langchain_core.language_models.llms import LLM

try:
    # LangChain <= 0.1.x
    from langchain.prompts import PromptTemplate
except ImportError:
    # LangChain >= 0.2.x
    from langchain_core.prompts import PromptTemplate

logging.basicConfig(level=logging.ERROR)

DB_FAISS_PATH = "vectorstore/db_faiss"

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
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_new_tokens,
                temperature=self.temperature,
            )
            message = response.choices[0].message
            if hasattr(message, "content"):
                return (message.content or "").strip()
            if isinstance(message, dict):
                return (message.get("content") or "").strip()
            return str(message).strip()
        except Exception as exc:
            logging.error("Generation failed: %s", exc)
            error_text = str(exc).lower()
            if "401" in error_text or "unauthorized" in error_text or "forbidden" in error_text:
                return "Authentication failed with Hugging Face. The access token may be expired or invalid."
            if "429" in error_text or "rate limit" in error_text:
                return "Hugging Face rate limit reached. Please retry after a short wait."
            return "Error generating response."

    @property
    def _identifying_params(self):
        return {"model": self.client.model}

    @property
    def _llm_type(self):
        return "huggingface_conversational"


def set_custom_prompt():
    return PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])


def load_llm():
    """Load the Hugging Face Inference Client."""
    api_token = os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN")
    if not api_token:
        raise ValueError("HUGGINGFACEHUB_ACCESS_TOKEN is not set. Add it to your environment variables.")

    try:
        client = InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=api_token)
        print("LLaMA 3 model loaded successfully.")
        return HuggingFaceConversationalLLM(client=client)
    except Exception as exc:
        logging.error("Failed to load model: %s", exc)
        raise RuntimeError("Model loading failed. Check your token or network.")


def create_chat_bot_chain():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    llm = load_llm()
    qa_prompt = set_custom_prompt()
    return db, llm, qa_prompt


def handle_query(question):
    """Handle user queries."""
    try:
        db, llm, qa_prompt = create_chat_bot_chain()
        docs = db.similarity_search(question, k=2)
        context = "\n\n".join(doc.page_content for doc in docs)
        prompt = qa_prompt.format(context=context, question=question)
        result = llm.invoke(prompt)
        return {"result": result, "source_documents": docs}
    except Exception as exc:
        logging.error("Error processing query: %s", exc)
        error_text = str(exc).lower()
        if "huggingfacehub_access_token" in error_text:
            return {
                "result": "HUGGINGFACEHUB_ACCESS_TOKEN is missing in environment variables. "
                "Set it in Hugging Face Space Settings > Variables and secrets."
            }
        if "401" in error_text or "unauthorized" in error_text or "forbidden" in error_text:
            return {
                "result": "Hugging Face authentication failed (token expired/invalid). "
                "Update HUGGINGFACEHUB_ACCESS_TOKEN in Space Secrets and restart the Space."
            }
        return {"result": "Oops! There was an issue processing your question. Please try again."}


if __name__ == "__main__":
    query = "What are common Ayurveda remedies for headache?"
    print("Query:", query)
    print("Answer:", handle_query(query))
