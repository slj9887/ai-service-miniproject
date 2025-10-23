"""
SearchAgent
최근 기술 트랜드를 Tavily로 구현
검색한 결과를 반환
"""
from agents.state_schema import SystemState

import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search_agent(state: SystemState) -> SystemState:
    """Tavily 검색 실행"""
    if state is None:
        state = {}

    queries = [
    '"AI technologies that are not yet commercialized but expected to gain significant attention within the next 3–5 years"',
    '"paradigm-shifting AI technologies emerging in the next 3–5 years"',
    '"next frontier areas of AI research"',
    '"disruptive AI innovations around 2030 that will reshape industries"',
    '"future AI architectures that will lead the next paradigm shift"',
    ]    

    reliable_sources = [
    "nature.com", "arxiv.org", "research.ibm.com",
    "deepmind.google", "mit.edu", "stanford.edu",
    "openai.com", "microsoft.com/en-us/research",
    "nvidia.com", "hbr.org"
    ]
    site_filter = " OR ".join([f"site:{d}" for d in reliable_sources])

    results = []
    for q in queries:
        filtered_query = f"{q} AND ({site_filter})"
        print(f"🔍 Tavily 검색 중: {filtered_query}")
        try:
            res = tavily.search(filtered_query, max_results=5)
            results.extend(res.get("results", []))
        except Exception as e:
            print(f"⚠️ 검색 실패: {e}")


    try:
        response = tavily.search(filtered_query, max_results=20)
        results = response.get("results", [])
    except Exception as e:
        print(f"⚠️ Tavily 검색 실패: {e}")
        state["search_results"] = []
        return state

    if not results:
        print("⚠️ 검색 결과가 없습니다.")
        state["search_results"] = []
        return state
    

    
    formatted_results = [
        {
            "title": r.get("title", "제목 없음"),
            "url": r.get("url", "N/A"),
            "content": r.get("content", "")[:500]
        }
        for r in results
    ]

    print(f" {len(formatted_results)}개 문서 수집 완료 (신뢰 도메인 한정)")
    state["search_results"] = formatted_results
    return state



if __name__ == "__main__":
    from agents.state_schema import SystemState

    # 초기 state 생성
    dummy_state: SystemState = {}

    
    queries = [
        "Emerging AI technologies 2026 and beyond",
        "Next-generation AI research frontiers",
        "AI technologies expected to grow in next 5 years",
        "Future directions of AI innovation"
    ]

    # 여러 쿼리를 OR로 연결해서 Tavily가 다양한 결과를 수집하도록 함
    combined_query = " OR ".join(queries)

    # ✅ state와 query를 모두 전달해야 함
    updated_state = search_agent(dummy_state, combined_query)

    # ✅ 결과 출력
    results = updated_state.get("search_results", [])
    print(f"\n총 {len(results)}개 결과 확인 완료 ✅")

    for i, r in enumerate(results, start=1):
        print(f"\n{i}. {r['title']}\n   {r['url']}\n   {r['content'][:100]}...")

