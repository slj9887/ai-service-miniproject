# agents/state_schema.py
"""
공통 state 구조 정의
모든 Agent가 공통으로 사용하는 데이터의 기본 형태를 정의한다.
"""

from typing import TypedDict, List, Optional, Dict, Any

class TrendAnalysis(TypedDict):
    definition: str
    key_technologies: str
    industry_trends: str
    adoption_flow: str
    future_outlook: str

class Scores(TypedDict):
    maturity: float
    growth: float
    applicability: float
    impact: float
    innovation: float

class SystemState(TypedDict, total=False):
    # 1️⃣ SearchAgent 결과
    search_results: List[Dict[str, Any]]  # Tavily 검색 결과 리스트
    
    # 2️⃣ TrendSelectAgent 결과
    remaining_trends: List[str]           # 남은 트렌드 목록
    current_trend: Optional[str]          # 현재 선택된 트렌드
    
    # 3️⃣ JudgeAgent 결과
    scores: Optional[Scores]              # 세부 점수
    total_score: Optional[float]          # 평균 점수
    is_qualified: Optional[bool]          # 적합 여부
    reason: Optional[str]                 # 요약 사유
    
    # 4️⃣ TrendAnalysisAgent 결과
    trend_analysis: Optional[TrendAnalysis]  # 트렌드 분석 결과
