import streamlit as st


QUESTIONS = [
    {
        "category": "Physical Build",
        "question": "What best describes your body frame?",
        "options": {
            "Vata": "Thin, light, delicate frame",
            "Pitta": "Medium build, muscular, well-proportioned",
            "Kapha": "Large, solid, heavy frame",
        },
    },
    {
        "category": "Physical Build",
        "question": "How would you describe your weight?",
        "options": {
            "Vata": "Underweight or difficulty gaining weight",
            "Pitta": "Normal weight, easy to maintain",
            "Kapha": "Overweight or tendency to gain weight easily",
        },
    },
    {
        "category": "Physical Build",
        "question": "What about your height?",
        "options": {
            "Vata": "Very tall or very short",
            "Pitta": "Average height",
            "Kapha": "Short to medium height",
        },
    },
    {
        "category": "Physical Build",
        "question": "How are your joints?",
        "options": {
            "Vata": "Thin, prominent, cracking sounds",
            "Pitta": "Medium-sized, well-formed",
            "Kapha": "Large, well-padded, smooth",
        },
    },
    {
        "category": "Skin",
        "question": "What best describes your skin?",
        "options": {
            "Vata": "Dry, thin, cool, rough",
            "Pitta": "Warm, sensitive, prone to rashes",
            "Kapha": "Oily, thick, cool, smooth",
        },
    },
    {
        "category": "Skin",
        "question": "How does your skin react to sun?",
        "options": {
            "Vata": "Burns easily, tans poorly",
            "Pitta": "Burns easily, tans well",
            "Kapha": "Tans easily, rarely burns",
        },
    },
    {
        "category": "Skin",
        "question": "What about moles and freckles?",
        "options": {
            "Vata": "Few or none",
            "Pitta": "Many moles and freckles",
            "Kapha": "Some, but not many",
        },
    },
    {
        "category": "Hair",
        "question": "What describes your hair best?",
        "options": {
            "Vata": "Dry, thin, curly, brittle",
            "Pitta": "Fine, straight, early graying",
            "Kapha": "Thick, oily, wavy, lustrous",
        },
    },
    {
        "category": "Hair",
        "question": "How is your hair growth?",
        "options": {
            "Vata": "Slow growth, prone to breakage",
            "Pitta": "Normal growth, early graying",
            "Kapha": "Fast growth, thick and strong",
        },
    },
    {
        "category": "Eyes",
        "question": "What best describes your eyes?",
        "options": {
            "Vata": "Small, dry, dark, restless",
            "Pitta": "Medium, sharp, light-colored, penetrating",
            "Kapha": "Large, attractive, thick lashes, calm",
        },
    },
    {
        "category": "Eyes",
        "question": "How do your eyes feel?",
        "options": {
            "Vata": "Dry, tired, sensitive to light",
            "Pitta": "Burning, bloodshot when stressed",
            "Kapha": "Watery, heavy, droopy",
        },
    },
    {
        "category": "Digestion",
        "question": "How is your appetite?",
        "options": {
            "Vata": "Irregular, sometimes forget to eat",
            "Pitta": "Strong, regular, can't skip meals",
            "Kapha": "Steady, can skip meals easily",
        },
    },
    {
        "category": "Digestion",
        "question": "What about your digestion?",
        "options": {
            "Vata": "Irregular, gas, bloating",
            "Pitta": "Strong, quick, sometimes loose stools",
            "Kapha": "Slow, steady, heavy feeling after meals",
        },
    },
    {
        "category": "Digestion",
        "question": "How do you feel about spicy food?",
        "options": {
            "Vata": "Can't handle much spice",
            "Pitta": "Love spicy food, crave it",
            "Kapha": "Moderate spice tolerance",
        },
    },
    {
        "category": "Energy",
        "question": "What describes your energy pattern?",
        "options": {
            "Vata": "Bursts of energy, then tired",
            "Pitta": "Steady, intense energy",
            "Kapha": "Slow to start, steady endurance",
        },
    },
    {
        "category": "Energy",
        "question": "How do you handle physical activity?",
        "options": {
            "Vata": "Love variety, get bored easily",
            "Pitta": "Intense, competitive activities",
            "Kapha": "Steady, routine activities",
        },
    },
    {
        "category": "Energy",
        "question": "What about your sleep pattern?",
        "options": {
            "Vata": "Light sleeper, irregular hours",
            "Pitta": "Moderate sleep, wake up hot",
            "Kapha": "Deep sleeper, hard to wake up",
        },
    },
    {
        "category": "Mental",
        "question": "How do you learn best?",
        "options": {
            "Vata": "Quick to learn, quick to forget",
            "Pitta": "Sharp, focused, analytical",
            "Kapha": "Slow to learn, excellent memory",
        },
    },
    {
        "category": "Mental",
        "question": "What about your decision making?",
        "options": {
            "Vata": "Quick decisions, change mind often",
            "Pitta": "Decisive, logical, sometimes impulsive",
            "Kapha": "Slow, deliberate, stick to decisions",
        },
    },
    {
        "category": "Mental",
        "question": "How do you handle stress?",
        "options": {
            "Vata": "Worry, anxiety, scattered thoughts",
            "Pitta": "Anger, irritability, criticism",
            "Kapha": "Withdrawal, denial, avoidance",
        },
    },
    {
        "category": "Emotional",
        "question": "What's your typical mood?",
        "options": {
            "Vata": "Enthusiastic, anxious, changeable",
            "Pitta": "Intense, passionate, irritable",
            "Kapha": "Calm, content, sometimes lethargic",
        },
    },
    {
        "category": "Emotional",
        "question": "How do you express emotions?",
        "options": {
            "Vata": "Quick to laugh or cry, expressive",
            "Pitta": "Intense, direct, sometimes harsh",
            "Kapha": "Steady, slow to anger, nurturing",
        },
    },
    {
        "category": "Weather",
        "question": "What weather do you prefer?",
        "options": {
            "Vata": "Warm, humid weather",
            "Pitta": "Cool, dry weather",
            "Kapha": "Warm, dry weather",
        },
    },
    {
        "category": "Weather",
        "question": "How do you handle cold weather?",
        "options": {
            "Vata": "Very sensitive to cold",
            "Pitta": "Moderate tolerance",
            "Kapha": "Good tolerance, prefer it",
        },
    },
    {
        "category": "General",
        "question": "What about your voice?",
        "options": {
            "Vata": "High-pitched, fast, talkative",
            "Pitta": "Sharp, clear, commanding",
            "Kapha": "Deep, slow, melodious",
        },
    },
    {
        "category": "General",
        "question": "How do you walk?",
        "options": {
            "Vata": "Fast, light, irregular pace",
            "Pitta": "Purposeful, determined stride",
            "Kapha": "Slow, steady, graceful",
        },
    },
]


