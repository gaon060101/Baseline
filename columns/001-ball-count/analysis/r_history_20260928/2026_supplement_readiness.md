# 2026년 R 보조 분석 준비 상태

2026-09-28 로컬 원본 검토. 이 문서는 **2026-09-07까지의 보관 자료를 재사용할 준비 상태**를 확인한 기록이며, R 보조 분석의 실행·완료 보고서가 아니다. 실제 실행 결과는 새 실행의 manifest로 별도 확인한다. 이 검토에서는 다운로드, 모델 적합, 기존 실행 수정 없이 원본·정제본·출처 해시와 저장된 분석 계획을 확인했다.

## 사용할 범위와 입력

- 기간: 2026-03-25~2026-09-07, MLB 정규시즌. 2026 전체 시즌이나 현재 최신 자료로 표시하지 않는다.
- 원본 폴더 S: `columns/001-ball-count/data/raw/mlb/2026/snapshot_20260908_ridge_v02`.
- 보완 폴더 T: `columns/001-ball-count/data/raw/mlb/2026/supplement_20260909_ridge_v02`.
- 원본 CSV는 S의 34개와 T의 1개, 총 35개다. 아래 명시된 파일만 사용한다. CSV마다 BCAP 준비에 필요한 31개 필드가 모두 있음을 헤더에서 확인했다.
- 일정: `S/schedule_2026.json`, SHA-256 `c988379d50a35284bc87b8c6e82b3a50c9b8c059df867532f8195c84c4380d88`.
- T의 보완 CSV 3,239행을 빼면 11경기가 빠진다: 823175, 823254, 823415, 823742, 823820, 823902, 824062, 824229, 824715, 824793, 824958.
- 기존 준비 감사 기록의 집계: 원본 639,042행, 전체 164,281타석, 유효 163,327타석, PITCH 유효 635,095행, SWING 라벨 유효 635,451행. 이 집계는 원래 감사 자료의 값이며 이번 준비 검토에서 모든 행을 다시 계산한 값은 아니다. SWING 라벨 유효 행이 존재한다는 사실은 2026 SWING 모델 실행 허용을 뜻하지 않는다.

35개 CSV와 일정의 실제 SHA-256을 기존 v1 준비 감사 기록의 입력 해시와 비교해 **36개 모두 일치**했다. 해시 검토 시각: 2026-09-28T12:30:04.3694077+09:00. 아래 행 수는 기존 입력 감사 기록의 값이다.

