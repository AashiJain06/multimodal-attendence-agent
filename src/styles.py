import streamlit as st


def apply_styles():
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
      .stApp { background: linear-gradient(180deg, #f7f9fc 0%, #f3f6fb 100%); }
      [data-testid="stSidebar"] { background: #101d35; }
      [data-testid="stSidebar"] * { color: #edf3ff !important; }
      h1 { color: #132544; letter-spacing: -0.035em; }
      h2, h3 { color: #20385e; }
      div[data-testid="stMetric"] { background: white; border: 1px solid #e3eaf4; padding: 16px; border-radius: 16px; box-shadow: 0 5px 20px rgba(23,48,84,.04); }
      div[data-testid="stTabs"] button { font-weight: 600; }
      .stButton button, .stDownloadButton button { border-radius: 10px; font-weight: 600; }
      div[data-testid="stAlert"] { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)
