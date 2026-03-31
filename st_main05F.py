import os
import re
import html
import streamlit as st
from dotenv import load_dotenv

from services.kakao_book_service import search_books
from services.openai_service import (
    get_openai_client,
    extract_book_keyword,
    recommend_books,
)


load_dotenv()

kakao_api_key = os.getenv("KAKAO_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = get_openai_client(openai_api_key)

SEARCH_TARGET_MAP = {
    "제목": "title",
    "저자": "person",
    "출판사": "publisher",
}

SORT_OPTION_MAP = {
    "정확도순": "accuracy",
    "최신순": "latest",
}


def clean_text(value):
    if not value:
        return ""
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def format_price(value):
    if not value:
        return "가격 정보 없음"
    return f"{value:,}원"


def build_book_context(book_documents):
    context = ""

    for i, book in enumerate(book_documents, 1):
        title = clean_text(book.get("title", ""))
        authors = ", ".join(book.get("authors", []))
        publisher = clean_text(book.get("publisher", ""))
        contents = clean_text(book.get("contents", ""))
        sale_price = book.get("sale_price", 0)
        status = clean_text(book.get("status", ""))
        url = book.get("url", "")

        context += (
            f"{i}) 제목: {title}\n"
            f"   저자: {authors}\n"
            f"   출판사: {publisher}\n"
            f"   소개: {contents}\n"
            f"   판매가: {format_price(sale_price)}\n"
            f"   판매 상태: {status}\n"
            f"   링크: {url}\n\n"
        )

    return context


def render_book_card(book):
    title = html.escape(clean_text(book.get("title", "")))
    authors = html.escape(", ".join(book.get("authors", [])))
    publisher = html.escape(clean_text(book.get("publisher", "")))
    contents = html.escape(clean_text(book.get("contents", ""))[:180] or "소개 정보 없음")
    sale_price = html.escape(format_price(book.get("sale_price", 0)))
    status = html.escape(clean_text(book.get("status", "")) or "상태 정보 없음")
    url = book.get("url", "")
    thumbnail = book.get("thumbnail", "")

    thumb_html = ""
    if thumbnail:
        thumb_html = f'<img src="{thumbnail}" class="book-thumb" alt="{title}">'

    st.markdown(
        f"""
        <div class="book-card">
            {thumb_html}
            <div class="book-body">
                <div class="book-title">{title}</div>
                <div class="book-meta">저자: {authors or "정보 없음"}</div>
                <div class="book-meta">출판사: {publisher or "정보 없음"}</div>
                <div class="book-desc">{contents}</div>
                <div class="book-footer">
                    <span class="book-chip">{sale_price}</span>
                    <span class="book-chip">{status}</span>
                </div>
                <div class="book-link"><a href="{url}" target="_blank">상세 페이지 보기</a></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --primary: #2f6f62;
            --on-primary: #ffffff;
            --primary-container: #b8f2e2;
            --on-primary-container: #0f2c26;
            --secondary-container: #d9e7e2;
            --surface: #f6fbf8;
            --surface-container: #ffffff;
            --surface-container-high: #eef7f3;
            --outline-variant: #d6e2dc;
            --on-surface: #1b1f1d;
            --on-surface-variant: #5d6763;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, #e8f6f0 0%, transparent 28%),
                linear-gradient(180deg, #f7fbf9 0%, #f1f7f4 100%);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            background: linear-gradient(135deg, #eef8f4 0%, #ffffff 100%);
            border: 1px solid var(--outline-variant);
            border-radius: 28px;
            padding: 28px 28px 22px 28px;
            margin-bottom: 1.2rem;
            box-shadow: 0 8px 24px rgba(30, 60, 50, 0.06);
        }

        .hero-kicker {
            color: var(--primary);
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .hero-title {
            color: var(--on-surface);
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 0.5rem;
        }

        .hero-desc {
            color: var(--on-surface-variant);
            font-size: 1rem;
            line-height: 1.6;
        }

        .hero-tags {
            margin-top: 1rem;
        }

        .hero-tag {
            display: inline-block;
            background: var(--secondary-container);
            color: #29433b;
            border-radius: 999px;
            padding: 0.4rem 0.8rem;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
        }

        .section-card {
            background: rgba(255,255,255,0.78);
            border: 1px solid var(--outline-variant);
            border-radius: 24px;
            padding: 20px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 18px rgba(30, 60, 50, 0.04);
        }

        .result-panel {
            background: linear-gradient(180deg, #ffffff 0%, #f4faf7 100%);
            border: 1px solid var(--outline-variant);
            border-radius: 24px;
            padding: 22px;
        }

        .book-card {
            background: var(--surface-container);
            border: 1px solid var(--outline-variant);
            border-radius: 22px;
            overflow: hidden;
            margin-bottom: 1rem;
            box-shadow: 0 6px 18px rgba(30, 60, 50, 0.04);
        }

        .book-thumb {
            width: 100%;
            max-height: 280px;
            object-fit: cover;
            display: block;
            background: #eef4f1;
        }

        .book-body {
            padding: 16px;
        }

        .book-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--on-surface);
            margin-bottom: 0.5rem;
            line-height: 1.4;
        }

        .book-meta {
            font-size: 0.92rem;
            color: var(--on-surface-variant);
            margin-bottom: 0.25rem;
        }

        .book-desc {
            font-size: 0.95rem;
            color: var(--on-surface);
            margin-top: 0.8rem;
            line-height: 1.55;
            min-height: 4.6rem;
        }

        .book-footer {
            margin-top: 1rem;
        }

        .book-chip {
            display: inline-block;
            background: var(--surface-container-high);
            color: #24453c;
            border: 1px solid var(--outline-variant);
            border-radius: 999px;
            padding: 0.32rem 0.7rem;
            font-size: 0.82rem;
            font-weight: 700;
            margin-right: 0.4rem;
            margin-bottom: 0.3rem;
        }

        .book-link {
            margin-top: 0.8rem;
        }

        .book-link a {
            color: var(--primary);
            text-decoration: none;
            font-weight: 700;
        }

        .book-link a:hover {
            text-decoration: underline;
        }

        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.75);
            border: 1px solid var(--outline-variant);
            border-radius: 20px;
            padding: 0.8rem 1rem;
        }

        div[data-testid="stMetric"] label {
            color: var(--on-surface-variant);
        }

        div[data-baseweb="tab-list"] {
            gap: 0.4rem;
        }

        button[data-baseweb="tab"] {
            border-radius: 999px;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .small-note {
            color: var(--on-surface-variant);
            font-size: 0.92rem;
            line-height: 1.55;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="도서 추천 검색",
    page_icon="📚",
    layout="wide",
)

apply_theme()

if "result" not in st.session_state:
    st.session_state.result = None

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">카카오 검색 기반</div>
        <div class="hero-title">도서 추천 검색</div>
        <div class="hero-desc">
            카카오 도서 검색으로 후보 책을 찾고, GPT가 그 목록 안에서만 추천해주는 도서 추천 앱입니다.
        </div>
        <div class="hero-tags">
            <span class="hero-tag">질문 기반 추천</span>
            <span class="hero-tag">카카오 도서 검색</span>
            <span class="hero-tag">GPT 추천</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("검색 설정")
    size = st.slider("검색 개수", min_value=5, max_value=20, value=10, step=5)

    selected_target_label = st.selectbox(
        "검색 기준",
        options=list(SEARCH_TARGET_MAP.keys()),
        index=0,
    )
    target = SEARCH_TARGET_MAP[selected_target_label]

    selected_sort_label = st.selectbox(
        "정렬 방식",
        options=list(SORT_OPTION_MAP.keys()),
        index=0,
    )
    sort = SORT_OPTION_MAP[selected_sort_label]

    show_context = st.toggle("GPT 입력용 도서 목록 보기", value=False)

st.markdown('<div class="section-card">', unsafe_allow_html=True)

question = st.text_area(
    "어떤 책을 찾고 있나요?",
    placeholder="예: 위로가 되고 쉽게 읽히는 심리학 책 추천해줘",
    height=120,
)

col1, col2 = st.columns([1, 1])
submit = col1.button("추천 받기", use_container_width=True, type="primary")
example = col2.button("예시 질문 보기", use_container_width=True)

if example:
    st.info("예시 질문: 위로가 되는 심리학 책 추천해줘 / 입문자가 읽기 쉬운 경제 책 알려줘 / 가볍게 읽을 수 있는 에세이 추천해줘")

st.markdown(
    """
    <div class="small-note">
        예시 질문: 위로가 되는 심리학 책 추천해줘 / 입문자가 읽기 쉬운 경제 책 알려줘 / 가볍게 읽을 수 있는 에세이 추천해줘
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)

if submit:
    if not question.strip():
        st.warning("질문을 입력해 주세요.")
    elif not kakao_api_key or not openai_api_key:
        st.error("API 키를 먼저 확인해 주세요. .env에 KAKAO_API_KEY와 OPENAI_API_KEY가 필요합니다.")
    else:
        try:
            with st.status("추천 과정을 진행하고 있습니다.", expanded=True) as status:
                st.write("1. 질문에서 검색 키워드를 추출하고 있습니다.")
                keyword = extract_book_keyword(client, question)
                st.write(f"추출된 검색 키워드: `{keyword}`")

                st.write("2. 카카오 도서 검색 API로 후보 도서를 찾고 있습니다.")
                book_data = search_books(
                    keyword,
                    kakao_api_key,
                    size=size,
                    target=target,
                    sort=sort,
                )
                book_documents = book_data.get("documents", [])
                meta = book_data.get("meta", {})

                if not book_documents:
                    status.update(label="검색 결과가 없습니다.", state="error")
                    st.session_state.result = {
                        "question": question,
                        "keyword": keyword,
                        "books": [],
                        "meta": meta,
                        "context": "",
                        "recommendation": "",
                    }
                else:
                    st.write(f"후보 도서 {len(book_documents)}권을 찾았습니다.")
                    st.write("3. 후보 도서 목록을 바탕으로 추천 결과를 생성하고 있습니다.")
                    context = build_book_context(book_documents)
                    recommendation = recommend_books(client, question, context)

                    st.session_state.result = {
                        "question": question,
                        "keyword": keyword,
                        "books": book_documents,
                        "meta": meta,
                        "context": context,
                        "recommendation": recommendation,
                    }
                    status.update(label="추천이 완료되었습니다.", state="complete")

        except Exception as e:
            st.session_state.result = None
            st.error(f"오류가 발생했습니다: {e}")

result = st.session_state.result

if result:
    books = result["books"]
    meta = result["meta"]

    c1, c2, c3 = st.columns(3)
    c1.metric("검색 키워드", result["keyword"])
    c2.metric("후보 도서 수", len(books))
    c3.metric("전체 검색 수", meta.get("total_count", 0))

    if not books:
        st.info("검색 결과가 없습니다. 질문을 더 넓게 바꾸거나 다른 키워드로 다시 시도해보세요.")
    else:
        tab1, tab2, tab3 = st.tabs(["추천 결과", "검색된 도서", "검색 정보"])

        with tab1:
            st.markdown('<div class="result-panel">', unsafe_allow_html=True)
            st.subheader("추천 결과")
            st.write(result["recommendation"])
            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.subheader("검색된 도서 목록")
            for i in range(0, len(books), 2):
                cols = st.columns(2)
                batch = books[i:i + 2]
                for col, book in zip(cols, batch):
                    with col:
                        render_book_card(book)

        with tab3:
            st.subheader("검색 정보")
            st.write(f"사용자 질문: {result['question']}")
            st.write(f"추출된 검색 키워드: {result['keyword']}")
            st.write(f"검색 기준: {selected_target_label}")
            st.write(f"정렬 방식: {selected_sort_label}")
            st.write(f"검색 개수: {size}")
            st.json(meta)

            if show_context:
                st.subheader("GPT 입력용 도서 목록")
                st.code(result["context"])
