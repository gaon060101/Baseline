# Saved-output comparison only. Run from repository root; never fit or download.
suppressPackageStartupMessages({library(data.table);library(jsonlite);library(digest);library(ggplot2)})
args <- commandArgs(TRUE)
out <- if(length(args)) args[1] else 'columns/001-ball-count/analysis/history_comparison_20260928_r01'
dir.create(out,recursive=TRUE,showWarnings=FALSE)
for(d in c('tables','figures','audit')) dir.create(file.path(out,d),showWarnings=FALSE)
save <- function(x,n) fwrite(x,file.path(out,'tables',paste0(n,'.csv')),bom=TRUE,na='NA')
hash <- function(p) digest(file=p,algo='sha256',serialize=FALSE)
inputs <- list()
track <- function(p,role,expected=NA_character_) {
 stopifnot(file.exists(p)); actual<-hash(p)
 if(!is.na(expected)) stopifnot(tolower(expected)==actual)
 inputs[[length(inputs)+1L]] <<- data.table(path=gsub('\\\\','/',p),role=role,sha256=actual,expected_sha256=expected,bytes=file.info(p)$size)
}
J <- function(p) fromJSON(p,simplifyVector=FALSE)
base <- 'columns/001-ball-count'
an <- file.path(base,'analysis')
pub <- file.path(base,'publish/naver_20260918')
# Freeze the original claims BEFORE screening historical findings.
claims <- data.table(
 id=sprintf('C%02d',1:11),
 kind=c(rep('당시 명시한 주장',10),'당시 명시한 보조 분석 범위'),
 original=c('0-2 최저, 3-0 최고; 볼 증가·스트라이크 감소 방향으로 지수 증가','1-1은 시작점 미만, 풀카운트는 시작점 초과','0-1과 2-2, 1-0과 2-1의 지수가 가깝다','두 스트라이크에서 볼이 늘어난 상태 사이의 W 간격은 뒤쪽일수록 컸다','S/B에서 0-2·1-2는 존 밖, 0-1 불명확, 다른 9카운트는 존 안','2023 존 안 12개 점추정은 스윙 방향; 10개 구간도 같은 방향','2023 존 밖 지원 44칸 모두 테이크; 3-0 네 칸은 자료 부족','구종의 2023·2026 자체/공통 96개 비교 중 92개 불명확','개발 FB/NFB 3-0의 차이는 남지만 지원·보정 의존성이 있다','개발 FF/non-FF 3-2의 비포심 방향은 제한된 단서','Ridge 보정 뒤 BCAI 최대 이동 약 1.61포인트'),
 numerical_evidence=c('0-2 63.99; 3-0 175.40; 364124 PA','1-1 94.16; 3-2 119.73','0-1 85.06 / 2-2 85.10; 1-0 112.96 / 2-1 112.80','2024 +0.023798,+0.043248,+0.106880 W','개발 S-B +0.027827,+0.021374 W;219 보정;95,563/96,411 및138,265/139,503 투구','2023 CENTER 12/12 지원,12/12 양수,10/12 구간 양수','2023 44/48 지원,44/44 음수 구간','92/96 불명확; 2026은9월7일까지','개발 자체 +0.0682 W; 공통 +0.0672 W','개발 공통 +0.0170 [0.0014,0.0326] W; 64,863투구','0-2 63.99→64.95;3-0 175.40→173.79'),
 scope=c(rep('2024–2025 관찰 지수',3),'2024 서로 다른 도달 집단 평균 차이','2024–2025 공유 적합;2023 기존 확인도 있음','2023 Python 재적합;236 보정','2023 Python 재적합;겹치는 구역','2023·2026 Python;자체/공통표본;독립96실험 아님','2024–2025;분류별 및 공통 지원표본','2024–2025;255 보정;전체학습 변동 미포함','2024–2025 Ridge 탐색;OBS와 별도'),
 source=c(rep(file.path(pub,'02_bcai.md'),4),rep(file.path(pub,'03_bcap.md'),4),rep(file.path(an,'bcap_pitch_classification_20260912__r01/report.md'),2),file.path(pub,'02_bcai.md')),
 run_id=c(rep('bcai_obs__mlb_2024_2025__20260908__r01',3),'bcap_followup__mlb_2024_2025__20260917__r01','bcap_pitch_sb__mlb_2024_2025__20260912__r01','bcap_swing__mlb_2023__20260914__r01','bcap_swing__mlb_2023__20260914__r01','bcap_external_20260914__r01 (보고서 묶음)','bcap_pitch_compare__mlb_2024_2025__20260912__r01','bcap_pitch_compare__mlb_2024_2025__20260912__r01','원고 인용 [2] Ridge 실행 연결 참조'))
