import streamlit as st
import tempfile


st.set_page_config(
    page_title="MarketMate",
    page_icon="🛍️",
    layout="centered",
)


@st.cache_resource
def load_agent():
    from shopping_agent import agent

    return agent


def message_text(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    return "".join(
        part.get("text", "")
        for part in content
        if isinstance(part, dict) and part.get("type") == "text"
    )


st.markdown(
    """
    <style>
        .stApp {
            background: #101817;
            color: #e7f0ed;
        }
        .block-container {
            max-width: 860px;
            padding-top: 2.5rem;
        }
        .brand {
            color: #7dd6be;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }
        h1 {
            color: #f2f8f5;
            letter-spacing: -0.04em;
            margin-bottom: 0.25rem;
        }
        .subtitle {
            color: #91a9a3;
            margin-bottom: 2rem;
        }
        [data-testid="stChatMessage"] {
            background: #172321;
            border: 1px solid #263b36;
            border-radius: 12px;
            margin-bottom: 0.7rem;
            padding: 0.75rem 1rem;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
            color: #e7f0ed;
            line-height: 1.65;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
            margin: 0.25rem 0 0.75rem;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p:last-child {
            margin-bottom: 0;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3 {
            color: #9be2cc;
            margin: 0.45rem 0;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ul,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ol {
            margin: 0.4rem 0 0.8rem;
            padding-left: 1.35rem;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
            margin: 0.35rem 0;
            padding-left: 0.2rem;
        }
        [data-testid="stChatMessage"] code {
            background: #0d1514;
            color: #a7e8d4;
        }
        [data-testid="stSidebar"] {
            background: #0c1211;
            border-right: 1px solid #263b36;
        }
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] p {
            color: #dceae6;
        }
        [data-testid="stChatInput"] {
            border-color: #40665d;
        }
        [data-testid="stChatInput"] textarea {
            color: #f2f8f5;
        }
    </style>
    <div class="brand">MarketMate</div>
    <h1>Find something good.</h1>
    <div class="subtitle">Tell me what you are looking for, and I will help you choose.</div>
    """,
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Shopping assistant")
    st.caption("Search products, compare ratings, and place an order when you are ready.")
    uploaded_image = st.file_uploader(
        "Find products from an image",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload a product photo or label to find similar items in the store.",
    )
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded product", use_container_width=True)
        find_from_image = st.button("Search this image", use_container_width=True)
    else:
        find_from_image = False
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=False)

prompt = st.chat_input("What would you like to shop for?")
image_prompt = None
if find_from_image and uploaded_image:
    with tempfile.NamedTemporaryFile(
        suffix="." + uploaded_image.name.rsplit(".", 1)[-1],
        delete=False,
    ) as image_file:
        image_file.write(uploaded_image.getvalue())
        image_prompt = f"I uploaded a product image at {image_file.name}. Find matching products."

request = prompt or image_prompt
if request:
    st.session_state.messages.append({"role": "user", "content": request})
    with st.chat_message("user"):
        if image_prompt:
            st.image(uploaded_image, width=220)
            st.markdown("Find products matching this image.", unsafe_allow_html=False)
        else:
            st.markdown(prompt, unsafe_allow_html=False)

    with st.chat_message("assistant"):
        with st.spinner("Looking through the store..."):
            try:
                result = load_agent().invoke({"messages": st.session_state.messages})
                reply = message_text(result["messages"][-1])
            except Exception as error:
                reply = f"I couldn't complete that request. {error}"
            st.markdown(reply, unsafe_allow_html=False)
            st.session_state.messages.append({"role": "assistant", "content": reply})