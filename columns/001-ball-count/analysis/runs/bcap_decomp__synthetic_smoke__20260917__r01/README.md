# BCAP 분해 인터페이스 모의 확인

2026-09-17 · BCAP-DECOMP-v0.1.0 · **DRAFT**

실제 MLB 자료를 학습하거나 새 행동 가치를 추정하지 않았다. 두 개의 모의 투구에 임의의 예측값을 넣어 합성·입력 거부·파일 보존 등 **21개 작은 확인을 통과**했다. 이 PASS는 통계 검증이나 기존 BCAP의 개선을 뜻하지 않는다.

- [manifest](manifest.json): Python 환경, 실행 시각, 입력·코드·설정·결과 SHA256
- [모의 입력](artifacts/synthetic_input.json) · [모의 집계 출력](artifacts/synthetic_output.json) · [21개 확인 기록](artifacts/checks.json)
- [모델 카드](../../../../../models/bcap/decomposition/v0.1.0/model_card.md) · [입력 계약](../../../../../models/bcap/decomposition/v0.1.0/input_contract.md)

모의 값은 산술 검사를 위한 임의 숫자이며 칼럼의 실증 수치로 쓰면 안 된다. 실제 분석에 필요한 분기 확률·조건부 W 적합, 경험적 지원·교정·불확실성 설계는 남아 있다. 새 업로드 제외 원자료·정제본·캐시는 생성하지 않았다.

프로젝트 루트에서 새 실행 폴더를 지정한다. 완료 폴더를 주면 실패한다.

```powershell
python -B models/bcap/decomposition/v0.1.0/run_smoke.py --out columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r02
```

기존 모델과 완료 실행은 수정하지 않았고 재학습·추가 seed·부트스트랩·외부 연도 적용·원자료 재검사는 수행하지 않았다.