DOSHA_CHARACTERISTICS = {
    "Vata": {
        "name": "Vata Dosha",
        "elements": "Air + Space",
        "qualities": "Cold, dry, light, mobile, rough, subtle",
        "description": "Vata governs movement, circulation, breathing, and elimination. People with dominant Vata are creative, energetic, and quick-thinking.",
        "physical_traits": [
            "Thin, light build",
            "Dry skin and hair",
            "Cold hands and feet",
            "Irregular appetite and digestion",
            "Light, interrupted sleep",
        ],
        "mental_traits": [
            "Quick to learn and forget",
            "Creative and artistic",
            "Enthusiastic and energetic",
            "Anxious when out of balance",
            "Tendency to worry",
        ],
        "recommendations": {
            "diet": [
                "Warm, cooked foods",
                "Sweet, sour, and salty tastes",
                "Regular meal times",
                "Avoid cold, raw foods",
                "Include healthy fats like ghee and olive oil",
            ],
            "lifestyle": [
                "Regular routine and schedule",
                "Gentle, grounding exercises like yoga",
                "Warm oil massage (abhyanga)",
                "Adequate rest and sleep",
                "Avoid excessive travel and stimulation",
            ],
            "herbs": [
                "Ashwagandha (for grounding)",
                "Brahmi (for mental calm)",
                "Shatavari (for nourishment)",
                "Triphala (for digestion)",
                "Ginger (for warming)",
            ],
        },
    },
    "Pitta": {
        "name": "Pitta Dosha",
        "elements": "Fire + Water",
        "qualities": "Hot, sharp, light, oily, liquid, mobile",
        "description": "Pitta governs digestion, metabolism, and transformation. People with dominant Pitta are intelligent, focused, and natural leaders.",
        "physical_traits": [
            "Medium build, muscular",
            "Warm skin, prone to rashes",
            "Strong appetite and digestion",
            "Good circulation",
            "Tendency to overheat",
        ],
        "mental_traits": [
            "Sharp intellect and memory",
            "Focused and determined",
            "Natural leadership qualities",
            "Perfectionist tendencies",
            "Can be critical when imbalanced",
        ],
        "recommendations": {
            "diet": [
                "Cooling foods and drinks",
                "Sweet, bitter, and astringent tastes",
                "Avoid spicy, sour, salty foods",
                "Fresh fruits and vegetables",
                "Moderate protein intake",
            ],
            "lifestyle": [
                "Cool, calm environment",
                "Regular exercise, avoid overheating",
                "Meditation and relaxation",
                "Avoid excessive competition",
                "Regular meal times",
            ],
            "herbs": [
                "Amla (for cooling)",
                "Neem (for purification)",
                "Brahmi (for mental calm)",
                "Shatavari (for cooling)",
                "Coriander (for digestion)",
            ],
        },
    },
    "Kapha": {
        "name": "Kapha Dosha",
        "elements": "Earth + Water",
        "qualities": "Heavy, slow, cool, oily, smooth, dense",
        "description": "Kapha governs structure, stability, and lubrication. People with dominant Kapha are calm, loving, and have great endurance.",
        "physical_traits": [
            "Large, solid build",
            "Oily, smooth skin",
            "Thick, lustrous hair",
            "Strong bones and joints",
            "Slow metabolism",
        ],
        "mental_traits": [
            "Calm and steady",
            "Excellent memory",
            "Loving and nurturing",
            "Slow to anger",
            "Tendency toward complacency",
        ],
        "recommendations": {
            "diet": [
                "Light, warm foods",
                "Pungent, bitter, astringent tastes",
                "Avoid heavy, oily foods",
                "Eat smaller portions",
                "Include warming spices",
            ],
            "lifestyle": [
                "Regular vigorous exercise",
                "Variety and stimulation",
                "Early morning routine",
                "Avoid excessive sleep",
                "Stay active and engaged",
            ],
            "herbs": [
                "Ginger (for stimulation)",
                "Turmeric (for purification)",
                "Triphala (for digestion)",
                "Brahmi (for mental clarity)",
                "Tulsi (for energy)",
            ],
        },
    },
}