| 파일(S/T는 위 폴더) | 기록된 행 수 | 실제 SHA-256(기록과 일치) |
| --- | ---: | --- |
| S/statcast_2026-03-25_2026-03-29.csv | 14,252 | `abef559ed8d5646cd235ca0d4ff52853e23792fedb748369dc6d238d99f85a78` |
| S/statcast_2026-03-30_2026-04-03.csv | 17,870 | `ab60362ecda705d741e55fbe4c687aa14d29450433f498d162ff9f7e74f0da4e` |
| S/statcast_2026-04-04_2026-04-08.csv | 22,473 | `a9db3b322075ed809a20dd913aa128338d15f2a10d694ddb04739f643b3bc3c3` |
| S/statcast_2026-04-09_2026-04-13.csv | 18,096 | `4bc421f07af0d97e29d3e744547ce9ec9e3292b7522c948b88c1db75b575d7c8` |
| S/statcast_2026-04-14_2026-04-18.csv | 21,066 | `9e6cacd02a3336a7379721c87ee739d2d8ac2884bb60f31f68b7a1611ceecb41` |
| S/statcast_2026-04-19_2026-04-23.csv | 19,181 | `4bb1f66f24d5a20e6c9e46b39cb0fb70ac544489cb6d70a9f68d5784d7ff0144` |
| S/statcast_2026-04-24_2026-04-28.csv | 19,826 | `6bde5ab20792cc3d72a06b9dc990862b9b7f876a2abca443b81157c4ba02bb14` |
| S/statcast_2026-04-29_2026-05-03.csv | 20,309 | `9e4a153b0dd33a313c0a3b672d03511b2ff4b14bb25a52d839062ce1ed1fc2f2` |
| S/statcast_2026-05-04_2026-05-08.csv | 18,571 | `44d6b05fb15256b9fa8ab1d2dc8b655aa4e80d13e1ffee23bca4bf794a9ad682` |
| S/statcast_2026-05-09_2026-05-13.csv | 19,169 | `344a755110c51cd3f90006b96f34fd99f64639898f048d27da219069eae5a433` |
| S/statcast_2026-05-14_2026-05-18.csv | 20,470 | `56cc3168f3a2a239fe12ba645c6696fb628485bd6515e5efbabc661d1d0c0040` |
| S/statcast_2026-05-19_2026-05-23.csv | 18,716 | `46eaf5ab9f0af579c2c9eb92fe6171697a1e2eaffc099c6741ae702b3b443b42` |
| S/statcast_2026-05-24_2026-05-28.csv | 18,401 | `7d80124191cbd9f35f0b0ad294e5900a114fe1ad822408f12f509e338933294b` |
| S/statcast_2026-05-29_2026-06-02.csv | 20,541 | `50c917ff61119e460d81b65ebd9cf3f3c198fe6dad8397baea2e18591ca6bc89` |
| S/statcast_2026-06-03_2026-06-07.csv | 20,095 | `70dd83ce61db4897e6043ba309e4b3a7f80bb471a6bc00605fa7b4ab7c66c220` |
| S/statcast_2026-06-08_2026-06-12.csv | 18,296 | `491806bd72e3fa38c9da17fa2451ce9c985d78b3818f28258f62e80acd9fed0b` |
| S/statcast_2026-06-13_2026-06-17.csv | 19,680 | `91988e6c2e63f9ccd1624f35100811f5e837269d163475a5a5760a622091c986` |
| S/statcast_2026-06-18_2026-06-22.csv | 17,786 | `d0cc3d4ab9904705b7a52cdf4f1f70fd790a819f3db10cbe5af3dcd7384f39b2` |
| S/statcast_2026-06-23_2026-06-27.csv | 20,349 | `769a7f005b4d8f12bcda433b9dfd5bfe905ab2da40e2395504c04a0310379179` |
| S/statcast_2026-06-28_2026-07-02.csv | 19,298 | `4c5c09cc8c322af0e5c17363a05f956e78f019b0a75fe3a98c87074d366e35cf` |
| S/statcast_2026-07-03_2026-07-07.csv | 20,192 | `d9e9a082400a892092e282fe0a551c9c36cd9bf5213599c7bcee27a68064aa86` |
| S/statcast_2026-07-08_2026-07-12.csv | 21,151 | `685c5cacafc166634b1566b3275c0eaa2c783d7ae26ae271edd97baf176c60e9` |
| S/statcast_2026-07-13_2026-07-17.csv | 4,527 | `c95b8d4b11d7378b5b428de691b650f10ac56fc0fd52e2cf3c81d48f49581b45` |
| S/statcast_2026-07-18_2026-07-22.csv | 22,288 | `08a6278d767ee0fc3c62bdac50f7cc1f6fb0c9611ecd8682514d5cfce0391612` |
| S/statcast_2026-07-23_2026-07-27.csv | 17,875 | `b18b42dd16c21166b8e04fbdc0b2c8ce6057c9e57c3a85f7d5be9891f3d7ad48` |
| S/statcast_2026-07-28_2026-08-01.csv | 21,023 | `6b653aaac1c65165c19069cfd48cf32ad29cef22c5a079f98c36c724e43a5fb0` |
| S/statcast_2026-08-02_2026-08-06.csv | 18,750 | `6622bcaab7caa1f5103ace5d2983ec2f5fa6b7bd90dfc5827def2db6ef060525` |
| S/statcast_2026-08-07_2026-08-11.csv | 20,670 | `37f8ca9722b526640d339d81d6bfc6f8c6a1d3917355b23786c8ab65ab945aa0` |
| S/statcast_2026-08-12_2026-08-16.csv | 19,895 | `3d813e8a06611291d70e86b382e1718ea080de6d62f9477738b1115be752c614` |
| S/statcast_2026-08-17_2026-08-21.csv | 19,417 | `3844f185f332d8ef2409bcfd1444c1dee8b8ea93122f9246607581c282233c72` |
| S/statcast_2026-08-22_2026-08-26.csv | 21,083 | `892d5ac3f17d42015f6ea8c4d0be1718e23492166657b17ec4538c829e257e32` |
| S/statcast_2026-08-27_2026-08-31.csv | 19,120 | `2280f1f4cf7f1e662c61e9fd2f4db19003bf3ca0e28690df481867364fa1f510` |
| S/statcast_2026-09-01_2026-09-05.csv | 20,968 | `248526f1c9caca2ef57964bf07813cb1f7c8fee77c702aa8bd3de52827ee6d33` |
| S/statcast_2026-09-06_2026-09-07.csv | 4,399 | `f28ed0c98892453e038cce929d97ee3b0f2c2655490d326fe42031af193ba31b` |
| T/statcast_2026-09-07_missing_games.csv | 3,239 | `a60a89b41821420ad50584efd65e384ab529cb7f97d27c4449b7ce47d7da3162` |

