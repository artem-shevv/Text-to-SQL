import logging
import traceback
import streamlit as st
from auth_module import show_login_form
from vanna_calls import (
    generate_sql_cached,
    generate_summary_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    should_generate_chart_cached,
    is_sql_valid_cached,
    run_sql_cached
)
from checker_injection_calls import (
    is_sql_injection
)
from additional_functions import (
    show_suggested_questions,
    df_to_string,
    get_name_role,
    get_role_specific_questions,
    avatar_url
)


# Check auth
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None 

if not st.session_state["authenticated"]:
    from auth_module import show_login_form
    show_login_form()
    st.stop()


st.set_page_config(layout="wide")

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Mobile view 
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

# Sidebar settings 
st.sidebar.title("Output Settings")

# Add info about user
st.sidebar.markdown("---")
st.sidebar.markdown("### Информация о пользователе")

# Get true role, id
true_role = get_name_role(st.session_state.user['role'])
user_id = st.session_state.user["original_id"]

# Show info for personal role
if st.session_state.user["role"] == "student":
    st.sidebar.markdown(f"**Роль:** {true_role}\n\n📚 **Номер:** {user_id}")
elif st.session_state.user["role"] == "teacher":
    st.sidebar.markdown(f"**Роль:** {true_role}\n\n📝 **Номер:** {user_id}")
else:
    st.sidebar.markdown(f"**Роль:** {true_role}\n\n🔑 **Номер:** {user_id}")

st.sidebar.markdown("---")
st.sidebar.checkbox("Show SQL", value=True, key="show_sql")
st.sidebar.checkbox("Show Table", value=True, key="show_table")
st.sidebar.checkbox("Show Plotly Code", value=True, key="show_plotly_code")
st.sidebar.checkbox("Show Chart", value=True, key="show_chart")
st.sidebar.checkbox("Show Summary", value=True, key="show_summary")

# Initialize default settings if not set 
for key, default in {
    "show_sql": True,
    "show_table": True,
    "show_plotly_code": True,
    "show_chart": True,
    "show_summary": True
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Reset chat 
if st.sidebar.button("Reset Chat", use_container_width=True):
    st.session_state.pop("chat_history", None)
    st.session_state.pop("my_question", None)
    st.session_state.pop("df", None)
    st.session_state.pop("user_input", None)  
    st.session_state.pop("last_user_id", None)

# Init chat history 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "show_suggestions" not in st.session_state:
    st.session_state["show_suggestions"] = False

st.title("AI assistant")

# Chat Input 
st.markdown("### Тестовые запросы:")

user_role = st.session_state.user["role"]
questions = get_role_specific_questions(user_role)

cols = st.columns(3)
for i, col in enumerate(cols):
    if i < len(questions):
        with col:
            if st.button(questions[i], key=f"test_question_{i}"):
                st.session_state["my_question"] = questions[i]
                st.session_state["df"] = None
                st.session_state["user_input"] = questions[i]

new_question = st.chat_input("Задайте вопрос о ваших данных")

if new_question:
    st.session_state["my_question"] = new_question
    st.session_state["df"] = None
    # Store user input for future checks
    st.session_state["user_input"] = new_question

# Render chat history 
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

# Processing a new question 
my_question = st.session_state.get("my_question", None)

if my_question:
    st.chat_message("user").write(my_question)

    try:
        logging.info(f"New question: {my_question}")

        recent_context = st.session_state.chat_history[-5:]
        context_parts = []
        for entry in recent_context:
            part = f"Q: {entry['question']}\nSQL: {entry['sql']}"
            if entry.get("df") is not None:
                part += f"\nDATA:\n{df_to_string(entry['df'])}"
            context_parts.append(part)

        user_info = f"Я {true_role} {st.session_state.user['original_id']}"

        if not st.session_state.chat_history:
            full_question = f"{user_info}\n\nQ: {my_question}"
        else:
            last_entry = st.session_state.chat_history[-1]
            context_text = f"Предыдущий вопрос: {last_entry['question']}\nОтвет: {last_entry['summary']}"
            full_question = f"{user_info}\n\n{context_text}\n\nНовый вопрос: {my_question}"

        logging.info(f"Generated promt: {full_question}")

        # SQL Generation
        sql = generate_sql_cached(question=full_question)
        logging.info(f"Generated SQL: {sql}")


        if not sql or not is_sql_valid_cached(sql):
            logging.error("Generated SQL is incorrect.")
            st.chat_message("assistant", avatar=avatar_url).error("Сгенерированный SQL некорректен.")
            st.stop()
        elif is_sql_injection(sql):
            logging.warning(f"Rejected SQL query due to suspected injection: {sql}")
            st.chat_message("assistant", avatar=avatar_url).error("Запрос отклонён системой безопасности из-за подозрения на SQL-инъекцию.")
            st.stop()
        # Running SQL
        else:
            logging.info(f"The generated SQL does not contain injections.")
            logging.info(f"is_sql_injection(sql): %s",is_sql_injection(sql))
            df = run_sql_cached(sql=sql)
            logging.info(f"The SQL query was executed successfully. Number of rows: {len(df)}")

        # Save DataFrame
        st.session_state["df"] = df

        # Plotly code and graph generation
        plotly_code = None
        fig = None
        if st.session_state.get("show_chart", True) and should_generate_chart_cached(question=my_question, sql=sql, df=df):
            plotly_code = generate_plotly_code_cached(question=my_question, sql=sql, df=df)
            if plotly_code:
                fig = generate_plot_cached(code=plotly_code, df=df)

        # Summary
        summary = None
        if st.session_state.get("show_summary", True):
            summary = generate_summary_cached(question=my_question + " (ответь на русском языке)", df=df)

        # Save to history
        if len(st.session_state.chat_history) > 1:
            st.session_state.chat_history = [st.session_state.chat_history[-1]]  # Save only last

        st.session_state.chat_history.append({
            "question": my_question,
            "sql": sql,
            "df": df,
            "summary": summary,
            "plotly_code": plotly_code,
            "fig": fig
        })

        # Displaying the response immediately
        assistant_msg = st.chat_message("assistant", avatar=avatar_url)

        if st.session_state.get("show_sql", True):
            assistant_msg.code(sql, language="sql")

        if st.session_state.get("show_table", True):
            if df is not None:
                if len(df) > 10:
                    assistant_msg.text("Displaying first 10 rows of data:")
                    assistant_msg.dataframe(df.head(10))
                    csv = df.to_csv(index=False)
                    st.download_button(label="Download Full Data", data=csv, file_name="full_data.csv", mime="text/csv")
                else:
                    assistant_msg.dataframe(df)

        if st.session_state.get("show_plotly_code", False) and plotly_code:
            assistant_msg.code(plotly_code, language="python")

        if st.session_state.get("show_chart", True) and fig:
            assistant_msg.plotly_chart(fig)

        if st.session_state.get("show_summary", True) and summary:
            assistant_msg.text(summary)

        st.session_state["my_question"] = None

    except Exception as e:
        error_trace = traceback.format_exc()
        logging.error(f"Request processing error: {str(e)}\n{error_trace}")
        st.chat_message("assistant", avatar=avatar_url).error("Произошла ошибка при обработке запроса.")

# Show suggested questions 
show_suggested_questions()