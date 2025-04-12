import time
import streamlit as st
import pandas as pd
from io import StringIO
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
    "Сколько студентов по каждой специальности?"
]

# --- Check for ID input based on keywords ---
def check_for_id_input(user_input):
    keywords = ["студент", "преподаватель", "учитель", "администратор"]
    if any(keyword in user_input.lower() for keyword in keywords) and any(c.isdigit() for c in user_input):
        return True
    return False

# --- Suggested Questions Section ---
def show_suggested_questions():
    assistant_message_suggested = st.chat_message("assistant", avatar=avatar_url)
    if assistant_message_suggested.button("Click to show suggested questions"):
        st.session_state["my_question"] = None
        # If user input contains ID (check for keyword + digits), show real model questions
        if "user_input" in st.session_state and check_for_id_input(st.session_state["user_input"]):
            questions = generate_questions_cached()  # Use the model's questions
        else:
            questions = NEUTRAL_QUESTIONS  # Default neutral questions

        for question in questions:
            st.button(question, on_click=set_question, args=(question,))

# --- Chat Input ---
new_question = st.chat_input("Задайте вопрос о ваших данных")

if new_question:
    st.session_state["my_question"] = new_question
    st.session_state["df"] = None
    # Store user input for future checks
    st.session_state["user_input"] = new_question

# --- Render chat history ---
for entry in st.session_state.chat_history:
    st.chat_message("user").write(entry["question"])

    assistant_msg = st.chat_message("assistant", avatar=avatar_url)

    if st.session_state.get("show_sql", True):
        assistant_msg.code(entry["sql"], language="sql")

    if st.session_state.get("show_table", True) and entry.get("df") is not None:
        df = entry["df"]
        
        # Check if the dataframe has more than 10 rows
        if len(df) > 10:
            assistant_msg.text("Displaying first 10 rows of data:")
            assistant_msg.dataframe(df.head(10))  # Display first 10 rows with scroll
            # Provide a download link for the full dataset
            csv = df.to_csv(index=False)
            st.download_button(label="Download Full Data", data=csv, file_name="full_data.csv", mime="text/csv")
        else:
            assistant_msg.dataframe(df)

    if st.session_state.get("show_summary", True) and entry.get("summary"):
        assistant_msg.text(entry["summary"])

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
            summary = generate_summary_cached(question=my_question, df=df)
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