## 완료 경기와 중복 일정

일정의 완료 판정은 `gameType=R`, `abstractGameState=Final`, `codedGameState=F`, `detailedState in {Final, Completed Early}`를 모두 만족해야 한다. 연도와 2026-09-07 cutoff는 별도로 적용한다. `abstractGameState=Final`만으로는 연기된 경기를 완료 경기로 잘못 볼 수 있다.

보관된 2026 일정에서 구 필터와 이 기준을 직접 대조했다.

| 판정 | 일정 기록 | 고유 경기 |
| --- | ---: | ---: |
| 구 필터: abstract Final, Cancelled 제외 | 2,192 | 2,165 |
| 완료 상태를 함께 확인한 필터 | 2,166 | 2,165 |

경기 ID 집합 차이는 0이다. 새 기준의 실제 상태 조합은 `Final/F/Final/F` 2,164개 기록과 `Final/F/Completed Early/FR` 2개 기록이다. 구 필터 아래 중복 별칭 27개는 game_pk·year·venue·official_date·cutoff가 일치함을 확인했다. 새 필터는 미완료 별칭 26개를 제거하지만 같은 2,165경기를 남긴다. 따라서 구 필터가 동결된 준비 사본도 이 2026 자료에서는 경기 집합 차이를 만들지 않는다. 원자료의 모든 투구·타석이 완전하다는 증명과는 구분한다.

## 기존 정제본과 가중치

기존 v1 정제본에서 외부 검토용 v2 정제본으로 이어지는 출처가 남아 있다.

- v1: `columns/001-ball-count/data/processed/bcap_2026_v010_bcap_pitch__mlb_2026_ytd_20260907__20260909__r01.pkl`, 177,028,363바이트.
- v2: `columns/001-ball-count/data/processed/bcap_external_v2_2026_20260914__r01.pkl`, 188,535,746바이트.
- v2 준비 기록: `columns/001-ball-count/analysis/bcap_external_20260914__r01/preparation_2026/preparation.json`.
- v1·v2 정제본, 준비 코드, plan·plan_seal, 기존 PITCH/FF의 검사·fold·score 자료 13개는 저장된 참조 해시와 실제 파일이 모두 일치했다. v1 준비 감사 JSON도 원래 manifest의 출력 해시와 일치한다. 측정 검토 MD/JSON은 plan_seal의 해시와 일치한다.

2026 가중치는 **2025 값을 동결하여 사용**한 것이다. 새 R config의 적용 연도는 2026으로 쓰되, 기준 연도 2025와 다음 값을 출처에 명시한다. 2026 시즌에서 새로 추정한 가중치라고 설명하지 않는다.

| 결과 | BB | HBP | 1B | 2B | 3B | HR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2025 동결 값 | 0.691 | 0.722 | 0.882 | 1.252 | 1.584 | 2.037 |

`weights_source`에는 위 v2 준비 기록을 연결할 수 있다. 모델 명세의 개발연도 2024·2025 값을 그대로 두고 2026 실제 적용 가중치를 누락하면 안 된다.

알려진 카운트 예외는 `columns/001-ball-count/analysis/bcap_independent_review_20260909__r01/lineage/all_strict_count_exceptions.csv`에 기록돼 있다. 2026의 `824212|43|3`(S/`statcast_2026-03-30_2026-04-03.csv`, 원본 기록 9,584)은 그대로 유지하는 감사 대상이다. 현재 초기 R 준비 코드의 `known_count_exception`은 개발연도 2개만 표시하므로 이 감사 표시에는 차이가 있다. 이 플래그는 제외·Y·모델 특징이 아니며, 해당 행을 새로 제외하거나 카운트를 고쳐서는 안 된다. 새 R 준비본과 v2 정제본을 대조할 때 의도된 2026 기하 보류 차이와 이 감사 표시 차이를 분리한다.

## 가능한 분석과 보류 범위

**BCAI와 BCAP PITCH/FF**는 동일한 35개 원본으로 준비할 수 있다. BCAI에는 `game_pk, at_bat_number, pitch_number, game_year, game_date, balls, strikes, events`가 필요하다. 기존 `tools/export_bcai_r_input.py`를 통한 v2 정제본의 무필터 형식 변환도 가능하지만, 새 입력 provenance에 원 정제본과 원본 연결을 남겨야 한다. 이번 검토에서는 비교 대상이 되는 독립 2026 OBS 실행을 확인하지 않았으므로 Ridge 실행을 OBS reference로 사용하지 않는다.

