suppressPackageStartupMessages({library(data.table);library(jsonlite);library(ggplot2);library(digest)})
setDTthreads(2)
base<-"columns/001-ball-count/analysis/r_supplement_20260928"
fig<-"columns/001-ball-count/figures/r_supplement_20260928"
runs<-c(bcai="bcai_supplement__mlb_2026_ytd_20260907__20260928__r01",
  pitch="bcap_pitch_r_supplement__mlb_2026_ytd_20260907__20260928__r01",
  pitch_ff="bcap_pitch_ff_r_supplement__mlb_2026_ytd_20260907__20260928__r01")
paths<-file.path("columns/001-ball-count/analysis/runs",runs)
manifests<-lapply(paths,function(p)fromJSON(file.path(p,"manifest.json"),simplifyVector=FALSE));names(manifests)<-names(runs)
if(!all(vapply(manifests,function(m)identical(m$status,"COMPLETE"),logical(1))))stop("Three completed supplement runs required")
if(file.exists(file.path(base,"report.md"))||dir.exists(fig))stop("Supplement report exists; use an explicit new edition")
dir.create(fig,recursive=TRUE)
sha<-function(p)digest(file=p,algo="sha256",serialize=FALSE)
meta<-function(p)list(path=p,sha256=sha(p),bytes=unname(file.info(p)$size))
checks<-list();ck<-function(name,ok,detail=NULL){checks[[length(checks)+1L]]<<-list(check=name,status=if(isTRUE(ok))"PASS" else "FAIL",detail=detail);if(!isTRUE(ok))stop(name)}
for(nm in names(runs)){
  m<-manifests[[nm]]
  ck(paste0(nm,"_output_hashes"),all(vapply(m$outputs,function(x)file.exists(x$path)&&identical(sha(x$path),x$sha256),logical(1))))
  val<-fromJSON(file.path(paths[match(nm,names(runs))],"artifacts",if(nm=="bcai")"validation.json"else"checks.json"),simplifyVector=FALSE)
  ck(paste0(nm,"_runtime_checks"),identical(val$status,"PASS"))
  if(nm!="bcai"){
    ck(paste0(nm,"_prepared_RDS_hash"),identical(sha(m$input$path),m$input$sha256))
    ck(paste0(nm,"_frozen_engine"),identical(sha(file.path(paths[match(nm,names(runs))],"artifacts/frozen_engine.R")),m$code[[1]]$sha256))
    ck(paste0(nm,"_frozen_runner"),identical(sha(file.path(paths[match(nm,names(runs))],"artifacts/frozen_run.R")),m$code[[2]]$sha256))
    ck(paste0(nm,"_family_and_seed"),m$configuration$comparison_family==255&&m$run_config$seed==20260928+2026)
  }
}
prepdir<-"columns/001-ball-count/data/processed/r_bcap_supplement_20260928/2026"
preppath<-file.path(prepdir,"audit/preparation_audit.json");prep<-fromJSON(preppath,simplifyVector=FALSE)
actualprep<-file.path(base,"bcap_preparation_snapshot/prepare_raw.R")
ck("executed_preparation_script_matches_recorded_and_frozen",identical(sha(actualprep),prep$code$sha256)&&identical(sha(actualprep),sha(prep$frozen_code$path)))
prov<-fromJSON("columns/001-ball-count/data/processed/r_bcai_supplement_20260928/2026/pitches.provenance.json",simplifyVector=FALSE)
ck("exact_35_archived_raw_sources_unchanged",length(prov$inputs)==35&&all(vapply(prov$inputs,function(x)identical(sha(x$path),x$sha256),logical(1))))
ck("transport_output_hash",identical(sha(prov$output$path),prov$output$sha256))
weight<-fromJSON(file.path(base,"weights.json"),simplifyVector=FALSE)
oldplan<-fromJSON(weight$source$path,simplifyVector=FALSE)
ck("2025_weights_frozen",identical(weight$frozen_weight_year,2025L)||weight$frozen_weight_year==2025)
ck("weight_values_equal_original2025",all(vapply(names(oldplan$weights[["2025"]]),function(k)weight$weights[[1]][[k]]==oldplan$weights[["2025"]][[k]],logical(1))))
schedule<-fromJSON("columns/001-ball-count/data/raw/mlb/2026/snapshot_20260908_ridge_v02/schedule_2026.json",simplifyVector=FALSE)
games<-unlist(lapply(schedule$dates,function(x)x$games),recursive=FALSE)
oldgames<-Filter(function(g)identical(g$gameType,"R")&&identical(g$status$abstractGameState,"Final")&&!identical(g$status$detailedState,"Cancelled")&&g$officialDate<="2026-09-07"&&substr(g$officialDate,1,4)=="2026",games)
strict<-Filter(function(g)identical(g$status$codedGameState,"F")&&g$status$detailedState%in%c("Final","Completed Early"),oldgames)
oldids<-vapply(oldgames,function(g)as.numeric(g$gamePk),numeric(1));newids<-vapply(strict,function(g)as.numeric(g$gamePk),numeric(1))
ck("strict_completed_game_set_unchanged",setequal(oldids,newids)&&length(unique(newids))==2165,
  list(old_records=length(oldids),strict_records=length(newids),unique_games=length(unique(newids)),removed_alias_records=length(oldids)-length(newids)))
