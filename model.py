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
- Always end the answer with a short **Follow-up questions you can ask:** section containing 3 standalone questions that are specific to the user's condition or symptom and their body type.
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
    "dizzy",
    "dizziness",
    "disease",
    "illness",
    "appetite",
    "immunity",
    "stress",
    "anxiety",
    "aankh",
    "ankh",
    "bukhar",
    "cold",
    "cough",
    "dard",
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
    "fat",
    "fatigue",
    "nausea",
    "nauseous",
    "pet",
    "vertigo",
    "weakness",
    "energy",
    "low",
    "inflammation",
    "joint",
    "muscle",
    "throat",
    "gala",
    "sinus",
    "symptom",
    "symptoms",
    "rash",
    "itching",
    "swelling",
    "breathlessness",
    "color",
    "colour",
    "dark",
    "discolor",
    "discolored",
    "discoloration",
    "discolour",
    "discoloured",
    "discolouration",
    "saans",
    "sardi",
    "allergy",
    "period",
    "menstrual",
    "pcos",
    "diabetes",
    "blood pressure",
    "cholesterol",
    "obesity",
    "obese",
    "overweight",
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
    "autoimmune",
    "bipolar",
    "bronchitis",
    "cancer",
    "cardiac",
    "chikungunya",
    "cholera",
    "ckd",
    "colitis",
    "copd",
    "covid",
    "crohn",
    "crohns",
    "dengue",
    "depression",
    "depressed",
    "dermatitis",
    "dysentery",
    "eczema",
    "endometriosis",
    "epilepsy",
    "fibromyalgia",
    "fatty liver",
    "fissure",
    "fistula",
    "fibroid",
    "flu",
    "gallstone",
    "gallstones",
    "gastritis",
    "gerd",
    "heart disease",
    "hepatitis",
    "high bp",
    "hypothyroid",
    "hypothyroidism",
    "hyperthyroid",
    "hyperthyroidism",
    "hypertension",
    "ibs",
    "ibd",
    "infection",
    "influenza",
    "infertility",
    "insomnia",
    "jaundice",
    "kidney stone",
    "kidney stones",
    "kidney disease",
    "lupus",
    "malaria",
    "ms",
    "menopause",
    "migraine",
    "mood disorder",
    "ocd",
    "panic",
    "parkinson",
    "parkinsons",
    "pcod",
    "piles",
    "pneumonia",
    "ptsd",
    "psoriasis",
    "rare disease",
    "sarcoma",
    "seizure",
    "seizures",
    "stroke",
    "syndrome",
    "thyroid",
    "tuberculosis",
    "typhoid",
    "ulcer",
    "unwell",
    "urti",
    "uti",
    "viral",
    "vomiting",
    "vomit",
    "vomits",
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
    "gallbladder",
    "gut",
    "heart",
    "kidney",
    "liver",
    "lung",
    "lungs",
    "mental",
    "mouth",
    "nerve",
    "nerves",
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
    "diagnosed",
    "eat",
    "facing",
    "feel",
    "feeling",
    "foods",
    "have",
    "having",
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
    "struggling",
    "suffering",
    "suffer",
    "treat",
    "treatment",
}

CASUAL_HEALTH_PHRASES = {
    "blood pressure",
    "bp",
    "khansi",
    "feel low",
    "feeling low",
    "feeling sick",
    "feeling unwell",
    "not feeling good",
    "not feeling well",
    "low feel",
    "dark urine",
    "discolored urine",
    "discoloured urine",
    "gala dard",
    "pet dard",
    "saans problem",
    "sick feel",
    "urine color",
    "urine colour",
    "urine discolor",
    "urine discoloration",
    "urine discolour",
    "urine discolouration",
    "unwell feel",
    "sir dard",
}

