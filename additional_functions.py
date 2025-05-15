import streamlit as st
from vanna_calls import (
    generate_questions_cached
)
avatar_url = "https://vanna.ai/img/vanna.svg"


NEUTRAL_QUESTIONS = [
    "Сколько всего студентов обучается?",
    "Сколько преподавателей работает в институте?",
    "Сколько всего групп?",
    "Сколько групп на каждом курсе?",
    "Какие дисциплины ведёт каждый преподаватель?",
    "Сколько студентов обучается на каждой специальности?"
]

# Suggested Questions 
def set_question(question):
    st.session_state["my_question"] = question
    st.session_state["df"] = None

# Categorization of generated questions 
def categorize_questions(questions):
    categorized = {
        "student": [],
        "teacher": [],
        "admin": [],
        "neutral": []
    }

    for q in questions:
        if not isinstance(q, str):
            continue
            
        q_clean = q.strip().lower()
        if "я студент" in q_clean:
            categorized["student"].append(q)
        elif "я преподаватель" in q_clean or "я учитель" in q_clean:
            categorized["teacher"].append(q)
        elif "я администратор" in q_clean:
            categorized["admin"].append(q)
        else:
            categorized["neutral"].append(q)

    return categorized


# Clearing the end of the question 
def clean_question_text(q):
    if not isinstance(q, str):
        return ""

    split_chars = ['?', '.']
    min_index = min([q.find(c) for c in split_chars if c in q] + [len(q)])

    cleaned = q[:min_index + 1] if min_index < len(q) else q
    return cleaned.strip()


# Displaying recommended questions 
def show_suggested_questions():
    if "show_suggestions" not in st.session_state:
        st.session_state["show_suggestions"] = False

    assistant_message_suggested = st.chat_message("assistant", avatar=avatar_url)
    if assistant_message_suggested.button("Показать рекомендуемые вопросы"):
        st.session_state["show_suggestions"] = not st.session_state["show_suggestions"]
        st.session_state["my_question"] = None

    if st.session_state["show_suggestions"]:
        user_role = st.session_state.user["role"]
        
        # Generate questions via Wanna
        all_questions = generate_questions_cached()
        categorized = categorize_questions(all_questions)

        # Determining which questions to show
        if user_role == "administrator":
            # For the administrator take neutral questions from Vanna
            vanna_questions = categorized.get("neutral", [])
            
            # Take up to 6 questions: first from Vanna, then from the neutral
            selected_questions = vanna_questions[:6]
            remaining = 6 - len(selected_questions)
            
            if remaining > 0:
                selected_questions.extend(NEUTRAL_QUESTIONS[:remaining])
        else:
            role_key = "student" if user_role == "student" else "teacher"
            personalized = categorized.get(role_key, [])[:3]
            neutrals = categorized.get("neutral", [])[:3]
            selected_questions = personalized + neutrals
            
            # If Vanna didn't return questions use the neutral
            if not selected_questions:
                selected_questions = NEUTRAL_QUESTIONS[:6]

        # Clearing the questions for display(shorter part)
        for i, question in enumerate(selected_questions):
            short_q = clean_question_text(question)
            st.button(short_q, on_click=set_question, args=(short_q,), key=f"suggested_q_{i}")

# Collecting context from a story
def df_to_string(df):
    if df is None or df.empty:
        return "No data"
    return df.head(5).to_csv(index=False)

def get_name_role(role):
    role_mapping = {
        "student": "студент",
        "teacher": "преподаватель",
        "administrator": "администратор"
    }
    return role_mapping.get(role.lower(), role)

def get_role_specific_questions(role):
    role_questions = {
        "student": [
            "Когда у меня день рождения?",
            "Кто староста моей группы?",
            "Что я изучу за время учёбы на этом направлении подготовки?"
        ],
        "teacher": [
            "Какие дисциплины я преподаю?",
            "Сколько студентов я обучаю?",
            "Какой у меня номер телефона?"
        ],
        "administrator": [
            "Сколько студентов обучается на каждой специальности?",
            "Какие дисциплины ведёт каждый преподаватель?",
            "Сколько преподавателей работает в институте?"
        ]
    }
    return role_questions.get(role, [])