import streamlit as st
import logging
from openai import OpenAI   # type: ignore

class LLMInjectionChecker:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def check_injection(self, sql: str) -> bool:
        prompt = f"""
        Your task is to identify whether a given SQL query contains any kind of SQL injection. 
        Only return "True" if the query shows signs of malicious intent, such as attempts to access unauthorized data, 
        drop or alter tables, bypass logical restrictions, union-based injections, or other typical SQL injection patterns. 
        Return "False" only if the query appears safe and contains no signs of injection or abuse.

        Respond with only True or False.

        SQL QUERY:
        {sql}
        """
        try:
            logging.info(f"sql for checking: %s", sql)
            logging.info("A request has been sent to the LLM to verify the injection.")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security assistant that checks for SQL injection."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            reply = response.choices[0].message.content.strip().lower()
            logging.info(f"Answer LLM: {reply}")
            return reply == "true"

        except Exception as e:
            logging.error(f"Injection check failed: {e}")
            return True

    def add_ddl(self, *args, **kwargs):
        pass

    def add_documentation(self, *args, **kwargs):
        pass

    def add_question_sql(self, *args, **kwargs):
        pass

    def generate_embedding(self, *args, **kwargs):
        pass

    def get_related_ddl(self, *args, **kwargs):
        pass

    def get_related_documentation(self, *args, **kwargs):
        pass

    def get_similar_question_sql(self, *args, **kwargs):
        pass

    def get_training_data(self, *args, **kwargs):
        pass

    def remove_training_data(self, *args, **kwargs):
        pass
            
@st.cache_data(show_spinner="Checking for SQL injection ...")
def is_sql_injection(sql: str) -> bool:
    checker = LLMInjectionChecker()
    return checker.check_injection(sql)