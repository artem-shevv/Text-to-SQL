import time
import streamlit as st
from vanna_calls import (
    generate_questions_cached,
    generate_sql_cached,
    run_sql_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    generate_followup_cached,
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
st.sidebar.checkbox("Show Follow-up Questions", value=True, key="show_followup")

# --- Reset chat ---
if st.sidebar.button("Reset Chat", use_container_width=True):
    st.session_state.pop("chat_history", None)
    st.session_state.pop("my_question", None)
    st.session_state.pop("df", None)

# --- Init chat history ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Suggested Questions ---
def set_question(question):
    st.session_state["my_question"] = question
    st.session_state["df"] = None

st.title("Vanna AI")

assistant_message_suggested = st.chat_message("assistant", avatar=avatar_url)
if assistant_message_suggested.button("Click to show suggested questions"):
    st.session_state["my_question"] = None
    questions = generate_questions_cached()
    for question in questions:
        st.button(question, on_click=set_question, args=(question,))

# --- Chat Input ---
new_question = st.chat_input("Ask me a question about your data")

if new_question:
    st.session_state["my_question"] = new_question
    st.session_state["df"] = None

# --- Render chat history ---
for entry in st.session_state.chat_history:
    st.chat_message("user").write(entry["question"])

    assistant_msg = st.chat_message("assistant", avatar=avatar_url)

    if st.session_state.get("show_sql", True):
        assistant_msg.code(entry["sql"], language="sql")

    if st.session_state.get("show_table", True) and entry.get("df") is not None:
        df = entry["df"]
        if len(df) > 10:
            assistant_msg.text("First 10 rows of data")
            assistant_msg.dataframe(df.head(10))
        else:
            assistant_msg.dataframe(df)

    if st.session_state.get("show_summary", True) and entry.get("summary"):
        assistant_msg.text(entry["summary"])

    if st.session_state.get("show_followup", True) and entry.get("followups"):
        assistant_msg.text("Follow-up questions:")
        for q in entry["followups"][:5]:
            assistant_msg.button(q, on_click=set_question, args=(q,))

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
                assistant_msg.text("First 10 rows of data")
                assistant_msg.dataframe(df.head(10))
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

        # Follow-up
        followups = []
        if st.session_state.get("show_followup", True):
            followups = generate_followup_cached(question=my_question, sql=sql, df=df)
            if followups:
                followup_msg = st.chat_message("assistant", avatar=avatar_url)
                followup_msg.text("Follow-up questions:")
                for q in followups[:5]:
                    followup_msg.button(q, on_click=set_question, args=(q,))

        # Сохраняем всё в историю
        st.session_state.chat_history.append({
            "question": my_question,
            "sql": sql,
            "df": df,
            "summary": summary,
            "followups": followups
        })

        st.session_state["my_question"] = None
