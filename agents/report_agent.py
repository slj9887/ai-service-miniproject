"""
ReportAgent
이전 모든 Agent의 결과를 종합해 완전한 트렌드 분석 보고서 생성
"""
import os
import json
from fpdf import FPDF
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.state_schema import SystemState
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")



class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('NotoSans', '', 'fonts/NotoSansKR-Regular.ttf')
        self.add_font('NotoSans', 'B', 'fonts/NotoSansKR-Bold.ttf')
        self.set_auto_page_break(auto=True, margin=15)

    def add_title_page(self):
        """표지 — AI 트렌드 분석 보고서만 출력"""
        self.add_page()
        self.set_font('NotoSans', 'B', 26)
        self.cell(0, 15, "AI 트렌드 분석 보고서", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(7)  

    def add_section(self, title, text):
        """본문 섹션"""
        self.set_font('NotoSans', 'B', 16)
        self.multi_cell(0, 8, title)
        self.ln(3)

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("### "):
                self.ln(2)
                self.set_font('NotoSans', 'B', 13)
                self.multi_cell(0, 7, line.replace("### ", ""))
                self.ln(2)

            elif line.startswith("## "):
                self.ln(4)
                self.set_font('NotoSans', 'B', 14)
                self.multi_cell(0, 8, line.replace("## ", ""))
                self.ln(2)

            elif line.startswith("# "):
                self.set_font('NotoSans', 'B', 16)
                self.multi_cell(0, 9, line.replace("# ", ""))
                self.ln(4)

            else:
                self.set_font('NotoSans', '', 11)
                self.multi_cell(0, 6, line)
                self.ln(5)






def report_agent(state: SystemState) -> SystemState:
    """TrendAnalysis, Predict, Risk 결과를 종합해 보고서 생성"""
    trend = state.get("current_trend")
    if not trend:
        print("current_trend가 없습니다.")
        return state
    print(f"ReportAgent: '{trend}' 보고서 생성중...")

    # 개별 섹션 내용 가져오기
    analysis = state.get("trend_analysis", {})
    prediction = state.get("trend_prediction", {})
    risk = state.get("risk_analysis", {})
    search_results = state.get("search_results", [])

    # 참고 문헌 URL 정리
    reference_urls = [r["url"] for r in search_results if r.get("url")] if search_results else []

     # 보고서 프롬프트
    prompt = ChatPromptTemplate.from_template("""
    당신은 미래 기술 전략 보고서를 작성하는 전문 분석가입니다.
    아래 제공된 분석 내용을 기반으로 {trend} 트렌드에 대한 완전한 기술 보고서를 작성하세요.

    보고서 목차는 다음과 같으며, 반드시 포함하세요:

    1. SUMMARY  - 주요 AI 트렌드 요약과 기업 관점 핵심 시사점을 하나의 문단으로 작성

    2. 트렌드 분석  
       2.1 트렌드 정의 및 등장 배경  
       2.2 주요 기술 및 사례  
       2.3 기업 및 산업 동향  
       2.4 산업별 적용 흐름  
       2.5 향후 5년간의 기술 발전 및 시장 변화 예측  

    3. 기업 전략 인사이트  
       3.1 비즈니스 기회 요인  
       3.2 리스크 및 대응 전략  
       3.3 기업 적용을 위한 제안  

    4. 참고 문헌  
       - 출처 URL 리스트 포함  

    5. APPENDIX  
       - 트렌드 선정 지표 세부 내용  
         - 기술적 성숙도  
         - 미래 성장성  
         - 산업 적용성  
         - 혁신성 및 차별성  

    --------------------------
    [분석 자료 요약]
    - Trend Analysis: {analysis}
    - Trend Prediction: {prediction}
    - Risk Analysis: {risk}
    - References: {references}
    --------------------------

    - 보고서는 자연스러운 한국어로 작성하되, 기술 용어는 영어 병기 가능.
    - 문단 간 명확한 구분과 제목 표기를 포함하세요.
    """)

    chain = prompt | llm
    response = chain.invoke({
        "trend": trend,
        "analysis": json.dumps(analysis, ensure_ascii=False, indent=2),
        "prediction": json.dumps(prediction, ensure_ascii=False, indent=2),
        "risk": json.dumps(risk, ensure_ascii=False, indent=2),
        "references": json.dumps(reference_urls, ensure_ascii=False)
    })

    report_text = response.content.strip()
    state["final_report"] = {
        "trend": trend,
        "report_text": report_text
    }


    os.makedirs("reports", exist_ok=True)
    pdf_path = f"reports/{trend.replace(' ', '_')}_report.pdf"

    pdf = PDF()
    pdf.add_title_page()
    pdf.add_section("",report_text)
    pdf.output(pdf_path)

    print(f"\n ReportAgent: '{trend}' 보고서 생성 완료!")
    print(f" PDF 저장 위치: {pdf_path}")

    return state



if __name__ == "__main__":
    dummy_state: SystemState = {
        "current_trend": "Federated Learning",
        "trend_analysis": {
            "definition": "분산 데이터 기반 학습 기술로, 개인정보 보호를 강화하면서 협업형 AI 학습을 가능하게 함.",
            "key_technologies": "Differential Privacy, Secure Aggregation, Decentralized Optimization",
            "industry_trends": "헬스케어, 금융, IoT 산업에서 빠르게 도입 중",
            "adoption_flow": "대기업과 스타트업 중심으로 PoC 및 초기 상용화 단계",
            "future_outlook": "데이터 주권 및 보안 중심의 AI 인프라로 성장 예상"
        },
        "trend_prediction": {
            "tech_path": "Differential Privacy와 Federated Learning 융합 연구 활발",
            "market_outlook": "2030년까지 연평균 25% 성장 예상",
            "industry_applications": "헬스케어, 금융, IoT 분야에서 상용화 확대",
            "barriers": "표준화 및 법적 규제 문제",
            "summary": "데이터 프라이버시 중심 AI 인프라로 자리 잡을 것"
        },
        "risk_analysis": {
            "opportunities": "데이터 보호 수요 증가, 글로벌 시장 확대",
            "risks": "초기 비용, 복잡성, 표준화 문제",
            "policy_factors": "데이터 규제 및 개인정보보호법 영향",
            "strategic_response": "규제 대응, R&D 투자, 표준화 주도 필요",
            "summary": "위험 대비 성장 가능성이 더 큼"
        },
        "search_results": [
            {"url": "https://www.nature.com/articles/federated-learning"},
            {"url": "https://www.mckinsey.com/ai/federated-learning-market-forecast"}
        ]
    }

    result = report_agent(dummy_state)
    print("\n 생성된 보고서 요약:")
    print(result["final_report"]["report_text"][:1000])