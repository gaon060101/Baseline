# 공식 측정 설명 확인

열람: 2026-09-09. [MLB / Baseball Savant CSV 설명](https://baseballsavant.mlb.com/csv-docs)을 웹 도구로 직접 열어 확인했다. 새 플레이 원본은 수집하지 않았다.

balls/strikes, on_1b/on_2b/on_3b, outs_when_up, inning은 투구 전 필드다. bat_score/fld_score 및 home_score/away_score도 투구 전이며 post_*는 사후다. 따라서 이 검수는 raw bat_score_diff를 두 독립 표기 방식의 투구 전 차와 대조했다.

공식 설명상 plate_x/z는 2025까지 앞면, 2026부터 중간면이고 sz_top/bot도 2026부터 ABS 존으로 바뀐다. 그 변화가 없는 동일 측정값이라고 가정하지 않았고 SWING 2026 모델 평가는 하지 않았다. CSV description은 결과 투구의 설명이지 선수 의도나 실시간 지각 관측값이라는 정의가 아니다.

웹 원문 전체 복제 대신 확인 범위와 링크만 저장했다. 원문 서버 과거 버전 불변은 이 메모의 검증 범위가 아니다.