BCAP PITCH/FF는 현재·이전 투구의 위치 좌표를 특징에 넣지 않는 기존 설계다. 기존 외부 계획에서도 두 모델은 COMPLETE였고, 같은 v2 정제본을 입력으로 사용했다. 그러나 이 사실이 구속이나 다른 측정값까지 모든 연도에 완전히 같다는 검증을 뜻하지는 않는다. BCAI와 BCAP 모두 관찰 자료에 기초한 지표로 설명하고, 2026 부분 시즌과 과거 전체 시즌의 차이를 함께 표시한다.

**2026 BCAP S/B와 SWING은 계속 보류**한다. 저장된 2026-09-14 측정 검토는 2025까지의 plate front plane과 2026 midplane, 수작업 존과 ABS 존 정의의 차이를 지적하며 검증된 변환이 없다고 기록한다. 이 문서는 해당 저장 자료와 봉인 해시를 확인한 것이며 외부 설명서를 오늘 다시 확인한 것은 아니다.

- S/B의 inside/outside 행동 정의 자체가 위치·존 정의에 의존한다.
- SWING의 물리량 구간, 상대 높이, 위치 셀과 5개 구역 보고도 같은 영향을 받는다.
- 단순 높이 정규화만으로 해소됐다고 보지 않으며, 심판 판정이나 위치를 뺀 대체 모형으로 자동 변경하지 않는다.
- R 준비본은 2026 S/B 행동·유효성을 보류하고, 실행기는 2026 S/B와 SWING 실행을 막아야 한다. 원 SWING 행동 라벨을 감사용으로 남기는 것과 모형 적합은 별개다.

## 새 실행을 위한 구체적 절차

1. 이 문서의 35개 CSV·일정·동결 가중치만 명시한 새 config를 만들고, 원본을 다시 수집하지 않는다. R 준비 코드의 실제 실행 사본을 먼저 동결하고 그 파일의 경로·해시를 감사 기록에 남긴다.
2. `models/bcap/r/prepare_raw.R`에 `input_csv`, `years:[2026]`, `seasons:[{year:2026,schedule:...,cutoff:"2026-09-07"}]`, 2026 행에 위 가중치를 담은 `weights`, `weights_source`, **새** `output_rds`·`audit_dir`를 전달한다. 기존 raw·정제본·감사 폴더를 덮어쓰지 않는다.
3. 준비 단계에서 키 중복·카운트 범위·타석 종료 사건·0-0 시작 여부, PA 안의 이전 투구 특징, 고유 경기 집합, 가중치와 출처 해시를 검사한다. 기존 정제본과 모델에 쓰는 특징·Y·행 선택을 대조하면 준비 코드의 독립 재현 확인에 도움이 된다.
4. BCAI는 새 2026 YTD 실행 ID로 수행한다. BCAP 실행은 `pitch,pitch_ff`를 명시하고 `2026_ytd_20260907` 범위를 남긴다. 2015~2023 전용 역사 드라이버에 2026을 억지로 넣지 않는다.
5. 기존 Python 수치의 정확 재현이 목표라면 원 fold와 보정 분할을 전달해야 한다. R의 새 난수 분할을 같은 seed의 NumPy 분할과 같다고 주장하지 않는다. 새 분할을 사용할 때는 실제 분할을 저장하고 새 계산으로 명시한다.
6. 기존 외부 계획의 동시비교 family와 새 R의 단순 연도별 표는 범위가 다르다. PITCH/FF 연도별 26개 표만 생성하면서 원 외부검토의 공통 지지집합 48개 비교를 재현했다고 쓰지 않는다. 사용할 family를 실행 전에 config/manifest에 명시한다.
7. 블로그용 표·그림에는 “2026-09-07까지”, “2025 동결 가중치”, “부분 시즌 보조 비교”를 표시한다. SB/SWING 빈칸은 0이 아니라 측정 정의 때문에 보류한 것으로 설명한다.

## 출처 파일의 실제 SHA-256

경로는 저장소 루트 `C:/Users/백창현/Desktop/Baseline` 기준이다. 아래 목록은 준비 검토 시 읽은 파일의 해시이며 새 실행의 manifest를 대신하지 않는다.