def get_dosha_icon(dosha: str) -> str:
    return {
        "Vata": "🌪️",
        "Pitta": "🔥",
        "Kapha": "🌊",
    }.get(dosha, "🧘‍♀️")


def get_dosha_color(dosha: str) -> str:
    return {
        "Vata": "#E3F2FD",
        "Pitta": "#FFF3E0",
        "Kapha": "#E8F5E8",
    }.get(dosha, "#F5F5F5")


class DoshaAssessment:
    def __init__(self, form_key: str = "dosha_assessment_form"):
        self.form_key = form_key
        self.questions = self._load_questions()
        self.dosha_characteristics = self._load_dosha_characteristics()

    def _load_questions(self):
        return QUESTIONS

    def _load_dosha_characteristics(self):
        return DOSHA_CHARACTERISTICS

    def calculate_dosha_scores(self, answers):
        scores = {"Vata": 0, "Pitta": 0, "Kapha": 0}
        for answer in answers:
            if answer in scores:
                scores[answer] += 1
        return scores

    def determine_primary_dosha(self, scores):
        primary_dosha = max(scores, key=scores.get)
        total_score = sum(scores.values())
        percentages = {
            dosha: round((score / total_score) * 100, 1) if total_score > 0 else 0
            for dosha, score in scores.items()
        }
        return primary_dosha, percentages

    def get_dosha_analysis(self, primary_dosha, percentages):
        dosha = self.dosha_characteristics[primary_dosha]
        sorted_doshas = sorted(percentages.items(), key=lambda item: item[1], reverse=True)
        secondary_dosha, secondary_percentage = sorted_doshas[1]

        def bullet_list(items):
            return "\n".join(f"- {item}" for item in items)

        analysis = f"""# Your Ayurvedic Body Type Assessment

## {get_dosha_icon(primary_dosha)} Primary Dosha: {dosha["name"]} ({percentages[primary_dosha]}%)

**Elements:** {dosha["elements"]}

**Qualities:** {dosha["qualities"]}

{dosha["description"]}

## Dosha Breakdown

- Vata: {percentages["Vata"]}%
- Pitta: {percentages["Pitta"]}%
- Kapha: {percentages["Kapha"]}%

## Physical Characteristics

{bullet_list(dosha["physical_traits"])}

## Mental Characteristics

{bullet_list(dosha["mental_traits"])}

## Dietary Recommendations

{bullet_list(dosha["recommendations"]["diet"])}

## Lifestyle Recommendations

{bullet_list(dosha["recommendations"]["lifestyle"])}

## Beneficial Herbs

{bullet_list(dosha["recommendations"]["herbs"])}
"""

        if secondary_percentage > 20:
            secondary = self.dosha_characteristics[secondary_dosha]
            secondary_diet = bullet_list(secondary["recommendations"]["diet"][:3])
            analysis += f"""

## Secondary Dosha Influence

Your {secondary["name"]} influence is also meaningful at {secondary_percentage}%. Consider these supportive diet notes:

{secondary_diet}
"""

        analysis += """

## Key Insights

- Your constitution is a starting point for understanding natural tendencies.
- Balance is influenced by season, age, diet, lifestyle, stress, and environment.
- Small, consistent routine changes are usually more helpful than extreme changes.

**Educational disclaimer:** This assessment is for educational wellness guidance only and is not a medical diagnosis. Consult a qualified healthcare professional for medical concerns, persistent symptoms, pregnancy, chronic conditions, or medication-related questions.
"""
        return analysis

    def run_assessment(self):
        st.markdown(
            """
            <div style="background-color:#F0FCED; padding:16px; border-radius:10px; margin-bottom:18px;">
                <h3 style="color:#22543D; margin:0;">Know Your Body Type</h3>
                <p style="margin:8px 0 0 0;">Choose the option that most closely matches your long-term natural tendencies.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answers = []
        current_category = None

        with st.form(self.form_key):
            for idx, question in enumerate(self.questions):
                if question["category"] != current_category:
                    current_category = question["category"]
                    st.markdown(f"### {current_category}")

                options = list(question["options"].keys())
                answer = st.radio(
                    question["question"],
                    options,
                    key=f"{self.form_key}_question_{idx}",
                    format_func=lambda dosha, opts=question["options"]: opts[dosha],
                    index=None,
                )
                answers.append(answer)

            submitted = st.form_submit_button("Submit Assessment", use_container_width=True, type="primary")

        if not submitted:
            return None

        if any(answer is None for answer in answers):
            unanswered_count = sum(answer is None for answer in answers)
            st.error(f"Please answer all questions before submitting. {unanswered_count} question(s) are still unanswered.")
            return None

        scores = self.calculate_dosha_scores(answers)
        primary_dosha, percentages = self.determine_primary_dosha(scores)
        analysis = self.get_dosha_analysis(primary_dosha, percentages)
        return {
            "primary_dosha": primary_dosha,
            "percentages": percentages,
            "scores": scores,
            "analysis": analysis,
        }
