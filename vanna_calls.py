import streamlit as st
from vanna.openai import OpenAI_Chat            # type: ignore
from vanna.vannadb import VannaDB_VectorStore   # type: ignore

class MyVanna(VannaDB_VectorStore, OpenAI_Chat):
    def __init__(self):
        VannaDB_VectorStore.__init__(
            self,
            vanna_model="vanna_performance_set_questions",
            vanna_api_key=st.secrets.get("VANNA_API_KEY")
        )
        OpenAI_Chat.__init__(
            self,
            config={
                "api_key": st.secrets.get("OPENAI_API_KEY"),
                "model": "gpt-4o-mini"  
            }
        )

    def get_db_user(self, role: str) -> str:
        role_to_db_user = {
            "student": "user_student",
            "teacher": "user_teacher",
            "administrator": "user_admin"
        }
        return role_to_db_user.get(role.lower(), "user_student")
    
@st.cache_resource(ttl=3600)
def setup_vanna():
    if "user" not in st.session_state:
        st.error("Требуется авторизация")
        st.stop()
    
    vn = MyVanna()
    
    try:
        db_user_key = vn.get_db_user(st.session_state.user["role"])
        
        vn.connect_to_postgres(
            host=st.secrets.postgres["host"],  
            dbname=st.secrets.postgres["dbname"],
            user=st.secrets.postgres[db_user_key],
            password=st.secrets.postgres["password"],
            port=st.secrets.postgres["port"],
            sslmode="require",
            connect_timeout=5
        )
        return vn
    except KeyError:
        st.error("Неверная роль пользователя")
        st.stop()
    except Exception as e:
        st.error(f"Ошибка подключения к БД: {str(e)}")
        st.stop()

@st.cache_data(show_spinner="Generating sample questions ...")
def generate_questions_cached():
    vn = setup_vanna()
    raw_questions = vn.generate_questions()

    if isinstance(raw_questions, list):
        return [q for q in raw_questions if isinstance(q, str)]
    return []

@st.cache_data(show_spinner="Generating SQL query ...")
def generate_sql_cached(question: str):
    vn = setup_vanna()
    return vn.generate_sql(question=question, allow_llm_to_see_data=True)

@st.cache_data(show_spinner="Checking for valid SQL ...")
def is_sql_valid_cached(sql: str):
    vn = setup_vanna()
    return vn.is_sql_valid(sql=sql)

@st.cache_data(show_spinner="Running SQL query ...")
def run_sql_cached(sql: str):
    vn = setup_vanna()
    return vn.run_sql(sql=sql)

@st.cache_data(show_spinner="Checking if we should generate a chart ...")
def should_generate_chart_cached(question, sql, df):
    vn = setup_vanna()
    return vn.should_generate_chart(df=df)

@st.cache_data(show_spinner="Generating Plotly code ...")
def generate_plotly_code_cached(question, sql, df):
    vn = setup_vanna()
    code = vn.generate_plotly_code(question=question, sql=sql, df=df)
    return code

@st.cache_data(show_spinner="Running Plotly code ...")
def generate_plot_cached(code, df):
    vn = setup_vanna()
    return vn.get_plotly_figure(plotly_code=code, df=df)\

@st.cache_data(show_spinner="Generating followup questions ...")
def generate_followup_cached(question, sql, df):
    vn = setup_vanna()
    return vn.generate_followup_questions(question=question, sql=sql, df=df)

@st.cache_data(show_spinner="Generating summary ...")
def generate_summary_cached(question, df):
    vn = setup_vanna()
    return vn.generate_summary(question=question, df=df)