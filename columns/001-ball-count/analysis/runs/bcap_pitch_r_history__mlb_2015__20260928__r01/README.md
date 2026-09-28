# bcap_pitch_r_history__mlb_2015__20260928__r01

R 계산 완료 · EXPERIMENTAL.

기존 보조 모형을 불러오지 않고 R에서 centered ridge·Platt calibration·3fold OOF AIPW를 다시 적합했다.
SB는 원 개발에서 선택된 α를 고정했고 튜닝은 반복하지 않았다. 같은 게임 분할이 제공되면 이를 그대로 재생한다.

블로그용 그림: artifacts/count_by_year.png. 표: action_values.csv, year_values.csv, year_differences.csv(해당 시).

관찰상 비교이며 인과 효과나 행동 추천이 아니다. 학습 변동·경기 간 선수 의존성은 구간에 포함되지 않는다.
2024·2025 연도 차이는 고정 OOF 점수의 독립 경기 근사이며, 공유된 학습 모형의 불확실성은 포함하지 않는다.