COMMON_HEALTH_TYPOS = {
    "acidityy": "acidity",
    "anxity": "anxiety",
    "anxeity": "anxiety",
    "anxietyy": "anxiety",
    "arthrits": "arthritis",
    "arthiritis": "arthritis",
    "asthama": "asthma",
    "bukhaar": "bukhar",
    "constipaton": "constipation",
    "constipationn": "constipation",
    "caugh": "cough",
    "coughh": "cough",
    "depresion": "depression",
    "depresson": "depression",
    "diabates": "diabetes",
    "diabeties": "diabetes",
    "diarea": "diarrhea",
    "diarrhoea": "diarrhea",
    "diahrea": "diarrhea",
    "dizzyness": "dizziness",
    "feaver": "fever",
    "feveer": "fever",
    "gastric": "gastritis",
    "headach": "headache",
    "headche": "headache",
    "khasi": "khansi",
    "migrane": "migraine",
    "nausia": "nausea",
    "nause": "nausea",
    "pnemonia": "pneumonia",
    "pnumonia": "pneumonia",
    "pneumoniaa": "pneumonia",
    "pnuemonia": "pneumonia",
    "psorisis": "psoriasis",
    "thypoid": "typhoid",
    "typhiod": "typhoid",
    "typhoid fever": "typhoid",
    "vommiting": "vomiting",
    "vomitting": "vomiting",
}

QUESTION_FILLER_WORDS = {
    "a",
    "about",
    "am",
    "an",
    "any",
    "are",
    "can",
    "do",
    "for",
    "from",
    "got",
    "hai",
    "have",
    "help",
    "how",
    "i",
    "is",
    "me",
    "my",
    "of",
    "please",
    "raha",
    "suffering",
    "the",
    "to",
    "what",
    "with",
}

CONCERN_DISPLAY_NAMES = {
    "bp": "high blood pressure",
    "ckd": "chronic kidney disease",
    "copd": "COPD",
    "crohn": "Crohn's disease",
    "crohns": "Crohn's disease",
    "covid": "COVID",
    "gerd": "GERD",
    "ibs": "IBS",
    "ibd": "IBD",
    "ocd": "OCD",
    "pcod": "PCOD",
    "pcos": "PCOS",
    "ptsd": "PTSD",
    "urti": "upper respiratory infection",
    "uti": "UTI",
    "bukhar": "fever",
    "gala dard": "throat pain",
    "khansi": "cough",
    "pet dard": "stomach pain",
    "saans": "breathing difficulty",
    "saans problem": "breathing difficulty",
    "sardi": "cold",
    "sir dard": "headache",
    "dark urine": "dark urine",
    "discolored urine": "urine discoloration",
    "discoloured urine": "urine discoloration",
    "urine discolour": "urine discoloration",
    "urine discolouration": "urine discoloration",
    "urine discolor": "urine discoloration",
    "urine discoloration": "urine discoloration",
    "vomit": "vomiting",
}

GENERIC_CONCERN_KEYWORDS = {
    "disease",
    "illness",
    "infection",
    "rare disease",
    "symptom",
    "symptoms",
    "syndrome",
}