claims[1:3,run_id:='bcai_obs__mlb_2024_2025__20260907__r01']
claims[id=='C04',run_id:='bcai_state_delta__mlb_2024_2025__20260917__r01']
claims[id=='C11',run_id:='bcai_ridge__mlb_2024_2025__20260908__r02']
save(claims,'original_claim_ledger')
for(p in unique(c(claims$source,file.path(pub,'01_ball_count.md'),file.path(pub,'04_references_ko.md'),file.path(pub,'05_data_validation.md'),file.path(an,'count_advantage_2024_2025.md'),file.path(an,'bcap_external_20260914__r01/final_column_conclusion.md')))) track(p,'preserved baseline text')
a_path<-file.path(an,'r_history_20260928/summary.csv'); b_path<-file.path(an,'r_bcap_history_20260928/summary.csv')
track(a_path,'BCAI saved summary');track(b_path,'BCAP saved summary')
a<-fread(a_path); b<-fread(b_path)
stopifnot(nrow(a)==132,nrow(b)==2552,identical(sort(unique(a$year)),2015:2025),identical(sort(unique(b$game_year)),2015:2025))
manpaths<-unique(c(a$source_manifest,b$source_manifest))
mans<-setNames(lapply(manpaths,function(p){track(p,'completed manifest'); m<-J(p);stopifnot(m$status=='COMPLETE');m}),manpaths)
verified <- function(p,mp,role) {
 m<-mans[[mp]]; if(is.null(m)){m<-J(mp);stopifnot(m$status=='COMPLETE');track(mp,'completed manifest');mans[[mp]]<<-m}
 records<-m$outputs
 hit<-Filter(function(z) !is.null(z$path)&&basename(gsub('\\\\','/',z$path))==basename(p),records)
 stopifnot(length(hit)==1)
 track(p,role,hit[[1]]$sha256)
 fread(p)
}
for(mp in manpaths){
 p<-unique(c(a[source_manifest==mp,source_csv],b[source_manifest==mp,source_csv]));stopifnot(length(p)==1)
 src<-verified(p,mp,'source annual estimates')
 if(mp %in% a$source_manifest){
  x<-a[source_manifest==mp];cols<-names(src);setorderv(x,c('year','count'));setorderv(src,c('year','count'))
 }else{ x<-b[source_manifest==mp];cols<-names(src);setorderv(x,c('game_year','level','count','region','pitch_group'));setorderv(src,c('game_year','level','count','region','pitch_group')) }
 stopifnot(isTRUE(all.equal(as.data.frame(x[,..cols]),as.data.frame(src),check.attributes=FALSE,tolerance=1e-12)))
}
base_bcai_dir<-file.path(an,'runs/bcai_r_check__mlb_2024_2025__20260928__r02')
ai0<-verified(file.path(base_bcai_dir,'artifacts/combined_indices.csv'),file.path(base_bcai_dir,'manifest.json'),'original two-year BCAI reproduced')
baseline<-rbindlist(lapply(unique(b$model),function(mod){
 mp<-unique(b[model==mod&game_year==2024,source_manifest]); p<-file.path(dirname(mp),'artifacts/action_values.csv')
 z<-verified(p,mp,'shared two-year BCAP estimates'); z[,model:=mod];z[,source_csv:=p];z[,run_id:=mans[[mp]]$run_id];z
}),fill=TRUE)
save(baseline,'baseline_bcap_shared_fit');save(ai0,'baseline_bcai_combined')
count_order<-c('0-0','0-1','0-2','1-0','1-1','1-2','2-0','2-1','2-2','3-0','3-1','3-2')
a[,`:=`(balls=as.integer(substr(count,1,1)),strikes=as.integer(substr(count,3,3)),window=ifelse(year<2024,'추가2015–2023','기준2024–2025'))]
a[,annual_rank:=frank(-index,ties.method='min'),by=year]
save(a,'bcai_all_132')
profile<-a[,.(index_min=min(index),min_year=year[which.min(index)],index_max=max(index),max_year=year[which.max(index)],index_median=median(index),rank_min=min(annual_rank),rank_max=max(annual_rank),W_min=min(value),W_max=max(value),N_min=min(N),N_max=max(N)),by=count]
profile<-merge(profile,ai0[,.(count,baseline_index=index,baseline_N=N_PA)],by='count')
profile<-merge(profile,a[year<2024,.(added_min=min(index),added_max=max(index),added_N=sum(N)),by=count],by='count')
profile<-profile[match(count_order,count)];save(profile,'bcai_count_profile')
yearshape<-a[,.(min_count=count[which.min(index)],max_count=count[which.max(index)],order=paste(count[order(-index)],collapse=' > '),eligible_PA=unique(eligible_PA),games=unique(games),start_W=value[count=='0-0'],gap_01_22=index[count=='2-2']-index[count=='0-1'],gap_10_21=index[count=='2-1']-index[count=='1-0'],state_02_12=value[count=='1-2']-value[count=='0-2'],state_12_22=value[count=='2-2']-value[count=='1-2'],state_22_32=value[count=='3-2']-value[count=='2-2'],balls_monotone=all(vapply(split(.SD,strikes),function(z)all(diff(z[order(balls),index])>0),logical(1))),strikes_monotone=all(vapply(split(.SD,balls),function(z)all(diff(z[order(strikes),index])<0),logical(1)))),by=year]
save(yearshape,'bcai_year_shape')
# Save all finite supported estimates; unsupported cells remain NA, never zero.
b[,status:=fifelse(!support_gate,'자료 부족',fifelse(family95_low>0,'양수·구간도 양수',fifelse(family95_high<0,'음수·구간도 음수',fifelse(delta>0,'양수·구간 불명확',fifelse(delta<0,'음수·구간 불명확','0·구간 불명확')))))]
save(b[support_gate==FALSE],'unsupported_source_audit_not_for_interpretation')
# Saved audit tables may retain numeric estimates below the reporting gate.
# Explicitly withhold these in all derived reader-facing outputs.
b[support_gate==FALSE,c('Q0','Q1','gcomp0','gcomp1','delta','SE','nominal95_low','nominal95_high','family95_low','family95_high'):=NA_real_]
save(b,'bcap_all_2552_screened')
summarize<-function(z) z[,.(years_total=.N,years_supported=sum(support_gate),positive=sum(support_gate&delta>0,na.rm=TRUE),negative=sum(support_gate&delta<0,na.rm=TRUE),clear_positive=sum(support_gate&family95_low>0,na.rm=TRUE),clear_negative=sum(support_gate&family95_high<0,na.rm=TRUE),unclear=sum(support_gate&family95_low<=0&family95_high>=0,na.rm=TRUE),unsupported=sum(!support_gate),delta_min=if(any(support_gate))min(delta,na.rm=TRUE) else NA_real_,delta_max=if(any(support_gate))max(delta,na.rm=TRUE) else NA_real_,coverage_min=min(coverage),coverage_max=max(coverage),n_min=min(n),n_max=max(n)),by=.(model,level,count,region,pitch_group)]
groups<-list(added_2015_2023=2015:2023,added_no2020=setdiff(2015:2023,2020),added_2017_2023=2017:2023,added_2017_2023_no2020=setdiff(2017:2023,2020),all_2015_2025=2015:2025,all_no2020=setdiff(2015:2025,2020),all_2017_2025=2017:2025,all_2017_2025_no2020=setdiff(2017:2025,2020),baseline_2024_2025=2024:2025)
counts<-rbindlist(lapply(names(groups),function(g){z<-summarize(b[game_year%in%groups[[g]]]);z[,window:=g];z[,years_used:=paste(groups[[g]],collapse=',')];z}))
save(counts,'bcap_pattern_counts_all_groups')
coverage<-b[level=='overall',.(model,game_year,n_all,n,coverage,PA,games,rows0,rows1,ESS0,ESS1,action1_rate_all,delta,family95_low,family95_high,support_gate,comparison_family,fit_scope)]
save(coverage,'bcap_overall_coverage')
byyear<-b[,.(cells=.N,supported=sum(support_gate),positive=sum(support_gate&delta>0,na.rm=TRUE),negative=sum(support_gate&delta<0,na.rm=TRUE),clear_positive=sum(support_gate&family95_low>0,na.rm=TRUE),clear_negative=sum(support_gate&family95_high<0,na.rm=TRUE),unclear=sum(support_gate&family95_low<=0&family95_high>=0,na.rm=TRUE)),by=.(model,game_year,level,region,pitch_group)]
save(byyear,'bcap_year_group_screen')
save(b[support_gate==FALSE],'bcap_unsupported_cells')
save(b[model=='swing'&level=='region_pitch'&support_gate],'swing_fine_groups_supported')
# Descriptive annual-index averages only, with explicit equal-year and PA weights.
wts<-rbindlist(lapply(names(groups),function(g){z<-a[year%in%groups[[g]]&count=='0-0',.(year,eligible_PA)];z[,`:=`(window=g,equal_year_weight=1/.N,start_PA_weight=eligible_PA/sum(eligible_PA))];z}))
save(wts,'annual_summary_weights')
aisens<-rbindlist(lapply(names(groups),function(g){z<-merge(a[year%in%groups[[g]]],wts[window==g,.(year,equal_year_weight,start_PA_weight)],by='year');z[,.(years=.N,index_min=min(index),index_max=max(index),annual_index_median=median(index),equal_year_mean_of_indices=sum(index*equal_year_weight),start_PA_weighted_mean_of_indices=sum(index*start_PA_weight)),by=count][,window:=g]}))
save(aisens,'bcai_descriptive_sensitivity')
events<-rbindlist(lapply(unique(a$source_manifest),function(mp){p<-file.path(dirname(mp),'artifacts/event_rates.csv');z<-verified(p,mp,'BCAI event rates');z[,source_csv:=p];z[,period:=paste(unique(a[source_manifest==mp,year]),collapse='+')];z}),fill=TRUE)
save(events,'bcai_event_rates')
weights<-fread(file.path(an,'r_history_20260928/weights.csv'));track(file.path(an,'r_history_20260928/weights.csv'),'season event weights');save(weights,'season_event_weights')
writeLines(capture.output(sessionInfo()),file.path(out,'audit/sessionInfo.txt'))
fwrite(unique(rbindlist(inputs)),file.path(out,'audit/source_hashes.csv'),bom=TRUE)
cat('BCAI PROFILE\n');print(profile,digits=5)
cat('BCAI YEAR SHAPE\n');print(yearshape,digits=5)
cat('BCAP LEVELS\n');print(unique(b[,.(model,level,region,pitch_group)]))
cat('ADDED COUNT SCREEN\n');print(counts[window=='added_2015_2023'&level=='count',.(model,count,years_supported,positive,negative,clear_positive,clear_negative,unclear,unsupported,delta_min,delta_max)],nrows=60)
cat('SWING REGIONS\n');print(byyear[model=='swing'&level=='region'],nrows=60)
cat('SUPPORT DETAILS\n');print(b[level=='count'&!support_gate,.(model,game_year,count,n_all,n,rows0,rows1,ESS0,ESS1,games0,games1,coverage)])
