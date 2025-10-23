"""
TrendAnalysisAgent
선정된 트렌드의 연구, 산업, 시장, 리스크 등 정보를 RAG 기반으로 분석
"""

import os
from typing import Dict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
from dotenv import load_dotenv
from agents.state_schema import SystemState, TrendAnalysis 
from utils.data_cleaner import clean_text

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
llm = ChatOpenAI(model="gpt-4o-mini")


def trend_analysis_agent(state: SystemState) -> SystemState:
    """
    TrendAnalysisAgent:
    1. Tavily로 트렌드 관련 문서 수집
    2. 벡터 스토어로 임베딩
    3. Retriever 기반 RAG 분석 수행
    4. 분석 결과를 state.trend_analysis에 저장
    """

    if state is None:
        state = {}

    trend = state.get("current_trend")
    if not trend:
        print("분석할 트랜드(current_trend)가 없습니다.")
        return state
    print(f"\n TrendAnalysisAgent: '{trend}' 트렌드 분석 시작...")

    # (③) Tavily 검색 부분 교체
    reliable_domains = [
        "nature.com", "arxiv.org", "mit.edu", "stanford.edu",
        "mckinsey.com", "weforum.org", "unctad.org", "nvidia.com",
        "microsoft.com/en-us/research", "deepmind.google"
    ]
    site_filter = " OR ".join([f"site:{d}" for d in reliable_domains])
    query = f"({trend} technology trends 2026 OR industrial applications OR challenges OR market forecast) AND ({site_filter})"

    print(f"🔍 검색 쿼리: {query}")
    response = tavily.search(query, max_results=20)
    results = response.get("results", [])

    docs = [
    Document(
        page_content=clean_text(r.get("content", "")[:1000]),
        metadata={"url": r.get("url")}
    )
    for r in results if r.get("content")
]

    print(f"📄 관련 문서 {len(docs)}개 수집 완료")
    if not docs:
        print("⚠️ 분석 가능한 문서가 없습니다.")
        state["trend_analysis"] = {"error": "문서 수집 실패"}
        return state
    

    #임베딩 + Chroma 벡터스토어 구축
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever(k=5)

    queries = {
        "definition": f"What is {trend} and why is it emerging?",
        "key_technologies": f"What are the core technologies or research areas driving {trend}?",
        "industry_trends": f"Which industries are adopting {trend}, and what are the notable use cases?",
        "adoption_flow": f"What stages of adoption are industries currently in for {trend}?",
        "future_outlook": f"What is the expected evolution or market forecast for {trend} by 2030?"
    }

    analysis: Dict[str, str]={}


    for topic, question in queries.items():
        retrieved_docs = retriever.invoke(question)
        combined_text = "\n\n".join([d.page_content for d in retrieved_docs])

        prompt = ChatPromptTemplate.from_template("""
        당신은 2030년을 내다보는 미래 기술 분석가입니다.
        다음 문서를 참고하여 '{trend}' 트렌드의 '{topic}'에 대해 분석을 작성하세요.
        "각 항목은 무조건 3문단 이상으로 작성하고, 기술적/산업적 근거를 포함하세요."


        ==== 문서 ====
        {context}
        """)

        chain = prompt | llm
        response = chain.invoke({"trend": trend, "topic": topic, "context": combined_text})
        analysis[topic] = response.content.strip()

        print(f"{topic} 분석 완료")

    state["trend_analysis"] = analysis  
    state["vectorstore_info"] = {"trend": trend, "doc_count": len(docs)} 

    print(f"\n📊 '{trend}' 분석 완료! ({len(docs)}개 문서 기반)")
    return state


if __name__ == "__main__":
    # ✅ 테스트용 실행
    state: SystemState = {"current_trend": "Federated Learning"}
    result = trend_analysis_agent(state)

    print("\n🧩 최종 분석 요약:")
    for k, v in result["trend_analysis"].items():
        print(f"\n[{k.upper()}]\n{v}\n")