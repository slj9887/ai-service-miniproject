# agents/risk_agent.py
"""
RiskAgent
트렌드의 위험요인과 기회요인을 분석한다.
입력 : TrendPredictAgent의 예측 결과
출력 : risk_analysis(SystemState에 저장)
"""

import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from agents.state_schema import SystemState

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")


def risk_agent(state: SystemState) -> SystemState:
    """TrendAnalysisAgent 결과를 바탕으로 미래 전망 생성"""

    trend = state.get("current_trend")
    prediction = state.get("trend_prediction", {})

    if not trend:
      print("⚠️ 트렌드 정보가 없습니다.")
      return state

    # trend_prediction 구조 확인
    prediction = state.get("trend_prediction")
    if not isinstance(prediction, dict) or not prediction.get("summary"):
        print("분석할 트렌드 또는 예측 정보가 없습니다.")
        print(f"[DEBUG] 현재 trend_prediction 값: {prediction}")
        return state


    
    print(f"RiskAgent: '{trend}' 트렌드의 리스크 및 기회 요인 분석중...")


    prompt = ChatPromptTemplate.from_template("""
    당신은 2030년 기술 정책 및 산업 전략 전문가입니다.
    아래는 {trend} 트렌드에 대한 기술 발전 및 시장 예측 정보입니다.
    이를 기반으로 기회 요인(Opportunities)과 위험 요인(Risks)을 도출하세요.

    [입력 정보]
    {prediction}

    [분석 항목]
    1 Opportunities (기회 요인)
      - 해당 기술이 산업/경제에 제공할 잠재적 이익
      - 새로운 시장 창출, 비용 절감, 생산성 향상 등

    2 Risks (위험 요인)
      - 기술적 불확실성, 사회적/정책적 리스크, 산업 혼란

    3 Policy & Regulation Factors (정책/규제 요인)
      - 법적/윤리적 이슈, 정부 규제, 표준화 동향

    4 Strategic Response (기업의 대응 전략)
      - 기업이 취해야 할 전략, 투자 방향, 협업 모델

    JSON 형식으로 출력:
    {{
      "risk_analysis": {{
        "opportunities": "",
        "risks": "",
        "policy_factors": "",
        "strategic_response": "",
        "summary": ""
      }}
    }}
    """)

    chain = prompt | llm
    response = chain.invoke({
        "trend": trend,
        "prediction": json.dumps(prediction, ensure_ascii=False, indent=2)
    })

    raw = response.content.strip()

    try:
        result = json.loads(raw)
        risk_data = result.get("risk_analysis",{})
    except Exception:
        import re
        cleaned = re.sub(r"^```[a-zA-Z]*\n?|```$", "", raw).strip()
        try:
            risk_data = json.loads(cleaned)["risk_analysis"]
        except Exception:
            print("⚠️ JSON 파싱 실패. LLM 응답 원문:\n", raw)
            risk_data = {
                "opportunities": "파싱 실패",
                "risks": "파싱 실패",
                "policy_factors": "파싱 실패",
                "strategic_response": "파싱 실패",
                "summary": "파싱 실패"
            }

    print("\n RiskAgent 분석 완료!\n")
    print(json.dumps(risk_data, indent=2, ensure_ascii=False))

    print(f"🧩 예측 결과 저장 완료: trend_prediction 키 존재 여부 = {'trend_prediction' in state}")
    print(f"🧩 예측 데이터 미리보기: {state.get('trend_prediction')}")

    # ✅ 기존 state 유지하면서 병합 (덮어쓰기 방지)
    from copy import deepcopy
    merged_state = deepcopy(state)
    merged_state["risk_analysis"] = risk_data

    print(f"[DEBUG] RiskAgent 종료 시 state keys: {list(merged_state.keys())}")
    print(f"[DEBUG] trend_prediction 유지 여부: {'trend_prediction' in merged_state}")
    print(f"[DEBUG] trend_prediction 내용 요약: {merged_state.get('trend_prediction', '없음')}")

    return merged_state



    




if __name__ == "__main__":
    # 테스트용 더미 입력
    dummy_state: SystemState = {
        "current_trend": "Federated Learning",
        "trend_prediction": {
            "tech_path": "Differential Privacy와 Secure Aggregation 기술이 향상될 전망",
            "market_outlook": "2030년까지 CAGR 25% 성장 예상",
            "industry_applications": "헬스케어, 금융, IoT 중심으로 확산",
            "barriers": "데이터 규제 및 초기 투자 비용",
            "summary": "데이터 프라이버시 중심 AI 인프라로 발전할 기술"
        }
    }

    result = risk_agent(dummy_state)
    print("\n🧩 최종 RiskAgent 결과:")
    print(json.dumps(result["risk_analysis"], indent=2, ensure_ascii=False))