prepared<-as.data.table(readRDS(file.path(prepdir,"prepared.rds")))
ck("raw_PA_sample_matches_archived_audit",nrow(prepared)==639042&&uniqueN(prepared[,.(game_pk,at_bat_number)])==164281&&sum(!duplicated(prepared[eligible_pa==TRUE,.(game_pk,at_bat_number)]))==163327)
ck("2026_geometry_explicitly_withheld",all(!prepared$geometry_comparable)&&!any(prepared$eligible_pitch_sb)&&all(is.na(prepared$A_pitch_sb)))
ck("BCAI_BCAP_eligible_PA_agree",manifests$bcai$sample$eligible_PA==prep$eligible_PA)
flag<-prepared[game_pk==824212 & at_bat_number==43 & pitch_number==3,.(game_pk,at_bat_number,pitch_number,known_count_exception,Y,eligible_pitch)]
ck("known2026exception_retained",nrow(flag)==1&&is.finite(flag$Y)&&flag$eligible_pitch)
fwrite(flag,file.path(base,"known_exception_retained.csv"));rm(prepared);gc(FALSE)
bcai<-fread(file.path(paths[1],"artifacts/season_indices.csv"));ct<-as.vector(t(outer(0:3,0:2,paste,sep="-")))
bcai[,count:=factor(count,levels=rev(ct))]
theme<-theme_minimal(base_family="Malgun Gothic",base_size=14)+theme(plot.caption=element_text(hjust=0,size=9),legend.position="bottom")
caption<-"출처: 보존된 MLB Statcast 35개 CSV · 2,165경기 · 유효 타석 163,327개\n2025년 공격가치 가중치 고정 · 2026 전체 시즌 결과 아님 · 인과 효과·행동 추천 아님"
p<-ggplot(bcai,aes(index,count))+geom_vline(xintercept=100,linetype=2,color="grey50")+
  geom_errorbar(aes(xmin=simultaneous95_low,xmax=simultaneous95_high),orientation="y",width=.2,color="#6B8BB5")+geom_point(size=2.7,color="#235C98")+
  labs(title="2026년 9월 7일까지, 카운트별 공격가치",subtitle="BCAI · 0-0 = 100 · 경기 단위 재표본 2,000회 · 시즌 내 11개 카운트 근사 동시 95% 구간",x="BCAI 지수",y="투구 전 카운트",caption=caption)+theme
