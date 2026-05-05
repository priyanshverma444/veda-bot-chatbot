import logging
import os
import re
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
You are an Ayurveda Advisor. Use the following information to answer the user's question in detail.
- Only answer questions related to Ayurvedic remedies, herbs, diet, lifestyle, wellness routines, symptoms, and Ayurveda education.
- If a question asks for anything outside Ayurvedic remedies or Ayurveda wellness guidance, refuse clearly and redirect the user to ask an Ayurveda-related health question.
- Every answer must explicitly mention the user's body type.
- Always end the answer with a short **Follow-up questions you can ask:** section containing 3 Ayurveda-relevant follow-up questions.
- Include remedies, precautions, and exceptions where necessary.
- Do **not** include any reference sections.
- Always convert follow-up questions into standalone questions while keeping context.
- Format your response in markdown with **bold**, _italics_, and bullet points where needed.
- If the answer exceeds 120 tokens, structure it into clear points.
- Personalize general lifestyle, diet, and routine suggestions for the user's dosha without treating it as a medical diagnosis.

Context: {context}
User body type: {body_type}
Question: {question}
"""

OUT_OF_SCOPE_RESPONSE = (
    "I can only help with Ayurvedic remedies, herbs, diet, lifestyle routines, "
    "wellness guidance, and Ayurveda-related health questions. Please ask a question "
    "within that Ayurveda wellness scope.\n\n"
    "**Follow-up questions you can ask:**\n"
    "- What are Ayurvedic remedies for better digestion?\n"
    "- Which foods are suitable for my dosha?\n"
    "- What daily routine can support my Ayurvedic balance?"
)

AYURVEDA_SCOPE_KEYWORDS = {
    "ayurveda",
    "ayurvedic",
    "dosha",
    "vata",
    "pitta",
    "kapha",
    "prakriti",
    "remedy",
    "remedies",
    "herb",
    "herbs",
    "herbal",
    "medicine",
    "health",
    "wellness",
    "diet",
    "food",
    "nutrition",
    "lifestyle",
    "routine",
    "yoga",
    "meditation",
    "sleep",
    "digestion",
    "digestive",
    "disease",
    "illness",
    "appetite",
    "immunity",
    "stress",
    "anxiety",
    "cold",
    "cough",
    "fever",
    "headache",
    "pain",
    "acidity",
    "gas",
    "bloating",
    "constipation",
    "diarrhea",
    "skin",
    "hair",
    "fatigue",
    "energy",
    "inflammation",
    "joint",
    "muscle",
    "throat",
    "sinus",
    "symptom",
    "symptoms",
    "allergy",
    "period",
    "menstrual",
    "pcos",
    "diabetes",
    "blood pressure",
    "cholesterol",
    "weight",
    "detox",
    "triphala",
    "ashwagandha",
    "brahmi",
    "turmeric",
    "ginger",
    "tulsi",
    "amla",
    "neem",
    "shatavari",
    "ghee",
    "abhyanga",
}

HEALTH_CONDITION_KEYWORDS = {
    "acne",
    "anemia",
    "arthritis",
    "asthma",
    "bronchitis",
    "chikungunya",
    "cholera",
    "ckd",
    "colitis",
    "copd",
    "covid",
    "dengue",
    "eczema",
    "fatty liver",
    "fissure",
    "flu",
    "gastritis",
    "gerd",
    "hepatitis",
    "hypertension",
    "ibs",
    "ibd",
    "infection",
    "influenza",
    "jaundice",
    "kidney stone",
    "malaria",
    "migraine",
    "piles",
    "pneumonia",
    "psoriasis",
    "thyroid",
    "tuberculosis",
    "typhoid",
    "ulcer",
    "urti",
    "uti",
    "viral",
    "vomiting",
}

HEALTH_CONTEXT_KEYWORDS = {
    "abdomen",
    "back",
    "bladder",
    "blood",
    "body",
    "bowel",
    "breathing",
    "chest",
    "ear",
    "eye",
    "gut",
    "heart",
    "kidney",
    "liver",
    "lung",
    "lungs",
    "mental",
    "mouth",
    "nose",
    "respiratory",
    "stomach",
    "sugar",
    "urinary",
    "urine",
}

HEALTH_ACTION_KEYWORDS = {
    "avoid",
    "care",
    "cure",
    "diet",
    "do",
    "eat",
    "foods",
    "help",
    "manage",
    "management",
    "prevent",
    "prevention",
    "recover",
    "recovery",
    "relief",
    "safe",
    "support",
    "treat",
    "treatment",
}

HEALTH_CONDITION_PATTERNS = [
    r"\b[a-z]+itis\b",
    r"\b[a-z]+osis\b",
    r"\b[a-z]+emia\b",
    r"\b[a-z]+algia\b",
    r"\b[a-z]+pathy\b",
]

OFF_TOPIC_KEYWORDS = {
    "code",
    "programming",
    "python",
    "javascript",
    "sql",
    "hack",
    "exploit",
    "malware",
    "password",
    "stock",
    "crypto",
    "investment",
    "movie",
    "song",
    "lyrics",
    "game",
    "politics",
    "election",
    "resume",
    "essay",
    "email",
    "recipe for bomb",
}


def contains_keyword(text, keywords):
    return any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords)


def contains_pattern(text, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def is_ayurveda_scope_query(question):
    normalized_question = f" {question.lower()} "
    has_off_topic_keyword = contains_keyword(normalized_question, OFF_TOPIC_KEYWORDS)
    if has_off_topic_keyword:
        return False

    has_ayurveda_or_health_keyword = contains_keyword(normalized_question, AYURVEDA_SCOPE_KEYWORDS)
    has_condition_keyword = contains_keyword(normalized_question, HEALTH_CONDITION_KEYWORDS)
    has_condition_pattern = contains_pattern(normalized_question, HEALTH_CONDITION_PATTERNS)
    has_health_context = contains_keyword(normalized_question, HEALTH_CONTEXT_KEYWORDS)
    has_health_action = contains_keyword(normalized_question, HEALTH_ACTION_KEYWORDS)

    return (
        has_ayurveda_or_health_keyword
        or has_condition_keyword
        or has_condition_pattern
        or (has_health_context and has_health_action)
    )


def format_scoped_response(message, body_type):
    if body_type:
        return f"For your {body_type} body type: {message}"
    return message


def ensure_follow_up_questions(result):
    if "follow-up questions you can ask" in result.lower():
        return result
    return (
        f"{result}\n\n"
        "**Follow-up questions you can ask:**\n"
        "- What Ayurvedic foods should I prefer for my body type?\n"
        "- What daily routine can help balance my dosha?\n"
        "- Which herbs are commonly used for this concern in Ayurveda?"
    )


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
    return PromptTemplate(template=custom_prompt_template, input_variables=["context", "body_type", "question"])


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


def handle_query(question, body_type=None):
    """Handle user queries."""
    try:
        if not body_type:
            return {
                "result": "Please complete the Know Your Body Type assessment before chatting with VedaBot."
            }

        if not is_ayurveda_scope_query(question):
            return {"result": format_scoped_response(OUT_OF_SCOPE_RESPONSE, body_type), "body_type": body_type}

        db, llm, qa_prompt = create_chat_bot_chain()
        docs = db.similarity_search(question, k=2)
        context = "\n\n".join(doc.page_content for doc in docs)
        prompt = qa_prompt.format(context=context, body_type=body_type or "Not provided", question=question)
        result = llm.invoke(prompt)
        result = ensure_follow_up_questions(result)
        result = format_scoped_response(result, body_type)
        return {"result": result, "source_documents": docs, "body_type": body_type}
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
