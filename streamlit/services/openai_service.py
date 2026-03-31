from openai import OpenAI


def get_openai_client(api_key):
    return OpenAI(api_key=api_key)


def extract_book_keyword(client, question, model="gpt-4o-mini"):
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "사용자 질문에서 도서 검색에 사용할 핵심 주제어 1개만 추출해줘. "
                    "검색 결과가 너무 좁아지지 않도록 짧고 일반적인 명사 형태로만 답해. "
                    "형용사, 설명, 문장 없이 키워드만 출력해."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0,
        max_output_tokens=20,
        top_p=1
    )

    return response.output_text.strip()


def recommend_books(client, question, context, model="gpt-4o-mini"):
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "너는 도서 추천 도우미야. "
                    "반드시 제공된 도서 목록 안에서만 추천해야 해. "
                    "목록에 없는 책은 추천하지 마. "
                    "사용자 질문에 가장 잘 맞는 책 3권을 골라서 추천하고, "
                    "각 책마다 추천 이유를 2문장 이내로 설명해줘."
                )
            },
            {
                "role": "user",
                "content": (
                    f"사용자 질문: {question}\n\n"
                    f"도서 목록:\n{context}"
                )
            }
        ],
        temperature=0.3,
        max_output_tokens=800,
        top_p=1
    )

    return response.output_text