HEALTH_CONDITION_PATTERNS = [
    r"\b[a-z]+blastoma\b",
    r"\b[a-z]+carcinoma\b",
    r"\b[a-z]+itis\b",
    r"\b[a-z]+osis\b",
    r"\b[a-z]+emia\b",
    r"\b[a-z]+algia\b",
    r"\b[a-z]+pathy\b",
    r"\b[a-z]+plasia\b",
    r"\b[a-z]+sclerosis\b",
    r"\b(?:[a-z]+\s+){1,3}syndrome\b",
    r"\b[a-z]+syndrome\b",
    r"\b(?:[a-z]+\s+)?sarcoma\b",
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

SELF_HARM_CRISIS_KEYWORDS = {
    "suicidal",
    "suicide",
    "kill myself",
    "end my life",
    "want to die",
    "dont want to live",
    "do not want to live",
    "life is not worth living",
    "overdose myself",
    "self harm",
    "selfharm",
    "harm myself",
    "cut myself",
}

BLEEDING_EMERGENCY_KEYWORDS = {
    "blood loss",
    "bleeding heavily",
    "bleeding",
    "bleed",
    "bled",
    "slit",
    "deep cut",
    "heavy bleeding",
    "lot of blood",
    "lots of blood",
    "cut wrist",
    "cut my wrist",
    "cut hand",
    "hand bleeding",
    "wrist bleeding",
}

CHEST_PAIN_EMERGENCY_KEYWORDS = {
    "chest pain",
    "chest tightness",
    "heart attack",
    "pain in chest",
    "pressure in chest",
    "left arm pain",
    "jaw pain with chest",
}

STROKE_EMERGENCY_KEYWORDS = {
    "stroke symptoms",
    "face drooping",
    "facial droop",
    "one side weakness",
    "slurred speech",
    "sudden confusion",
    "sudden numbness",
    "sudden weakness",
    "cannot speak",
    "cant speak",
}

BREATHING_EMERGENCY_KEYWORDS = {
    "cannot breathe",
    "cant breathe",
    "can't breathe",
    "difficulty breathing",
    "severe breathlessness",
    "shortness of breath",
    "struggling to breathe",
    "choking",
    "blue lips",
}

POISONING_OVERDOSE_EMERGENCY_KEYWORDS = {
    "overdose",
    "poison",
    "poisoning",
    "drank poison",
    "ate poison",
    "took too many pills",
    "too many tablets",
    "medicine overdose",
    "drug overdose",
}

SEIZURE_UNCONSCIOUS_EMERGENCY_KEYWORDS = {
    "unconscious",
    "fainted and not waking",
    "not waking up",
    "seizure not stopping",
    "continuous seizure",
    "fits not stopping",
    "convulsion",
}

ALLERGY_EMERGENCY_KEYWORDS = {
    "anaphylaxis",
    "severe allergy",
    "allergic reaction",
    "swollen tongue",
    "tongue swelling",
    "throat swelling",
    "face swelling",
    "hives with breathing",
}

BURN_EMERGENCY_KEYWORDS = {
    "burn",
    "burns",
    "burnt",
    "burned",
    "scald",
    "scalded",
    "severe burn",
    "major burn",
    "burned badly",
    "chemical burn",
    "electric burn",
    "electrical burn",
}

PREGNANCY_EMERGENCY_KEYWORDS = {
    "pregnant bleeding",
    "bleeding during pregnancy",
    "pregnancy bleeding",
    "severe pregnancy pain",
    "pregnant severe pain",
}

SELF_HARM_CRISIS_RESPONSE = (
    "I'm really sorry you're feeling this. This is urgent and you deserve immediate support.\n\n"
    "- If you might hurt yourself, call your local emergency number now or go to the nearest emergency room.\n"
    "- If you're in the U.S. or Canada, call or text **988** for immediate crisis support. If you're in India, call **112** for emergency help.\n"
    "- Move away from anything you could use to harm yourself, and contact a trusted person to stay with you right now.\n\n"
    "I can't help with self-harm instructions, but I can stay with you and help you take the next safe step: please tell me whether you are alone right now."
)

BLEEDING_EMERGENCY_RESPONSE = (
    "This may need urgent medical care. Please do this now:\n\n"
    "- Apply firm, continuous pressure on the bleeding area with a clean cloth or bandage.\n"
    "- Raise the injured hand/arm above heart level if you can.\n"
    "- Call your local emergency number or go to the nearest emergency room if bleeding is heavy, won't stop, the cut is deep, or you feel weak/dizzy.\n"
    "- Do not rely on Ayurvedic or home remedies for active bleeding or blood loss."
)

CHEST_PAIN_EMERGENCY_RESPONSE = (
    "Chest pain or pressure can be an emergency. Please call your local emergency number now or go to the nearest emergency room, especially if there is sweating, nausea, breathlessness, jaw/arm pain, faintness, or pressure in the chest.\n\n"
    "Do not wait for Ayurvedic or home remedies for possible heart attack symptoms."
)

STROKE_EMERGENCY_RESPONSE = (
    "This could be a stroke emergency. Call your local emergency number now.\n\n"
    "- Watch for face drooping, arm weakness, speech trouble, sudden confusion, sudden numbness, or sudden severe headache.\n"
    "- Note the time symptoms started.\n"
    "- Do not wait for home or Ayurvedic remedies."
)

BREATHING_EMERGENCY_RESPONSE = (
    "Breathing trouble can become dangerous quickly. Call your local emergency number now or go to the nearest emergency room if breathing is difficult, worsening, noisy, associated with blue lips, chest pain, choking, or severe weakness.\n\n"
    "Sit upright if possible and avoid taking anything by mouth while struggling to breathe."
)

POISONING_OVERDOSE_EMERGENCY_RESPONSE = (
    "Poisoning or overdose needs urgent help. Call your local emergency number or poison control now, or go to the nearest emergency room.\n\n"
    "- Do not try to vomit unless a medical professional tells you to.\n"
    "- Keep the medicine/chemical/container with you for doctors.\n"
    "- Do not wait for Ayurvedic or home remedies."
)

SEIZURE_UNCONSCIOUS_EMERGENCY_RESPONSE = (
    "This needs urgent medical attention. Call your local emergency number now if someone is unconscious, not waking up, has repeated seizures, or a seizure lasts more than a few minutes.\n\n"
    "Keep the person on their side, move nearby hazards away, and do not put anything in their mouth."
)

ALLERGY_EMERGENCY_RESPONSE = (
    "This could be a severe allergic reaction. Call your local emergency number now if there is throat/tongue/face swelling, breathing trouble, dizziness, or widespread hives.\n\n"
    "Use an epinephrine auto-injector if one has been prescribed, and do not wait for Ayurvedic or home remedies."
)

BURN_EMERGENCY_RESPONSE = (
    "A severe, chemical, electrical, face/genital, or large burn needs urgent medical care. Call your local emergency number or go to the nearest emergency room.\n\n"
    "Cool the burn under clean running water if safe to do so. Do not apply herbs, ghee, oils, or powders to a serious burn."
)

PREGNANCY_EMERGENCY_RESPONSE = (
    "Bleeding or severe pain during pregnancy needs urgent medical care. Please contact your obstetrician immediately, call your local emergency number, or go to the nearest emergency room.\n\n"
    "Do not rely on Ayurvedic or home remedies for pregnancy bleeding or severe pregnancy pain."
)

URGENT_SAFETY_CATEGORIES = [
    (SELF_HARM_CRISIS_KEYWORDS, SELF_HARM_CRISIS_RESPONSE),
    (PREGNANCY_EMERGENCY_KEYWORDS, PREGNANCY_EMERGENCY_RESPONSE),
    (BLEEDING_EMERGENCY_KEYWORDS, BLEEDING_EMERGENCY_RESPONSE),
    (CHEST_PAIN_EMERGENCY_KEYWORDS, CHEST_PAIN_EMERGENCY_RESPONSE),
    (STROKE_EMERGENCY_KEYWORDS, STROKE_EMERGENCY_RESPONSE),
    (BREATHING_EMERGENCY_KEYWORDS, BREATHING_EMERGENCY_RESPONSE),
    (POISONING_OVERDOSE_EMERGENCY_KEYWORDS, POISONING_OVERDOSE_EMERGENCY_RESPONSE),
    (SEIZURE_UNCONSCIOUS_EMERGENCY_KEYWORDS, SEIZURE_UNCONSCIOUS_EMERGENCY_RESPONSE),
    (ALLERGY_EMERGENCY_KEYWORDS, ALLERGY_EMERGENCY_RESPONSE),
    (BURN_EMERGENCY_KEYWORDS, BURN_EMERGENCY_RESPONSE),
]


def contains_keyword(text, keywords):
    return any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords)


