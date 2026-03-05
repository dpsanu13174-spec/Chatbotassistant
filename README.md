## Chatbot Assistant

A simple conversational chatbot built with **Streamlit**, **LangChain**, and **Groq**.
It keeps per-session chat history and answers follow-up questions with context.

### Prerequisites

- Python 3.11.9 (recommended)
- A Groq API key

### Setup

From the project root (`/Users/nehatomar/Documents/LANGCHAIN`), create and activate a virtual environment (optional), then install dependencies:

```bash
pip install -r requirements.txt
```

Set your Groq API key in the environment (or in a `.env` file in the project root):

```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

### Run the app

Change into the `Chatbotassistant` directory and start Streamlit:

```bash
cd Chatbotassistant
streamlit run app.py
```

Then open the URL shown in your terminal (typically `http://localhost:8501`) in a browser.
