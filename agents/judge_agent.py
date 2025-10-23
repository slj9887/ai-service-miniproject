"""
JudgeAgent
TrendSelectAgent에서 전달받은 트렌드를 평가
기술적 성숙도, 미래 성장성, 산업 적용성,  혁신성 및 차별성 네 가지 지표 기반으로
평균 계산 후 적합 여부 판단
"""

from agents.state_schema import SystemState

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import json

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")

##JudgeAgent
def judge_agent(state: SystemState) -> SystemState:
    """TrendSelectAgent에서 넘겨받은 current_trend 평가"""
    trend = state.get("current_trend")
    if not trend:
        print("평가할 트렌드가 없습니다.")
        state["is_qualified"] = False
        return state
    
    if not state.get("remaining_trends"):
        print("🚫 남은 트렌드가 없습니다. 워크플로우 종료.")
        return state

    
    print(f"\n JudgeAgent: '{trend}' 트렌드 평가 중...")

    prompt = ChatPromptTemplate.from_template("""
    당신은 2030년을 바라보는 미래 기술 분석가입니다.
    당신의 역할은 ‘냉철한 평가자’로서 기술을 객관적으로 판단하는 것입니다.  
    AI 기술에 대해 과도한 낙관 평가를 피하고,  
    기술적/상업적 한계와 불확실성도 반드시 반영하세요.
    이미 상용화된 기술을 제외하고 향후 3~5년 내에 급성장하거나 새롭게 등장할 가능성이 높은 기술을 중심으로 다음 평가 지표를 통해 평가하세요.

    트렌드명: {trend}

    [평가 지표]
    1. 기술 성숙도 (Technological Maturity)
   - 현재 연구/개발 단계, 상용화 여부
    2. 미래 성장성 (Market Growth Potential)
    - 향후 5년 내 시장 확장 가능성, 투자 및 시장 규모
    3. 산업 적용성 (Industrial Applicability)
    - 다양한 산업에서의 도입 가능성 및 효율성
    4. 혁신성 및 차별성 (Innovativeness & Differentiation)
    - 기존 기술 대비 혁신 정도, 새로운 패러다임 제시 여부
                                              
    [평가 지표 세부 기준]
    - 0.0 ~ 0.3: 매우 낮음 
    - 0.4 ~ 0.6: 중간 수준 
    - 0.7 ~ 0.8: 유망 
    - 0.9 ~ 1.0: 매우 유망 

                                              
    JSON 형식으로 출력:
    {{
    "trend": "{trend}",
    "scores": {{
        "maturity": 0.0~1.0,
        "growth": 0.0~1.0,
        "applicability": 0.0~1.0,
        "innovation": 0.0~1.0
    }},
    "total_score": 평균값,
    "is_qualified": true/false,
    "reason": "요약된 근거 (기술의 한계와 리스크 포함)"
    }}

    판단 기준:
    - total_score ≥ 0.65 → true (적합)
    - total_score < 0.65 → false (부적합)
    """)


    chain = prompt | llm
    response = chain.invoke({"trend": trend})
    raw_text = response.content.strip()

    # JSON 파싱
    try:
        result = json.loads(raw_text)
    except Exception:
        import re
        cleaned = re.sub(r"^```[a-zA-Z]*\n?|```$", "", raw_text).strip()
        try:
            result = json.loads(cleaned)
        except Exception:
            print("⚠️ JSON 파싱 실패. LLM 원문:\n", raw_text)
            result = {
                "trend": trend,
                "scores": {
                    "maturity": 0,
                    "growth": 0,
                    "applicability": 0,
                    "impact": 0,
                    "innovation": 0
                },
                "total_score": 0,
                "is_qualified": False,
                "reason": "LLM 응답 파싱 실패"
            }


    # 평가 결과 출력
        # 평가 결과 출력
    s = result.get("scores", {})

    print(f"  ▪ 기술 성숙도 (Maturity): {s.get('maturity')}")
    print(f"  ▪ 미래 성장성 (Growth): {s.get('growth')}")
    print(f"  ▪ 산업 적용성 (Applicability): {s.get('applicability')}")
    print(f"  ▪ 혁신성 및 차별성 (Innovation): {s.get('innovation')}")
    print(f"  ▪ 총점: {result.get('total_score')} ({'적합' if result.get('is_qualified') else '부적합'})")
    print(f"  ▪ 사유: {result.get('reason')}")

    state["state"] = s
    state["total_score"] = result.get("total_score", 0)
    state["is_qualified"] = result.get("is_qualified", False)
    state["judge_result"] = "기준 통과" if result.get("is_qualified") else "기준 미달"
    state["reason"] = result.get("reason","")

    return state


if __name__ == "__main__":
    from agents.trend_select_agent import trend_select_agent
    from agents.search_agent import search_agent
    from agents.state_schema import SystemState

    # ✅ state 초기화
    state: SystemState = {}

    query = (
        "Emerging AI technologies 2026 and beyond OR "
        "Next-generation AI research frontiers OR "
        "AI technologies expected to grow in next 5 years OR "
        "Future directions of AI innovation"
    )

    # ✅ search_agent 호출 시 state와 query 둘 다 전달
    state = search_agent(state, query)

    # 1️⃣ 트렌드 하나 선택
    selected = trend_select_agent(state)
    current_trend = selected["current_trend"]

    # 2️⃣ 선택된 트렌드 평가
    state["current_trend"] = current_trend
    result = judge_agent(state)

    print("\n✅ 최종 평가 결과:")
    print(result)

