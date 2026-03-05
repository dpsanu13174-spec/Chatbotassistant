import io, os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError
from langchain_groq.chat_models import ChatGroq


def main():
    load_dotenv(Path(__file__).with_name('.env'))
    st.set_page_config(page_title='AI Assistant', page_icon='🤖', layout='wide')
    ss = st.session_state
    ss.setdefault('messages', []); ss.setdefault('groq_api_key_override', ''); ss.setdefault('seed_prompt', '')

    with st.sidebar:
        st.title('⚙️ Settings'); st.divider()
        model = st.selectbox('Choose Model', ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'])
        temp = st.slider('Creativity', 0.0, 1.0, 0.3, 0.1)
        theme = st.radio('Theme', ['Dark', 'Light'], horizontal=True)
        st.text_input('Groq API Key', key='groq_api_key_override', type='password')
        files = st.file_uploader('Upload file(s)', type=['pdf', 'docx', 'txt', 'csv'], accept_multiple_files=True)
        if st.button('🗑 Clear Chat', use_container_width=True): ss.messages, ss.seed_prompt = [], ''; st.rerun()
        st.subheader('Chat History')
        for m in ss.messages[-8:]: st.caption(f"{m['role']}: {m['content'][:70]}")

    st.markdown(
        """<style>.stApp{background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff!important}.stApp *{color:#fff!important}</style>"""
        if theme == 'Dark' else
        """<style>.stApp{background:linear-gradient(135deg,#f8fbff,#eef5ff,#e6f2ff);color:#0f172a!important}.stApp *{color:#0f172a!important}[data-testid="stSidebar"]{background:#eef5ff!important}.stButton>button,button[kind],button[data-testid],.stDownloadButton>button,[data-testid="stBaseButton-secondary"],[data-testid="stBaseButton-primary"],[data-testid="stFileUploaderDropzone"] button,[data-testid="stFileUploaderDropzone"],[data-testid="stChatInput"]>div,[data-baseweb="input"]>div,[data-baseweb="select"]>div,input,textarea{background:#fff!important;color:#0f172a!important;border:1px solid #cbd5e1!important}</style>""",
        unsafe_allow_html=True,
    )

    st.title('🤖 AI Assistant'); st.caption('Powered by Groq + LangChain'); st.write('Try asking:')
    c1, c2 = st.columns(2)
    if c1.button('Explain AI', use_container_width=True): ss.seed_prompt = 'Explain AI in simple terms.'
    if c2.button('Write Python code', use_container_width=True): ss.seed_prompt = 'Write a clean Python function for binary search.'

    clean = lambda x: (x or '').strip().strip("'\"")
    key, source = clean(ss.groq_api_key_override), 'sidebar'
    if not key:
        try: key, source = clean(st.secrets.get('GROQ_API_KEY', '')), 'streamlit_secrets'
        except StreamlitSecretNotFoundError: key = ''
    if not key: key, source = clean(os.getenv('GROQ_API_KEY') or os.getenv('GROQ_API_TOKEN') or os.getenv('GROQ_KEY')), 'environment'
    if not key: st.info('Add Groq key in sidebar or set GROQ_API_KEY in .env'); st.stop()
    if not key.startswith('gsk_'): st.error('Invalid key format. Groq key must start with gsk_'); st.stop()
    st.caption(f"Using {source} key: `{key[:4]}...{key[-4:] if len(key) > 8 else '****'}`")

    try: llm = ChatGroq(model=model, groq_api_key=key, temperature=temp)
    except TypeError: llm = ChatGroq(model=model, api_key=key, temperature=temp)

    txts = []
    for f in files or []:
        n, b = f.name.lower(), f.read()
        try:
            if n.endswith('.txt'): txts.append(b.decode('utf-8', errors='ignore'))
            elif n.endswith('.csv'):
                try:
                    import pandas as pd
                    txts.append(pd.read_csv(io.BytesIO(b)).head(100).to_csv(index=False))
                except Exception: txts.append(b.decode('utf-8', errors='ignore'))
            elif n.endswith('.pdf'):
                try:
                    from pypdf import PdfReader
                    txts.append('\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(b)).pages))
                except Exception: st.warning(f'Cannot parse PDF: {f.name} (install pypdf)')
            elif n.endswith('.docx'):
                try:
                    import docx2txt
                    txts.append(docx2txt.process(io.BytesIO(b)) or '')
                except Exception: st.warning(f'Cannot parse DOCX: {f.name} (install docx2txt)')
        except Exception as e: st.warning(f'File error {f.name}: {e}')
    file_context = '\n\n'.join(t for t in txts if t).strip()

    for m in ss.messages:
        with st.chat_message(m['role'], avatar='👤' if m['role'] == 'user' else '🤖'): st.write(m['content'])

    prompt = st.chat_input('Ask me anything...') or ss.seed_prompt; ss.seed_prompt = ''
    if not prompt:
        dump = '\n'.join(f"{m['role']}: {m['content']}" for m in ss.messages)
        st.download_button('Download Chat', dump or 'No chat yet', file_name='chat_history.txt', use_container_width=True)
        st.markdown('---'); st.caption('Built using LangChain, Groq, and Streamlit'); return

    ss.messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user', avatar='👤'): st.write(prompt)

    rag = ''
    if file_context:
        chunks = [file_context[i:i + 1200] for i in range(0, len(file_context), 1000)][:50]
        q = set(prompt.lower().split()); rag = '\n\n'.join(sorted(chunks, key=lambda c: sum(w in c.lower() for w in q), reverse=True)[:3])

    msgs = [{'role': 'system', 'content': 'You are concise, accurate, and helpful.'}]
    if rag: msgs.append({'role': 'system', 'content': f'Use uploaded file context if relevant:\n{rag}'})
    msgs += ss.messages

    with st.chat_message('assistant', avatar='🤖'):
        with st.spinner('🤖 Thinking...'):
            resp, box = '', st.empty()
            try:
                for ch in llm.stream(msgs): resp += getattr(ch, 'content', '') or ''; box.write(resp)
                if not resp.strip(): resp = getattr(llm.invoke(msgs), 'content', '') or 'No response.'; box.write(resp)
            except Exception as e: resp = f'Groq API error: {e}'; box.write(resp)
    ss.messages.append({'role': 'assistant', 'content': resp})

    dump = '\n'.join(f"{m['role']}: {m['content']}" for m in ss.messages)
    st.download_button('Download Chat', dump, file_name='chat_history.txt', use_container_width=True)
    st.markdown('---'); st.caption('Built using LangChain, Groq, and Streamlit')


if __name__ == '__main__':
    main()
