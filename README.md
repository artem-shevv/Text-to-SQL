# Hello, this repositority will be used for my graduate work, and I will be glad if it can be useful to you.

# Install

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

# Configure
Modify the `setup_vanna` function in [vanna_calls.py](./vanna_calls.py) to use your desired Vanna setup.

You can configure secrets in `.streamlit/secrets.toml` and access them in your app using `st.secrets.get(...)`.

# Run

```bash
streamlit run app.py
```