def contains_pattern(text, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def normalize_question(question):
    text = question.lower()
    text = re.sub(r"\bi['’]?m\b", " i am ", text)
    text = re.sub(r"\bm\b", " am ", text)
    text = re.sub(r"\bi['’]?ve\b", " i have ", text)
    text = re.sub(r"\bcant\b", " cannot ", text)
    text = re.sub(r"\bcan't\b", " cannot ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for typo, correction in COMMON_HEALTH_TYPOS.items():
        text = re.sub(rf"\b{re.escape(typo)}\b", correction, text)
    return f" {text} "


def extract_query_concern(question):
    normalized_question = normalize_question(question)
    searchable_keywords = (
        HEALTH_CONDITION_KEYWORDS
        | AYURVEDA_SCOPE_KEYWORDS
        | HEALTH_CONTEXT_KEYWORDS
        | CASUAL_HEALTH_PHRASES
    )
    matches = [
        keyword
        for keyword in searchable_keywords
        if re.search(rf"\b{re.escape(keyword)}\b", normalized_question)
    ]
    pattern_matches = [
        match.group(0)
        for pattern in HEALTH_CONDITION_PATTERNS
        for match in re.finditer(pattern, normalized_question)
    ]
    if pattern_matches:
        return max(pattern_matches, key=len).strip()

    specific_matches = [keyword for keyword in matches if keyword not in GENERIC_CONCERN_KEYWORDS]
    if specific_matches:
        return max(specific_matches, key=len)

    if matches:
        return max(matches, key=len)

    words = [
        word
        for word in normalized_question.strip().split()
        if word not in QUESTION_FILLER_WORDS and len(word) > 2
    ]
    return "this concern" if not words else " ".join(words[:4])


def format_concern_for_display(concern):
    return CONCERN_DISPLAY_NAMES.get(concern, concern)


def build_follow_up_questions(question, body_type=None):
    concern = format_concern_for_display(extract_query_concern(question))
    body_type_text = f" for my {body_type} body type" if body_type else " for my body type"
    return (
        "**Follow-up questions you can ask:**\n"
        f"- What Ayurvedic diet and drinks are best{body_type_text} while dealing with {concern}?\n"
        f"- Which daily routine changes can support recovery from {concern}{body_type_text}?\n"
        f"- Which warning signs with {concern} mean I should consult a doctor urgently?"
    )


def is_ayurveda_scope_query(question):
    normalized_question = normalize_question(question)
    has_off_topic_keyword = contains_keyword(normalized_question, OFF_TOPIC_KEYWORDS)
    if has_off_topic_keyword:
        return False

    has_ayurveda_or_health_keyword = contains_keyword(normalized_question, AYURVEDA_SCOPE_KEYWORDS)
    has_condition_keyword = contains_keyword(normalized_question, HEALTH_CONDITION_KEYWORDS)
    has_casual_health_phrase = contains_keyword(normalized_question, CASUAL_HEALTH_PHRASES)
    has_condition_pattern = contains_pattern(normalized_question, HEALTH_CONDITION_PATTERNS)
    has_health_context = contains_keyword(normalized_question, HEALTH_CONTEXT_KEYWORDS)
    has_health_action = contains_keyword(normalized_question, HEALTH_ACTION_KEYWORDS)

    return (
        has_ayurveda_or_health_keyword
        or has_condition_keyword
        or has_casual_health_phrase
        or has_condition_pattern
        or (has_health_context and has_health_action)
    )


def get_urgent_safety_response(question):
    normalized_question = normalize_question(question)
    for keywords, response in URGENT_SAFETY_CATEGORIES:
        if contains_keyword(normalized_question, keywords):
            return response
    return None


def format_scoped_response(message, body_type):
    if body_type:
        return f"For your {body_type} body type: {message}"
    return message


def ensure_follow_up_questions(result, question, body_type=None):
    answer_without_followups = re.split(
        r"\n\s*\*\*follow-up questions you can ask:\*\*",
        result,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].rstrip()
    return f"{answer_without_followups}\n\n{build_follow_up_questions(question, body_type)}"


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
        urgent_safety_response = get_urgent_safety_response(question)
        if urgent_safety_response:
            return {"result": urgent_safety_response, "body_type": body_type}

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
        result = ensure_follow_up_questions(result, question, body_type)
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
