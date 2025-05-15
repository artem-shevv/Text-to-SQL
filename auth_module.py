import streamlit as st
import psycopg2
import bcrypt
import logging
from logging.handlers import RotatingFileHandler

auth_logger = logging.getLogger('auth_module')
auth_logger.setLevel(logging.INFO)
auth_logger.propagate = False

auth_handler = RotatingFileHandler(
    'auth.log',
    maxBytes=1024*1024,  # 1 MB
    backupCount=3,
    encoding='utf-8'
)
auth_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
auth_logger.addHandler(auth_handler)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets.postgres["host"],
            dbname=st.secrets.postgres["dbname"],
            user=st.secrets.postgres["user"],
            password=st.secrets.postgres["password"],
            port=st.secrets.postgres["port"],
            sslmode="require"
        )
        auth_logger.info("Установлено подключение к БД")
        return conn
    except Exception as e:
        auth_logger.error(f"Ошибка подключения к БД: {str(e)}", exc_info=True)
        st.error("Ошибка подключения к базе данных")
        return None

def authenticate_user(login: str, password: str) -> dict:
    auth_conn = None
    try:
        auth_logger.info(f"Начата аутентификация для пользователя: {login}")
        
        auth_conn = psycopg2.connect(
            host=st.secrets.postgres["host"],
            dbname=st.secrets.postgres["dbname"],
            user=st.secrets.postgres["user"], 
            password=st.secrets.postgres["password"],
            port=st.secrets.postgres["port"],
            sslmode="require"
        )
        
        with auth_conn.cursor() as cursor:
            # Get the password hash, salt, and role
            cursor.execute(
                """SELECT password_hash, role, original_id 
                   FROM USERS WHERE login = %s""",
                (login,)
            )
            user_data = cursor.fetchone()
            
            if not user_data:
                auth_logger.warning(f"Пользователь не найден: {login}")
                st.error("Неверные учетные данные")
                return None
                
            stored_hash = user_data[0].encode('utf-8')
            if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                auth_logger.warning(f"Неверный пароль для пользователя: {login}")
                st.error("Неверные учетные данные")
                return None
            
            role = user_data[1]
            auth_logger.info(f"Успешная аутентификация: {login} с ролью {role}")
            
            return {
                "login": login,
                "role": role,  # (student/teacher/administrator)
                "original_id": user_data[2] if user_data[2] else None
            }
            
    except Exception as e:
        auth_logger.error(f"Ошибка аутентификации: {str(e)}", exc_info=True)
        st.error("Ошибка при аутентификации")
        return None
    finally:
        if auth_conn:
            auth_conn.close()

def show_login_form():
    st.markdown("""
    <style>
        .st-emotion-cache-1elqkl5 {
            display: none !important;
        }
        .quick-login-btn {
            margin-top: 1rem;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Авторизация")
    
    login = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")
    
    if st.button("Войти"):
        if not login or not password:
            st.error("Заполните все поля")
        else:
            with st.spinner("Проверка данных..."):
                user = authenticate_user(login, password)
                if user:
                    st.session_state["user"] = user
                    st.session_state["authenticated"] = True
                else:
                    st.error("Ошибка входа")

    st.markdown("---")
    st.markdown("### Быстрый вход:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Студенческий вход", key="quick_student", 
                    help="Вход для студента", 
                    on_click=lambda: quick_login(st.secrets.quick_login["login_st"], st.secrets.quick_login["pass_st"]),
                    use_container_width=True):
            pass
            
    with col2:
        if st.button("Преподавательский вход", key="quick_teacher", 
                    help="Вход для преподавателя",
                    on_click=lambda: quick_login(st.secrets.quick_login["login_te"], st.secrets.quick_login["pass_te"]),
                    use_container_width=True):
            pass
            
    with col3:
        if st.button("Административный вход", key="quick_admin", 
                    help="Вход для администратора",
                    on_click=lambda: quick_login(st.secrets.quick_login["login_ad"], st.secrets.quick_login["pass_ad"]),
                    use_container_width=True):
            pass

def quick_login(login: str, password: str):
    with st.spinner(f"Выполняется вход как {login}..."):
        user = authenticate_user(login, password)
        if user:
            st.session_state["user"] = user
            st.session_state["authenticated"] = True
        else:
            st.error("Ошибка быстрого входа")