"""
main_graph.py
LangGraph 기반 AI 트렌드 자동 분석 루프
"""
from langgraph.graph import StateGraph, START, END
from agents.state_schema import SystemState
from agents.search_agent import search_agent
from agents.trend_select_agent import trend_select_agent
from agents.judge_agent import judge_agent
from agents.trend_analysis_agent import trend_analysis_agent
from agents.trend_predict_agent import trend_predict_agent
from agents.risk_agent import risk_agent
from agents.report_agent import report_agent


def build_graph():
    graph = StateGraph(SystemState)

    # ✅ 노드 정의
    graph.add_node("search", search_agent)
    graph.add_node("select", trend_select_agent)
    graph.add_node("judge", judge_agent)
    graph.add_node("analysis", trend_analysis_agent)
    graph.add_node("predict", trend_predict_agent)
    graph.add_node("risk", risk_agent)
    graph.add_node("report", report_agent)

    # ✅ 흐름 연결
    graph.add_edge(START, "search")
    graph.add_edge("search", "select")
    graph.add_edge("select", "judge")

    # 조건 분기: 적합성 판단 결과에 따라 흐름 분리
    def route_after_judge(state: SystemState):
        if state.get("is_qualified"):
            return "analysis"
        else:
            print(f"🚫 '{state.get('current_trend')}' 기준 미달 → 다음 트렌드로 재선택")
            return "select"

    graph.add_conditional_edges("judge", route_after_judge, {
        "analysis": "analysis",
        "select": "select",
    })

    # 나머지 직선 연결
    graph.add_edge("analysis", "predict")
    graph.add_edge("predict", "risk")
    graph.add_edge("risk", "report")
    graph.add_edge("report", END)

    return graph.compile()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # 초기 state
    state = SystemState()

    # 그래프 실행
    workflow = build_graph()
    result = workflow.invoke(state)

    # 그래프 시각화
    print(workflow.get_graph().draw_ascii())

    print("\n🎯 파이프라인 완료!")
    print(f"📄 최종 보고서: {result.get('final_report', {}).get('path', 'N/A')}")