ggsave(file.path(fig,"bcai_2026_ytd.png"),p,width=11,height=8,dpi=180,bg="white")
allbcap<-list()
for(nm in c("pitch","pitch_ff")){
  d<-fread(file.path(paths[match(nm,names(runs))],"artifacts/action_values.csv"),encoding="UTF-8")[level=="count"]
  d[,count:=factor(count,levels=rev(ct))];d[,module:=nm];allbcap[[nm]]<-d
  title<-if(nm=="pitch")"패스트볼 계열 − 나머지 구종" else "포심 − 비포심"
  p<-ggplot(d,aes(delta,count))+geom_vline(xintercept=0,linetype=2,color="grey50")+
    geom_errorbar(aes(xmin=family95_low,xmax=family95_high),orientation="y",width=.2,color="#3E8793")+
    geom_point(aes(shape=ifelse(support_gate,"지원 표본 충족","비교 자료 부족")),size=2.7,color="#225C67")+
    labs(title=paste0("2026년 9월 7일까지: ",title),subtitle="BCAP · 음수는 앞 구종의 허용 공격가치가 낮은 점추정 · 경기 군집 조건부 255가족 보정 구간",
      x="최종 타석 공격가치 차이 (W)",y="투구 전 카운트",shape=NULL,caption=caption)+theme
  ggsave(file.path(fig,paste0("bcap_",nm,"_2026_ytd.png")),p,width=12,height=8,dpi=180,bg="white")
}
fwrite(bcai,file.path(base,"bcai_summary.csv"),bom=TRUE);fwrite(rbindlist(allbcap),file.path(base,"bcap_summary.csv"),bom=TRUE)
held<-list(status="WITHHELD_MEASUREMENT",models=c("BCAP-PITCH-SB-v0.1.0","BCAP-SWING-v0.2.0"),
 reason="2026 좌표 기준·존 정의 변경으로 이전 연도와 측정 비교 가능성 보류. 수치 적합·행동 추천 없음.",source=meta("columns/001-ball-count/analysis/bcap_external_20260914__r01/plan.json"))
write_json(held,file.path(base,"withheld_measurement.json"),pretty=TRUE,auto_unbox=TRUE)
notes<-c("# 2026 보조 R 분석 — 9월 7일까지",
  "","**BCAI와 BCAP 구종 두 모듈의 R 계산 완료. 전체 시즌 결과가 아닌 보조 자료다.**",
  "","2026년 3월 25일~9월 7일의 보존된 원 CSV 35개를 사용했다. 신규 수집 없이 639,042개 투구 행, 2,165경기, 유효 타석 163,327개를 확인했다. 2026 고유 가중치를 새로 추정하지 않고 기존 계획의 2025 가중치(BB .691, HBP .722, 1B .882, 2B 1.252, 3B 1.584, HR 2.037)를 고정했다.",
  "","## 계산 범위",
  "","- BCAI-OBS: R 집계와 경기 단위 bootstrap 2,000회. 0-0=100이며 시즌 내 11개 카운트의 근사 동시 구간을 제공한다. 다른 시즌과 공식 차이 검정은 수행하지 않았다.",
  "- BCAP-PITCH·PITCH-FF: 2026 안에서 경기 3분할 OOF 재적합. 기존 개발 규제값 고정, seed=20262954, 가족=255. R 분할은 원 NumPy 분할과 같다고 주장하지 않는다.",
  "- BCAP S/B·SWING: WITHHELD_MEASUREMENT. 2026 위치·존 정의의 비교 가능성 문제를 해결하기 전까지 계산하지 않았다.",
  "","## 해석과 한계",
  "","카운트별 도달 타석과 구종별 공통 지원 표본이 다르므로 지수나 공격가치 차이를 인과 효과·실전 행동 추천·타석 전체 정책 개선량으로 읽지 않는다. BCAP 구간은 고정 OOF 점수의 경기 군집 조건부 구간이며 보조 모형 전체 학습 변동과 경기 간 선수 의존성을 포함하지 않는다. 과거에 이미 노출된 2026 자료의 재계산이며 새 미노출 외부 검증으로 부르지 않는다.",
  "","## 검산 기록",
  "","세 완료 실행의 결과·동결 코드·전처리 입력 해시와 원 35개 파일 보존을 확인했다. 새 완료경기 기준은 일정 기록 수를 2,192→2,166으로 줄이지만 고유 경기 집합은 2,165개로 정확히 같다. 기존 준비 결과의 표본에는 영향이 없다.",
  "","2026은 새 R 경기 분할로 적합했으며 원 Python 행별 점수 재현을 검사한 작업이 아니다. 동결 실행기의 checks.json에 남은 공통 scope 문구보다 실제 검사 목록과 본 보고서를 이번 검증 범위의 기준으로 사용한다. 원 점수 재현은 앞선 2024·2025 실행에서 별도로 확인했다.",
  "","알려진 카운트 예외 824212/43/3 행은 제외하지 않고 원래 Y와 함께 유지했다. 준비 사본의 known_count_exception 플래그가 이 2026 사례를 표시하지 않는 감사상 차이가 있으나 이 플래그는 모델 입력·제외 기준이 아니므로 계산값에는 영향을 주지 않는다. 후속 원자료 감사에서 별도 표를 참고한다.",
  "","- 상세 검산: [postflight.json](postflight.json)",
  "- 측정 보류: [withheld_measurement.json](withheld_measurement.json)",
  "- [BCAI 표](bcai_summary.csv) · [BCAP 표](bcap_summary.csv)",
  "","## 블로그용 그림",
  "",paste0("![2026 BCAI](../../figures/r_supplement_20260928/bcai_2026_ytd.png)"),
  "",paste0("![2026 패스트볼](../../figures/r_supplement_20260928/bcap_pitch_2026_ytd.png)"),
  "",paste0("![2026 포심](../../figures/r_supplement_20260928/bcap_pitch_ff_2026_ytd.png)"))
