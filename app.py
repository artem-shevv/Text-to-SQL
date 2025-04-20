import random
import logging
import traceback
import os
import streamlit as st
from vanna_calls import (
    generate_questions_cached,
    generate_sql_cached,
    run_sql_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    should_generate_chart_cached,
    is_sql_valid_cached,
    generate_summary_cached
)

avatar_url = "https://vanna.ai/img/vanna.svg"

st.set_page_config(layout="wide")

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

ENABLE_LOG_DOWNLOAD =  False#True

# --- Custom responsive styles ---
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-size: 14px;
        }

        @media (max-width: 768px) {
            html, body, [class*="css"] {
                font-size: 12px !important;
            }

            h1 {
                font-size: 18px !important;
                margin-top: 1rem !important; 
                margin-bottom: 0.5rem !important;
                text-align: center; 
            }

            button {
                font-size: 12px !important;
                padding: 4px 8px !important;
            }

            .stButton>button {
                height: auto !important;
                width: 100% !important;
            }

            [data-testid="stDecoration"] {
                display: none;
            }

            section[data-testid="stSidebar"] {
                padding: 0.5rem !important;
            }

            .markdown-text-container {
                font-size: 13px !important;
            }

            .stChatMessage {
                font-size: 13px !important;
            }

            .block-container {
                padding: 0.5rem 1rem 1rem 1rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar settings ---
st.sidebar.title("Output Settings")
st.sidebar.checkbox("Show SQL", value=True, key="show_sql")
st.sidebar.checkbox("Show Table", value=True, key="show_table")
st.sidebar.checkbox("Show Plotly Code", value=True, key="show_plotly_code")
st.sidebar.checkbox("Show Chart", value=True, key="show_chart")
st.sidebar.checkbox("Show Summary", value=True, key="show_summary")

# --- Reset chat ---
if st.sidebar.button("Reset Chat", use_container_width=True):
    st.session_state.pop("chat_history", None)
    st.session_state.pop("my_question", None)
    st.session_state.pop("df", None)
    st.session_state.pop("user_input", None)  
    st.session_state.pop("last_user_id", None)  # Reset last user ID

# --- Init chat history ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "show_suggestions" not in st.session_state:
    st.session_state["show_suggestions"] = False

# --- Suggested Questions ---
def set_question(question):
    st.session_state["my_question"] = question
    st.session_state["df"] = None

st.title("Vanna AI")

# --- Neutral questions ---
NEUTRAL_QUESTIONS = [
    "Сколько всего студентов обучается?",
    "Сколько преподавателей работает в институте?",
    "Сколько всего групп?",
    "Сколько групп на каждом курсе?",
    "Какие дисциплины ведёт каждый преподаватель?",
    "Сколько студентов обучается на каждой специальности?"
]

# --- Check for ID input based on keywords ---
def check_for_id_input(user_input):
    keywords = ["студент", "преподаватель", "учитель", "администратор"]
    if any(keyword in user_input.lower() for keyword in keywords) and any(c.isdigit() for c in user_input):
        return True
    return False

# --- Определение роли по вводу пользователя ---
def get_user_role(user_input):
    roles = {
        "студент": ["студент", "ученик"],
        "преподаватель": ["преподаватель", "учитель", "педагог"],
        "администратор": ["администратор"]
    }

    if any(c.isdigit() for c in user_input):
        lower_input = user_input.lower()
        for role, keywords in roles.items():
            if any(keyword in lower_input for keyword in keywords):
                return role
    return None

# --- Категоризация сгенерированных вопросов ---
def categorize_questions(questions):
    categorized = {
        "student": [],
        "teacher": [],
        "admin": [],
        "neutral": []
    }

    for q in questions:
        q_clean = q.strip()
        if q_clean.endswith("Я студент"):
            categorized["student"].append(q)
        elif q_clean.endswith("Я преподаватель"):
            categorized["teacher"].append(q)
        elif "Я студент" in q_clean or "Я преподаватель" in q_clean:
            # Исключаем вопросы, содержащие "Я студент" или "Я преподаватель"
            continue
        elif "Я администратор" in q_clean:
            categorized["admin"].append(q)
        else:
            categorized["neutral"].append(q)

    return categorized

# --- Очистка конца вопроса ---
def clean_question_text(q):
    if not isinstance(q, str):
        return ""

    split_chars = ['?', '.']
    min_index = min([q.find(c) for c in split_chars if c in q] + [len(q)])

    cleaned = q[:min_index + 1] if min_index < len(q) else q
    return cleaned.strip()

# --- Отображение рекомендованных вопросов ---
def show_suggested_questions():
    if "show_suggestions" not in st.session_state:
        st.session_state["show_suggestions"] = False

    assistant_message_suggested = st.chat_message("assistant", avatar=avatar_url)
    if assistant_message_suggested.button("Click to show suggested questions"):
        st.session_state["show_suggestions"] = not st.session_state["show_suggestions"]
        st.session_state["my_question"] = None

    if st.session_state["show_suggestions"]:
        user_input = st.session_state.get("user_input", "")
        user_role = get_user_role(user_input)

        if user_role:
            all_questions = generate_questions_cached()
            categorized = categorize_questions(all_questions)

            max_total = 6
            n_personal = random.randint(2, max_total - 2)
            n_neutral = max_total - n_personal

            role_map = {
                "студент": "student",
                "преподаватель": "teacher",
                "администратор": "admin"
            }

            role_key = role_map.get(user_role, "neutral")

            if user_role == "администратор":
                # Для администратора показываем только нейтральные вопросы
                selected_questions = categorized.get("neutral", [])[:n_neutral]
            else:
                # Для остальных ролей — комбинируем персонализированные и нейтральные вопросы
                personalized = categorized.get(role_key, [])[:n_personal]
                neutrals = categorized.get("neutral", [])[:n_neutral]
                selected_questions = personalized + neutrals

            random.shuffle(selected_questions)
        else:
            selected_questions = NEUTRAL_QUESTIONS

        # 👇 Очистка вопросов только для отображения
        for i, question in enumerate(selected_questions):
            short_q = clean_question_text(question)
            st.button(short_q, on_click=set_question, args=(short_q,), key=f"suggested_q_{i}")

# --- Chat Input ---
st.markdown("### Тестовые запросы:")

# Список всех тестовых запросов
test_questions = [
    "🎓 Я студент 11111-222, когда у меня день рождения?",
    "Я студент 11112-222, кто староста моей группы?",
    "Я студент 11113-222, что я изучу за время учёбы на этом направлении подготовки?",
    "👨‍🏫 Я преподаватель 62-180-5657, какие дисциплины я преподаю?",
    "Я преподаватель 62-180-5657, сколько студентов я обучаю?",
    "Я преподаватель 62-180-5657, какой у меня номер телефона?",
    "🧑‍💼 Я администратор 08-731-2673, сколько студентов обучается на каждой специальности?",
    "Я администратор 08-731-2673, какие дисциплины ведёт каждый преподаватель?",
    "Я администратор 08-731-2673, сколько преподавателей работает в институте?"
]

# Состояние страницы
if "test_question_page" not in st.session_state:
    st.session_state["test_question_page"] = 0

# Флаг нажатия переключателя
if "carousel_advance" not in st.session_state:
    st.session_state["carousel_advance"] = False

# Обработка нажатия кнопки переключения
def advance_carousel():
    st.session_state["test_question_page"] = (st.session_state["test_question_page"] + 1) % (len(test_questions) // 3)
    st.session_state["carousel_advance"] = True

    # Очистка истории и контекста модели
    st.session_state.pop("chat_history", None)
    st.session_state.pop("my_question", None)
    st.session_state.pop("df", None)
    st.session_state.pop("user_input", None)

# Интерфейс кнопок
start_index = st.session_state["test_question_page"] * 3
current_questions = test_questions[start_index:start_index + 3]

cols = st.columns([4, 4, 4, 1])  # Последняя колонка — под ⏭️

# Основные кнопки
for i, col in enumerate(cols[:3]):
    if i < len(current_questions):
        q = current_questions[i]
        with col:
            if st.button(q, key=f"question_button_{start_index + i}"):
                st.session_state["my_question"] = q
                st.session_state["df"] = None
                st.session_state["user_input"] = q
                # Сброс флага переключения
                st.session_state["carousel_advance"] = False

# Кнопка переключения страниц
with cols[3]:
    st.button("🔄", key="next_page", on_click=advance_carousel, help="Показать другие примеры")


new_question = st.chat_input("Задайте вопрос о ваших данных")

if new_question:
    st.session_state["my_question"] = new_question
    st.session_state["df"] = None
    # Store user input for future checks
    st.session_state["user_input"] = new_question

# --- Render chat history ---
for i, entry in enumerate(st.session_state.chat_history):
    st.chat_message("user").write(entry["question"])
    assistant_msg = st.chat_message("assistant", avatar=avatar_url)

    if st.session_state.get("show_sql", True):
        assistant_msg.code(entry["sql"], language="sql")

    if st.session_state.get("show_table", True) and entry.get("df") is not None:
        df = entry["df"]
        if len(df) > 10:
            assistant_msg.text("First 10 rows of data")
            assistant_msg.dataframe(df.head(10))

            csv = df.to_csv(index=False)

            unique_key = f"download_button_{i}_{id(entry)}"

            st.download_button(
                label=f"Download Full Data (Q{i+1})",
                data=csv,
                file_name=f"full_data_{i}.csv",
                mime="text/csv",
                key=unique_key
            )
        else:
            assistant_msg.dataframe(df)

    if st.session_state.get("show_chart", True) and entry.get("df") is not None and entry.get("question") and entry.get("sql"):
        if should_generate_chart_cached(question=entry["question"], sql=entry["sql"], df=entry["df"]):
            code = generate_plotly_code_cached(question=entry["question"], sql=entry["sql"], df=entry["df"])
            if st.session_state.get("show_plotly_code", False):
                assistant_msg.code(code, language="python")
            if code:
                fig = generate_plot_cached(code=code, df=entry["df"])
                if fig:
                    assistant_msg.plotly_chart(fig)

    if st.session_state.get("show_summary", True):
        summary = entry.get("summary")
        if not summary:
            summary = generate_summary_cached(question=entry["question"] + " (ответь на русском)", df=entry["df"])
            entry["summary"] = summary
        if summary:
            assistant_msg.text(summary)

# --- Обработка нового вопроса ---
my_question = st.session_state.get("my_question", None)

if my_question:
    st.chat_message("user").write(my_question)

    try:
        logging.info(f"Новый вопрос: {my_question}")

        # Сбор контекста из истории
        def df_to_string(df):
            if df is None or df.empty:
                return "No data"
            return df.head(5).to_csv(index=False)

        recent_context = st.session_state.chat_history[-5:]
        context_parts = []
        for entry in recent_context:
            part = f"Q: {entry['question']}\nSQL: {entry['sql']}"
            if entry.get("df") is not None:
                part += f"\nDATA:\n{df_to_string(entry['df'])}"
            context_parts.append(part)

        context_text = "\n\n".join(context_parts)
        full_question = f"{context_text}\n\nQ: {my_question}" if context_text else my_question

        # Генерация SQL
        sql = generate_sql_cached(question=full_question)
        logging.info(f"Сгенерированный SQL: {sql}")

        if not sql or not is_sql_valid_cached(sql=sql):
            logging.error("Сгенерированный SQL некорректен")
            st.chat_message("assistant", avatar=avatar_url).error("Generated SQL is invalid.")
            st.stop()

        # Запуск SQL
        df = run_sql_cached(sql=sql)
        if df is None or df.empty:
            logging.info("SQL-запрос не вернул данных")
            #st.chat_message("assistant", avatar=avatar_url).error("Query returned no data.")
            #st.stop()

        logging.info(f"Успешно выполнен SQL-запрос. Кол-во строк: {len(df)}")

        # Сохраняем DataFrame
        st.session_state["df"] = df

        # Показываем SQL, таблицу, график (если нужно)
        if st.session_state.get("show_sql", True):
            st.chat_message("assistant", avatar=avatar_url).code(sql, language="sql")

        if st.session_state.get("show_table", True):
            assistant_msg = st.chat_message("assistant", avatar=avatar_url)
            if len(df) > 10:
                assistant_msg.text("Displaying first 10 rows of data:")
                assistant_msg.dataframe(df.head(10))
                csv = df.to_csv(index=False)
                st.download_button(label="Download Full Data", data=csv, file_name="full_data.csv", mime="text/csv")
            else:
                assistant_msg.dataframe(df)

        # Summary
        summary = None
        if st.session_state.get("show_summary", True):
            summary = generate_summary_cached(question=my_question + " (ответь на русском языке)", df=df)
            if summary:
                st.chat_message("assistant", avatar=avatar_url).text(summary)

        # Сохраняем в историю
        st.session_state.chat_history.append({
            "question": my_question,
            "sql": sql,
            "df": df,
            "summary": summary
        })

        st.session_state["my_question"] = None

    except Exception as e:
        error_trace = traceback.format_exc()
        logging.error(f"Ошибка при обработке запроса: {str(e)}\n{error_trace}")
        st.chat_message("assistant", avatar=avatar_url).error("⚠️ Произошла ошибка при обработке запроса.")

if ENABLE_LOG_DOWNLOAD:
    if os.path.exists("app.log"):
        with open("app.log", "r") as f:
            st.sidebar.download_button("Download log", f.read(), file_name="app.log", mime="text/plain", use_container_width=True)

# --- Show suggested questions ---
show_suggested_questions()
