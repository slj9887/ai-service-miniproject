"""
main.py
TrendSelectAgent + JudgeAgent 루프 테스트
"""

from agents.search_agent import search_agent
from agents.trend_select_agent import trend_select_agent
from agents.judge_agent import judge_agent

# 1️⃣ 초기 검색
query = "Emerging AI technologies 2026 and beyond OR Next-generation AI research frontiers OR AI technologies expected to grow in next 5 years OR Future directions of AI innovation"
search_results = search_agent(query)

# 2️⃣ state 생성
state = {"search_results": search_results}

# 3️⃣ 루프 시작
print("\n🚀 메인 루프 시작 (적합한 트렌드 찾기 테스트)\n")

max_attempts = 10  # 최대 10개 트렌드만 테스트
for attempt in range(max_attempts):
    print(f"\n🔄 [{attempt+1}회차] TrendSelectAgent 호출")
    select_result = trend_select_agent(state)
    current_trend = select_result["current_trend"]

    if not current_trend:
        print("❌ 더 이상 평가할 트렌드가 없습니다.")
        break

    # JudgeAgent 평가 실행
    print(f"\n JudgeAgent '{current_trend}' 평가 시작...")
    state["current_trend"] = current_trend
    judge_result = judge_agent(state)

    if judge_result.get("is_qualified"):
        print(f"\n✅ '{current_trend}' 트렌드 적합 판정! 루프 종료.")
        break
    else:
        print(f"\n❌ '{current_trend}' 트렌드 부적합 → 다음 후보로 이동.")
else:
    print("\n⚠️ 모든 트렌드 평가 완료 (적합한 항목 없음)")