writeLines(notes,file.path(base,"report.md"),useBytes=TRUE)
html<-paste0('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>2026 보조 R 분석</title><style>body{max-width:1100px;margin:auto;padding:28px;font:17px/1.7 "Malgun Gothic",sans-serif;color:#203048}img{width:100%;height:auto}h1{line-height:1.35}a{color:#246099}.note{background:#f1f5f9;padding:18px;border-radius:12px}</style><h1>2026 보조 R 분석<br>9월 7일까지</h1><p class="note">BCAI와 BCAP 구종 두 모듈 계산 완료. 2025 가중치 고정 · 전체 시즌 결과가 아닌 보조 자료입니다. S/B와 스윙은 측정 비교 문제로 보류했습니다.</p><p>원본 35개 CSV · 639,042개 투구 행 · 2,165경기 · 유효 타석 163,327개. 신규 자료 수집은 하지 않았습니다.</p><p><a href="report.md">방법·한계·검산 보고서</a> · <a href="postflight.json">검산 기록</a> · <a href="bcai_summary.csv">BCAI 표</a> · <a href="bcap_summary.csv">BCAP 표</a></p>',
  paste0('<img alt="2026 보조 결과" src="../../figures/r_supplement_20260928/',c("bcai_2026_ytd.png","bcap_pitch_2026_ytd.png","bcap_pitch_ff_2026_ytd.png"),'">',collapse=""),
  '<p>관찰상 비교이며 인과 효과나 행동 추천이 아닙니다. BCAP 구간에는 전체 학습 변동·경기 간 선수 의존성이 포함되지 않습니다. 기존에 노출된 2026 자료의 재계산입니다.</p></html>')
writeLines(html,file.path(base,"report.html"),useBytes=TRUE)
write_json(list(status="PASS",checks=checks,runs=lapply(paths,function(p)meta(file.path(p,"manifest.json"))),
 actual_preparation_script=meta(actualprep),preparation=meta(preppath),source_plan=meta(weight$source$path),
 intentional_geometry_holds=held,known_count_exception_audit_difference="824212|43|3 retained; audit flag false in frozen preparer; not used in fitting/exclusion",
 reference_score_reproduction="NOT_RUN for 2026: frozen checks.json generic scope label is too broad; actual checks are structural/numerical only",
 outputs=lapply(c(file.path(base,c("report.md","report.html","bcai_summary.csv","bcap_summary.csv","known_exception_retained.csv","withheld_measurement.json")),list.files(fig,full.names=TRUE)),meta)),
 file.path(base,"postflight.json"),pretty=TRUE,auto_unbox=TRUE,na="null",digits=16)
cat("PASS 2026 supplement postflight:",length(checks),"checks; report and 3 PNGs saved\n")
