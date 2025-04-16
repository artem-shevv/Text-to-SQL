import streamlit as st
from vanna.openai import OpenAI_Chat # type: ignore
from vanna.vannadb import VannaDB_VectorStore # type: ignore

class MyVanna(VannaDB_VectorStore, OpenAI_Chat):
    def __init__(self):
        # Инициализация с использованием st.secrets
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

    def get_top_training_matches(self, question, top_k=1):
        # Используем метод get_similar_question_sql для получения похожих запросов
        similar_questions = self.get_similar_question_sql(question, top_k=top_k)
        return similar_questions
    
@st.cache_resource(ttl=3600)
def setup_vanna():
    vn = MyVanna()
    # Подключение к PostgreSQL через секреты
    vn.connect_to_postgres(
        host=st.secrets.postgres["host"],  
        dbname=st.secrets.postgres["dbname"],
        user=st.secrets.postgres["user"],
        password=st.secrets.postgres["password"],
        port=st.secrets.postgres["port"],
        sslmode="require",  # Обязательно для Supabase
        connect_timeout=5  
    )
    return vn

@st.cache_data(show_spinner="Generating sample questions ...")
def generate_questions_cached():
    vn = setup_vanna()
    return vn.generate_questions()


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
    return vn.get_plotly_figure(plotly_code=code, df=df)


@st.cache_data(show_spinner="Generating followup questions ...")
def generate_followup_cached(question, sql, df):
    vn = setup_vanna()
    return vn.generate_followup_questions(question=question, sql=sql, df=df)

@st.cache_data(show_spinner="Generating summary ...")
def generate_summary_cached(question, df):
    vn = setup_vanna()
    return vn.generate_summary(question=question, df=df)