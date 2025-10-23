"""
TrendSelectAgent
빈도 기반으로 필터링 하고 LLM기반으로 중요도 순으로 정렬한다.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.state_schema import SystemState


import re
from collections import Counter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()



llm = ChatOpenAI(model="gpt-4o-mini")

def clean_text(text):
    """불필요한 기호 제거"""
    text = re.sub(r"[^A-Za-z0-9가-힣\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_trend_candidates(docs):
    """기사 요약들에서 트랜드 키워드 후보 추출"""
    combined_text = "\n".join([clean_text(d["content"]) for d in docs])
    prompt = ChatPromptTemplate.from_template("""
    다음은 여러 AI 기술 트렌드 기사 요약문이다.
    이 내용을 기반으로 향후 5년 급성장하거나 새롭게 등장할 가능성이 높은 AI 관련 기술 트렌드 후보를 추출하라.
    - 구체적인 기술명만 포함 (예: Neuromorphic AI, Synthetic Data, Federated Learning, Multimodal AI, Self-learning AI 등)
    - 이미 상용화된 기술 제외
    - 응용 기술도 포함
    - 사회적 개념(예: Ethics, Inclusivity, Regulation)은 제외
    - 기업명, 산업명 제외
    - 유사어는 하나로 통합
    - 형식: JSON {{"candidates": ["", "", ...]}}

    ==== 기사 요약 ====
    {content}
    """)

    chain = prompt | llm
    response = chain.invoke({"content": combined_text})

    import json, re
    raw_text = response.content.strip()

    # ✅ JSON 코드블록 처리
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)  # ```json 혹은 ``` 제거
        raw_text = raw_text.replace("```", "").strip()

    try:
        result = json.loads(raw_text)
        candidates = result.get("candidates", [])
    except Exception as e:
        print("\n⚠️ JSON 파싱 실패:", e)
        print("LLM 응답 원문:\n", raw_text)
        # fallback - 일반 텍스트 패턴에서 후보 추출
        matches = re.findall(r'\b[A-Z][A-Za-z0-9\s\-]+AI\b', raw_text)
        candidates = list(set(matches))
        print(f"⚙️ 일반 텍스트 기반 후보 추출: {candidates}")


    return candidates



def rank_by_future_relevance(candidates):
    """LLM 기반 미래 중심 중요도 평가"""
    prompt = ChatPromptTemplate.from_template("""
    다음은 AI 관련 트렌드 목록이다:
    {trend_list}

    각 트렌드를 '미래 3~5년 내 기업 전략 관점'에서 평가하라.
    아래 기준으로 0~1 사이 점수를 부여하고, 총합이 높은 순으로 정렬하라.

    평가 기준:
    1. Emergence (최근 2년 내 급부상 정도)
    2. Growth Potential (향후 5년 성장 가능성)
    3. Industry Applicability (산업 적용성)
    출력은 JSON 형식으로:
    {{
      "ranked_trends": [
        {{"name": "", "scores": {{"emergence":0.0, "growth":0.0, "applicability":0.0}}, "total": 0.0, "reason": ""}},
        ...
      ]
    }}
    """)

    chain = prompt | llm
    response = chain.invoke({"trend_list": "\n".join(candidates)})

    import json, re
    raw = response.content.strip()


    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = raw.replace("```", "").strip()

    try:
        result = json.loads(raw)
        ranked_data = result.get("ranked_trends", [])
        if not ranked_data:  # ⚠️ 빈 리스트인 경우 대비
            print("⚠️ LLM이 빈 ranked_trends를 반환했습니다.")
            return candidates
        ranked = sorted(ranked_data, key=lambda x: x.get("total", 0), reverse=True)
        final = [r["name"] for r in ranked]
    except Exception as e:
        print(f"⚠️ JSON 파싱 실패: {e}")
        print("LLM 응답 원문:\n", raw)
        final = candidates

    # ⚠️ None 방지 — 비어 있으면 candidates 그대로 반환
    if not final:
        print("⚠️ LLM 정렬 결과가 비어 있습니다. 원본 candidates 사용.")
        final = candidates

    return final



def trend_select_agent(state: SystemState) -> SystemState:
    """
    TrendSelectAgent:
    - ranked_trends 리스트를 state에서 관리
    - 호출될 때마다 하나씩 trend를 꺼내 state["current_trend"]로 전달
    """

    if state is None:
        state = {}

    # 최초 실행이면 새로 후보 생성
    if "remaining_trends" not in state:
        docs = state.get("search_results", [])
        if not docs:
            print("❌ 검색 결과가 없습니다.")
            state["current_trend"] = None
            return state

        print("\n🔹 트렌드 후보 새로 생성 중...")
        candidates = extract_trend_candidates(docs)
        final_ranked = rank_by_future_relevance(candidates)

        print(f"  ▪ 최종 정렬된 트렌드 목록: {final_ranked}")
        state["remaining_trends"] = final_ranked
        state["search_results"] = docs

    # 남은 트렌드에서 하나 꺼내기
    remaining = state.get("remaining_trends", [])
    if not remaining:
        print("⚠️ 더 이상 남은 트렌드가 없습니다.")
        state["current_trend"] = None
        return state

    current = remaining.pop(0)
    print(f"\n🎯 TrendSelectAgent → 다음 트렌드 선택: {current}")

    # state 업데이트
    state["current_trend"] = current
    state["remaining_trends"] = remaining or []
    return state



if __name__ == "__main__":
    from agents.search_agent import search_agent
    from agents.state_schema import SystemState

    # state 초기화
    state: SystemState = {}

    query = (
        "Emerging AI technologies 2026 and beyond OR "
        "Next-generation AI research frontiers OR "
        "AI technologies expected to grow in next 5 years OR "
        "Future directions of AI innovation"
    )

    #  state와 query를 함께 전달
    state = search_agent(state, query)

    print("\nTrendSelectAgent 반복 테스트 시작")

    # 3번 반복 실행 (pop 동작 확인)
    for i in range(3):
        print(f"\n--- 실행 {i+1}회차 ---")
        result = trend_select_agent(state)

        if result["current_trend"] is None:
            print("⚠️ 더 이상 꺼낼 트렌드가 없습니다.")
            break

        print(f"선택된 트렌드: {result['current_trend']}")
        print(f" 남은 트렌드 수: {len(result['remaining_trends'])}")

