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
                margin-top: 1rem !important; /* добавим отступ сверху */
                margin-bottom: 0.5rem !important;
                text-align: center; /* чтобы смотрелось аккуратно */
            }

            /* Остальные стили */
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
    st.session_state.pop("user_input", None)  # Reset the user input flag for ID check

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

# --- Suggested Questions Section ---
def show_suggested_questions():
    if "show_suggestions" not in st.session_state:
        st.session_state["show_suggestions"] = False

    assistant_message_suggested = st.chat_message("assistant", avatar=avatar_url)
    if assistant_message_suggested.button("Click to show suggested questions"):
        st.session_state["show_suggestions"] = not st.session_state["show_suggestions"]
        st.session_state["my_question"] = None

    if st.session_state["show_suggestions"]:
        if "user_input" in st.session_state and check_for_id_input(st.session_state["user_input"]):
            questions = generate_questions_cached()  # Use the model's questions
        else:
            questions = NEUTRAL_QUESTIONS  # Default neutral questions

        for i, question in enumerate(questions):
            st.button(question, on_click=set_question, args=(question,), key=f"suggested_q_{i}")



# --- Chat Input ---
# --- Быстрые кнопки с вопросами ---
st.markdown("### Быстрые вопросы:")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎓 Я студент 11111-222, когда у меня день рождения?"):
        st.session_state["my_question"] = "Я студент 11111-222, когда у меня день рождения?"
        st.session_state["df"] = None
        st.session_state["user_input"] = st.session_state["my_question"]

with col2:
    if st.button("👨‍🏫 Я преподаватель 62-180-5657, какие дисциплины я преподаю?"):
        st.session_state["my_question"] = "Я преподаватель 62-180-5657, какие дисциплины я преподаю?"
        st.session_state["df"] = None
        st.session_state["user_input"] = st.session_state["my_question"]

with col3:
    if st.button("🧑‍💼 Я администратор 08-731-2673, сколько студентов обучается на каждой специальности?"):
        st.session_state["my_question"] = "Я администратор 08-731-2673, сколько студентов обучается на каждой специальности?"
        st.session_state["df"] = None
        st.session_state["user_input"] = st.session_state["my_question"]




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

    # Сбор контекста из истории (включая SQL и данные)
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


    sql = generate_sql_cached(question=full_question)

    if sql:
        if not is_sql_valid_cached(sql=sql):
            st.chat_message("assistant", avatar=avatar_url).error("Generated SQL is invalid.")
            st.stop()

        if st.session_state.get("show_sql", True):
            st.chat_message("assistant", avatar=avatar_url).code(sql, language="sql")

        df = run_sql_cached(sql=sql)
        if df is not None:
            st.session_state["df"] = df
        else:
            st.chat_message("assistant", avatar=avatar_url).error("Query returned no data.")
            st.stop()

        # Показываем таблицу
        if st.session_state.get("show_table", True):
            assistant_msg = st.chat_message("assistant", avatar=avatar_url)
            if len(df) > 10:
                assistant_msg.text("Displaying first 10 rows of data:")
                assistant_msg.dataframe(df.head(10))  # Display first 10 rows with scroll
                # Provide a download link for the full dataset
                csv = df.to_csv(index=False)
                st.download_button(label="Download Full Data", data=csv, file_name="full_data.csv", mime="text/csv")
            else:
                assistant_msg.dataframe(df)

        # Чарт
        if should_generate_chart_cached(question=my_question, sql=sql, df=df):
            code = generate_plotly_code_cached(question=my_question, sql=sql, df=df)
            if st.session_state.get("show_plotly_code", False):
                st.chat_message("assistant", avatar=avatar_url).code(code, language="python")
            if st.session_state.get("show_chart", True) and code:
                fig = generate_plot_cached(code=code, df=df)
                if fig:
                    st.chat_message("assistant", avatar=avatar_url).plotly_chart(fig)

        # Summary
        summary = None
        if st.session_state.get("show_summary", True):
            summary = generate_summary_cached(question=my_question + " (ответь на русском языке)", df=df)
            if summary:
                st.chat_message("assistant", avatar=avatar_url).text(summary)

        # Сохраняем всё в историю
        st.session_state.chat_history.append({
            "question": my_question,
            "sql": sql,
            "df": df,
            "summary": summary
        })

        st.session_state["my_question"] = None

# --- Show suggested questions ---
show_suggested_questions()
