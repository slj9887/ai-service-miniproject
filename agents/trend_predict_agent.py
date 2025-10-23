"""
TrendPredictAgent
선정된 트렌드에 대해 향후 3~5년간 기술 발전 방향과 시장 적용 가능성 예측
"""


import sys, os, json
import re

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from agents.state_schema import SystemState

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")


def trend_predict_agent(state: SystemState) -> SystemState:
    """TrendAnalysisAgent 결과를 바탕으로 미래 전망 생성"""

    if state is None:
        state = {}

    trend = state.get("current_trend")
    trend_analysis = state.get("trend_analysis")

    if not trend or not trend_analysis:
        print("분석할 트렌드 정보가 부족합니다. (trend_analysis 없음).")
        return state
    print(f"\n TrendPredictAgent: '{trend}' 트렌드의 미래 발전 방향 예측 중...")

    context = f"""
    [트랜드명]
    {trend}

    [트렌드 분석 요약]
    정의: {trend_analysis.get('definition')}
    핵심 기술: {trend_analysis.get('key_technologies')}
    산업 동향: {trend_analysis.get('industry_trends')}
    적용 흐름: {trend_analysis.get('adoption_flow')}
    미래 전망: {trend_analysis.get('future_outlook')}
    """

    prompt = ChatPromptTemplate.from_template("""
    당신은 2030년을 내다보는 기술 전략 분석가입니다.
    아래 정보를 바탕으로 {trend} 기술의 발전 방향, 시장 확장, 산업 적용 가능성을 예측하세요.
    예측은 근거를 바탕으로 하고 2500자 정도로 작성하세요.

    [분석 컨텍스트]
    {context}

    예측 시 고려할 요소:
    1. 기술 발전 경로 (연구/개발 단계, 주요 혁신 포인트)
    2. 시장 확장 및 투자 전망 (예상 CAGR, 성장 요인)
    3. 산업별 적용 가능성 (새로운 산업군, 기존 산업에서의 확장성)
    4. 기술적/정책적 장애 요인
    5. 향후 5년간의 전반적 전망 요약

    출력 형식 (JSON):
    {{
      "trend": "{trend}",
      "prediction": {{
        "tech_path": "",
        "market_outlook": "",
        "industry_applications": "",
        "barriers": "",
        "summary": ""
      }}
    }}
                                              
    응답은 반드시 JSON 형식 **그 자체만** 출력하세요.
    코드블록(```)이나 문장, 설명은 절대 포함하지 마세요.
    """)

    chain = prompt | llm
    response = chain.invoke({"trend": trend, "context": context})
    raw = response.content.strip()

    def safe_parse_json(raw_text):
        """Markdown, 문장 등이 포함된 응답에서도 JSON만 추출"""
        try:
            return json.loads(raw_text)
        except Exception:
            # ```json ... ``` 제거
            cleaned = re.sub(r"```(?:json)?|```", "", raw_text, flags=re.DOTALL).strip()
            # JSON 괄호 내부만 추출
            cleaned = re.sub(r"^[^{]*({.*})[^}]*$", r"\1", cleaned, flags=re.DOTALL)
            try:
                return json.loads(cleaned)
            except Exception:
                print("⚠️ JSON 파싱 실패. LLM 원문:", raw_text[:300], "...")
                return None


    result = safe_parse_json(raw)

    # ✅ JSON 파싱 실패 시 기본 구조 생성
    if not result or not isinstance(result, dict):
        print("⚠️ JSON 파싱 실패. LLM 응답 원문:\n", raw)
        result = {
            "tech_path": "",
            "market_outlook": "",
            "industry_applications": "",
            "barriers": "",
            "summary": "파싱 실패"
        }

    # ✅ "prediction" 키가 있으면 내부로, 없으면 전체를 사용
    if isinstance(result, dict):
        if "prediction" in result and isinstance(result["prediction"], dict):
            prediction_data = result["prediction"]
        else:
            prediction_data = result
    else:
        prediction_data = {}

    # ✅ 비어 있을 경우 기본값 제공
    if not prediction_data or not isinstance(prediction_data, dict):
        prediction_data = {
            "tech_path": "",
            "market_outlook": "",
            "industry_applications": "",
            "barriers": "",
            "summary": "LLM 응답이 비어 있음"
        }

    # ✅ state 안전하게 복사 후 저장
    state = dict(state)
    state["trend_prediction"] = prediction_data

    print("\n TrendPredictAgent 예측 완료!\n")
    print(json.dumps(state["trend_prediction"], indent=2, ensure_ascii=False))
    print(f"🧩 [DEBUG] TrendPredictAgent 종료 시 state keys: {list(state.keys())}")
    print(f"🧩 [DEBUG] trend_prediction 내용 타입: {type(state['trend_prediction'])}, 값: {state['trend_prediction']}")
    print(f"[DEBUG] TrendPredictAgent 최종 반환 직전 state keys: {list(state.keys())}")
    print(f"[DEBUG] TrendPredictAgent 최종 반환 직전 trend_prediction: {state.get('trend_prediction')}")


    return state




if __name__ == "__main__":
    # 테스트 실행
    dummy_state: SystemState = {
        "current_trend": "Federated Learning",
        "trend_analysis": {
            "definition": "분산 데이터 기반 학습 기술로, 개인정보 보호를 강화하면서 협업형 AI 학습을 가능하게 함.",
            "key_technologies": "Differential Privacy, Secure Aggregation, Decentralized Optimization",
            "industry_trends": "헬스케어, 금융, IoT 산업에서 빠르게 도입 중",
            "adoption_flow": "대기업과 스타트업 중심으로 PoC 및 초기 상용화 단계",
            "future_outlook": "데이터 주권 및 보안 중심의 AI 인프라로 성장 예상"
        }
    }

    result = trend_predict_agent(dummy_state)
