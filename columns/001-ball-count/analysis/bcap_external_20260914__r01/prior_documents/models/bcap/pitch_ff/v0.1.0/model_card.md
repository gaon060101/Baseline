# BCAP-PITCH-FF-v0.1.0

**2024·2025 개발 비교 완료, 외부 검증 미실시 — EXPERIMENTAL**. UTC 2026-09-11T17:56:49.616639+00:00. DRAFT에서 실제 개발 실행 완료에 따라 갱신했다. specification.yaml의 status_at_definition은 정의 당시 기록으로 보존했다.

현재 한 구의 FF(포심) 대 non-FF(비포심)와 최종 PA 공격가치 W의 보정 연관 비교다. 같은 실제 지지 행에 양 행동을 표준화하며 가상 평균 선수나 PA 전체 순차 정책을 추정하지 않는다. 기존 BCAP-PITCH-v0.2.0의 FB/NFB 비교와 행동 내용이 달라 별도 모듈로 등록했다. 기존 버전의 상태·결과는 변경하지 않았다.

FF=FF. non-FF=SI,FC,SL,CH,ST,CU,FS,KC,SV,FA,EP,KN,FO,CS,SC. active mapping은 명세의 action_codes다. actions에 남아 있는 기존 분류 사전은 상속한 참조이며 새 A를 결정하지 않는다. 기존 eligible_pitch를 그대로 사용하고 PO/UN/결측·기존 PA 제외를 비포심에 채우지 않는다. FA/Other의 분류 한계를 유지한다.

기존 투구 전14개 입력과 직전 FB/NFB, 투수·타자 shrinkage, 3fold 경기 분리·seed20260909·훈련 안 Platt, alpha p100/m0=m1=1000을 유지했다. 새 FF용 propensity와 두 결과모형만 새 A로 적합했다. 현재 구종·위치·속도·스윙·타구 결과를 입력하지 않는다. 외부/반복 학습·튜닝·학습 정책은 없다.

전체 적격 1,415,566행, FF 자체 지지 1,271,802행(89.84%), FB 자체 1,395,443행, 공통 1,268,736행이다. FF 자체 지지와 FB 지지의 교집합에서 각자의 OOF 점수를 재집계했으며 교집합으로 재학습하지 않았다. 지원은 선택확률 범위와 훈련 투수 행동 수 기준이며 선수 능력을 뜻하지 않는다.

결과: FF3-2 공통 Δ=+0.01699 W, Bonferroni255 명목95% [+0.00141,+0.03257]로 비포심 방향의 개발 단서가 있다. 구간 하한이0.01 W보다 작아 최소 실질 차이를 확보한 것은 아니다. 0-0은 두 분류의 자체·공통 구간 모두±0.01 W 안이다. FF3-0은 실질적인 분할 부호 반전이 있어 보류한다. 다른 카운트 대부분은 충분히 구분하지 못했다.

[한국어 HTML 보고서](../../../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/report.html) · [보고서 Markdown](../../../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/report.md) · [새 FF 학습](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2024_2025__20260912__r01/manifest.json) · [기존 FB 재사용 및 자체/공통 비교](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/manifest.json) · [기본 확인 범위](validation.md) · [추가 결과 전 기준](../../../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/analysis_plan.json) · [재현 명령](../../../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/reproduction.md)

선택집단·미측정 의도·품질·컨디션과 결과모형 의존성이 남는다. 고정 점수의 경기 변동 구간은 전체 재학습 불확실성·경기 간 선수 의존성·실제95% 포함률을 검증한 것이 아니다. 외부 미검증이며 인과적 투구 지시나 일반적인 구종 우열을 권고하지 않는다.
