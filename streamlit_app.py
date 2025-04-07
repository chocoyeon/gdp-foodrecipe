import streamlit as st
from openai import OpenAI
import os
import json

# 세션 상태 초기화 - 이 부분 추가
if 'messages' not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="오늘의 식탁", page_icon="🥕", layout="wide")

st.markdown("<h1 style='text-align: center;'>🥕 오늘의 식탁 🍽️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>매일매일, 무엇을 먹을지 고민될 때!<br>당신의 재료나 요리 이름을 입력하면 알맞은 레시피를 추천해드려요 🍳</p>", unsafe_allow_html=True)

openai_api_key = st.secrets['openai']['API_KEY']
client = OpenAI(api_key=openai_api_key)

with st.sidebar:
    st.markdown("### 사용 방법")
    st.markdown("1. 검색 유형을 선택하고, 요리 이름이나 재료를 입력하세요.")
    st.markdown("2. 에피타이저, 메인요리 등으로 추천 요리가 분류됩니다.")
    st.markdown("3. '레시피 보기' 버튼을 누르면 AI가 요리법을 알려줍니다.")
    st.markdown("---")
    st.markdown("### 팁")
    st.markdown("- 예: 김치찌개, 애호박, 돼지고기, 콩나물, 감자")

# CSS로 검색창 레이아웃 개선
st.markdown("""
<style>
    .search-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
    }
    .search-label {
        margin-right: 10px;
        font-size: 0.9rem;
        white-space: nowrap;
    }
    .search-item {
        margin: 0 5px;
        display: flex;
        align-items: center;
    }
    .stButton button {
        height: 38px;
        padding-top: 0;
        padding-bottom: 0;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# 검색 컨테이너 시작
st.markdown('<div class="search-container">', unsafe_allow_html=True)

# 검색 유형 라벨과 드롭다운
st.markdown('<div class="search-item search-label">검색 유형</div>', unsafe_allow_html=True)
search_col = st.columns([1, 5, 1])
with search_col[0]:
    search_type = st.selectbox("", ["요리", "재료"], label_visibility="collapsed")

# 검색 입력란
with search_col[1]:
    query = st.text_input("", placeholder="검색어 입력 (예: 갈비찜, 애호박, 콩나물)", label_visibility="collapsed")

# 검색 버튼
with search_col[2]:
    search_clicked = st.button("검색")

# 검색 컨테이너 종료
st.markdown('</div>', unsafe_allow_html=True)

# 레시피 가져오는 함수 - 별도로 분리하여 재사용 가능하게 함
def get_recipe_for_dish(dish_name):
    try:
        messages = [
            {"role": "system", "content": "당신은 요리 전문가입니다. 사용자가 입력한 요리에 대한 레시피를 재료와 만드는 순서로 자세히 설명해주세요. 간단하고 따뜻한 말투로 작성해주세요."},
            {"role": "user", "content": f"{dish_name} 레시피 알려줘"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"레시피를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return "레시피를 불러오는데 실패했습니다. 다시 시도해주세요."

# OpenAI를 사용하여 요리 추천 받기
def get_recipes_from_openai(ingredient):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """당신은 요리 전문 AI 비서입니다. 주어진 재료로 만들 수 있는 요리 목록을 JSON 형식으로 제공해주세요.
                다음 카테고리별로 요리를 분류해주세요:
                - 에피타이저: 가볍게 먹는 전채요리
                - 메인요리: 주요리, 한 끼 식사로 충분한 요리
                - 밑반찬: 밥과 함께 먹는 반찬류
                - 국/찌개: 국물 요리
                - 디저트: 후식, 간식류
                
                각 카테고리별로 3-4개의 요리를 추천해주세요. 재료가 포함된 한국 요리를 중심으로 추천해주세요.
                응답은 다음과 같은 JSON 형식이어야 합니다:
                {
                    "에피타이저": ["요리1", "요리2",...],
                    "메인요리": ["요리1", "요리2",...],
                    "밑반찬": ["요리1", "요리2",...],
                    "국/찌개": ["요리1", "요리2",...],
                    "디저트": ["요리1", "요리2",...]
                }
                """},
                {"role": "user", "content": f"다음 재료로 만들 수 있는 요리 추천해줘: {ingredient}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # 응답에서 JSON 파싱
        recipes_data = json.loads(response.choices[0].message.content)
        return recipes_data
        
    except Exception as e:
        st.error(f"레시피를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return {}

if query and (search_clicked or 'Enter' in query):
    # 요리 검색인 경우
    if search_type == "요리":
        with st.spinner("검색 중..."):
            recipes_data = {
                "에피타이저": [],
                "메인요리": [query],
                "밑반찬": [],
                "국/찌개": [],
                "디저트": []
            }
    
    # 재료 검색인 경우 OpenAI로 요리 추천 받기
    else:
        with st.spinner("AI가 추천 요리를 찾고 있어요..."):
            recipes_data = get_recipes_from_openai(query)
    
    # 결과가 있는 카테고리만 표시
    filtered_categories = {k: v for k, v in recipes_data.items() if v}
    
    if filtered_categories:
        num_categories = len(filtered_categories)
        category_cols = st.columns(min(5, num_categories))  # 최대 5개 열까지만 사용
        
        for i, (category, dishes) in enumerate(filtered_categories.items()):
            col_index = i % len(category_cols)
            with category_cols[col_index]:
                st.markdown(f"<h4 style='text-align: center;'>{category}</h4>", unsafe_allow_html=True)
                for dish in dishes:
                    # 각 요리에 대한 버튼 생성
                    button_key = f"{category}_{dish}_{i}"  # 고유한 키 생성
                    if st.button(f"{dish} 🍽️", key=button_key):
                        with st.spinner("AI 요리사가 레시피를 준비하고 있어요..."):
                            # 별도 함수 호출로 레시피 가져오기
                            recipe = get_recipe_for_dish(dish)

                        st.markdown(f"<h4 style='text-align: center;'>📋 {dish} 레시피</h4>", unsafe_allow_html=True)
                        st.markdown(f"<div style='text-align: justify;'>{recipe}</div>", unsafe_allow_html=True)
    else:
        st.warning("입력한 내용과 일치하는 요리를 찾을 수 없어요. 다시 시도해보세요! 🍲")