| 경로 | SHA-256 |
| --- | --- |
| `columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260909__r01/artifacts/preparation/preparation_audit.json` | `0aaf13062ac9e2e84827acbe55ffa650580113e7bf70fb61f934f8c307666549` |
| `columns/001-ball-count/analysis/bcap_external_20260914__r01/preparation_2026/preparation.json` | `2768a285a9e3259a23e00979d7bf33e18b17e1cc1320efb04480d2b8bb406148` |
| `columns/001-ball-count/analysis/bcap_external_20260914__r01/measurement_review.md` | `6a8cb0a1cd0826bed1dd69f1c196c9ac6f1734444ad5ed8ad65f466e99c3fc81` |
| `columns/001-ball-count/analysis/bcap_external_20260914__r01/measurement_review.json` | `852fc27894599afec76e85f345a296a6683f949ee7fd30c108449c0c0b3637f6` |
| `columns/001-ball-count/data/raw/mlb/2026/snapshot_20260908_ridge_v02/acquisition_audit.json` | `0e7bc560f27871522ce71225d7fe31cc348264c940b14a02990e1dbfc85706a6` |
| `columns/001-ball-count/data/raw/mlb/2026/supplement_20260909_ridge_v02/acquisition_audit.json` | `56664c3ed4a39aeb123b90df3dd60c6e195334c4b79e124d93761b611416e826` |
| `columns/001-ball-count/data/processed/bcap_2026_v010_bcap_pitch__mlb_2026_ytd_20260907__20260909__r01.pkl` | `6640fea427cdda6fd059df5bd38794f878cd6d935d55f01b0533ba0576f044f3` |
| `columns/001-ball-count/data/processed/bcap_external_v2_2026_20260914__r01.pkl` | `7f60388928032b3efa6995c2a4a0e42faa1891c6d7dc63ab54c015c0d896ac25` |
| `columns/001-ball-count/analysis/bcap_external_20260914__r01/prepare_external.py` | `d8c883e5327a82128b5d186207899368c7f927466eebb93f91a90bc8033b2340` |
| `columns/001-ball-count/analysis/bcap_external_20260914__r01/plan.json` | `116957ffe2bb3338c4610a48aa95fedaebfe4701e01be8d1cec1444327bbb4ad` |
| `columns/001-ball-count/analysis/bcap_external_20260914__r01/plan_seal.json` | `c367b76c1feab3beff3b26923cc719d9585dcf5ffcca4f1e00ad05633e0abcc0` |
| `columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260914__r01/artifacts/basic_checks.json` | `b400aa4c8948e478ce5489ac10fb13cc896ddf69676ad982b420c8e97d0b46c3` |
| `columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260914__r01/artifacts/fold_membership.csv` | `f90d443097c593726879ec6cdb05cc698ba96e7f48d76a37de8bb60f0b443234` |
| `columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260914__r01/artifacts/fold_records.json` | `fda9aec4c37fd4b26005fe4bc2eddbd3c6499254e858a8325c7a15f632f2ae69` |
| `columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260914__r01/artifacts/scores.pkl` | `aa137ab6381fabd973b6519e8e010c878d37e512f9726fb87ca06f4e0b78a0a2` |
| `columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2026_ytd_20260907__20260914__r01/artifacts/basic_checks.json` | `cfc019774700ee79fa70e8754cb42b4f6fc0af2fbd0dcc679eb41459e4969f5d` |
| `columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2026_ytd_20260907__20260914__r01/artifacts/fold_membership.csv` | `1497126d96061a575ea435b115b4d1dfaf58798f5c9c1c8e9d21f4573b4f9014` |
| `columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2026_ytd_20260907__20260914__r01/artifacts/fold_records.json` | `fda9aec4c37fd4b26005fe4bc2eddbd3c6499254e858a8325c7a15f632f2ae69` |
| `columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2026_ytd_20260907__20260914__r01/artifacts/scores.pkl` | `066f209da9178989617cf45f2ab5f22447a38b3601c8d927b384f9c95c52c582` |
| `columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260914__r01/manifest.json` | `d08d63e1784d2c88a18a080955fe6e42c9973e6efde3885cbe72f2137da80cfc` |
| `columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2026_ytd_20260907__20260914__r01/manifest.json` | `3801bf322ca72041fd5957cb72d863585a0e00ea267cb0941b60e5e5edb02b34` |
| `columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2026_ytd_20260907__20260914__r01/manifest.json` | `16f0b61a3e80eb321c95afb569fa2d38393c9d45e06af04717e4503663913295` |
| `columns/001-ball-count/analysis/runs/bcap_swing__mlb_2026_ytd_20260907__20260914__r01/manifest.json` | `8177554a06306d4a00535f2337d44903eee4c257bf3153936469ed4de2ec358a` |

