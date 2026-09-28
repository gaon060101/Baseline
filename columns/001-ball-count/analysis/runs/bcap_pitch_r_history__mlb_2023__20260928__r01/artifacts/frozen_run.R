script_argument<-grep("^--file=",commandArgs(trailingOnly=FALSE),value=TRUE)
entry_script<-if(length(script_argument))sub("^--file=","",script_argument[1]) else "models/bcap/r/run.R"
entry_dir<-dirname(normalizePath(entry_script,mustWork=TRUE))
engine_path<-if(file.exists(file.path(entry_dir,"frozen_engine.R")))file.path(entry_dir,"frozen_engine.R") else
  if(file.exists(file.path(entry_dir,"engine.R")))file.path(entry_dir,"engine.R") else "models/bcap/r/engine.R"
source(engine_path,encoding="UTF-8")
args<-commandArgs(trailingOnly=TRUE);if(length(args)!=1)stop("Usage: run.R config.json")
cfg<-jsonlite::fromJSON(args[1],simplifyVector=TRUE)
run<-cfg$output_dir;if(dir.exists(run))stop("Existing run is immutable; choose a new output_dir")
dir.create(file.path(run,"artifacts"),recursive=TRUE);art<-file.path(run,"artifacts")
model<-cfg$model;version<-if(model%in%c("pitch_sb","pitch_ff"))"0.1.0" else "0.2.0"
specpath<-file.path("models/bcap",model,paste0("v",version),"specification.yaml")
c<-jsonlite::fromJSON(specpath,simplifyVector=TRUE)
alphas<-if(model=="pitch_sb")list(p=1000,m0=1000,m1=1000) else c$fixed_alpha
if(!is.null(cfg$comparison_family))c$comparison_family<-cfg$comparison_family
manifest<-list(run_id=basename(run),model_id=c$model_id,version=c$version,implementation="R centered ridge/Platt/OOF AIPW",
  status="RUNNING",model_status="EXPERIMENTAL",started_at_utc=bc_now(),configuration=c,run_config=cfg,
  selected_alpha=alphas,definition=bc_meta(specpath),code=lapply(c(engine_path,entry_script),bc_meta),
  interpretation="관찰상 보정 비교; 인과 효과·행동 추천 아님. 구간은 고정 점수의 경기 군집 조건부 구간.",
  limitations=c("보조 모형 전체 학습 불확실성 미포함","경기 간 선수 의존성 미포함","완료 타석 및 지원 표본 선택",
    "연도별 표는 탐색용이며 연도 차이는 같은 개발 적합의 하위집단 비교","기존 SB 선택 alpha만 재사용; 튜닝 재실행 아님"),
  environment=list(R=R.version.string,Matrix=as.character(packageVersion("Matrix")),data_table=as.character(packageVersion("data.table"))))
bc_json(manifest,file.path(run,"manifest.json"));checks<-list()
check<-function(name,ok,detail=NULL){checks[[length(checks)+1L]]<<-list(check=name,status=if(isTRUE(ok))"PASS" else "FAIL",detail=detail);if(!isTRUE(ok))stop(name)}
tryCatch({
  file.copy(c(engine_path,entry_script,specpath,args[1]),
            file.path(art,c("frozen_engine.R","frozen_run.R","frozen_specification.yaml","frozen_run_config.json")))
  if(!is.null(cfg$input_rds)) {
    prepared<-readRDS(cfg$input_rds);preparation_path<-attr(prepared,"preparation_manifest")
    d<-as.data.table(prepared);rm(prepared);manifest$input<-bc_meta(cfg$input_rds)
    if(!is.null(preparation_path)) {
      check("preparation_manifest_exists",file.exists(preparation_path))
      manifest$input_preparation<-bc_meta(preparation_path)
      preparation<-jsonlite::fromJSON(preparation_path,simplifyVector=FALSE)
      check("prepared_RDS_hash",any(vapply(preparation$outputs,function(x)identical(x$sha256,manifest$input$sha256),logical(1))))
      manifest$preparation_details<-preparation
    }
  } else {
    path<-file.path(cfg$input_dir,"rows.csv");d<-fread(path,colClasses="character",na.strings="__BCAP_NA__",encoding="UTF-8")
    manifest$input<-bc_meta(path);prov<-file.path(cfg$input_dir,"provenance.json")
    if(file.exists(prov)) {
      manifest$transport_provenance<-bc_meta(prov);transport<-jsonlite::fromJSON(prov,simplifyVector=FALSE)
      check("transport_rows_hash",identical(manifest$input$sha256,transport$outputs[["rows.csv"]]$sha256))
    }
  }
  for(f in intersect(c("row_id","game_pk","at_bat_number","pitch_number","game_year","Y","plate_x","plate_z","sz_top","sz_bot","release_speed","pfx_x","pfx_z","A_pitch","A_pitch_sb","A_swing"),names(d)))set(d,j=f,value=as.numeric(d[[f]]))
  for(f in intersect(c("eligible_pitch","eligible_pitch_sb","eligible_swing","known_count_exception"),names(d))) set(d,j=f,value=tolower(as.character(d[[f]]))%in%c("true","1"))
  eligibility<-if(model=="pitch_ff")"eligible_pitch" else paste0("eligible_",model)
  check("required_eligibility",eligibility%in%names(d))
  selected<-which(d[[eligibility]]);d<-d[selected]
  if(model=="pitch_ff")d[,A:=as.integer(pitch_type=="FF")] else d[,A:=get(paste0("A_",model))]
  bc_features(d,c)
  check("unique_complete_pitch_keys",!anyNA(d[,.(row_id,game_pk,at_bat_number,pitch_number)])&&uniqueN(d$row_id)==nrow(d)&&uniqueN(d[,.(game_pk,at_bat_number,pitch_number)])==nrow(d))
  check("valid_actions_outcomes",all(d$A%in%0:1)&&all(is.finite(d$Y)))
  check("valid_counts",all(d$count%in%as.vector(outer(0:3,0:2,paste,sep="-"))))
  check("requested_years",setequal(sort(unique(d$game_year)),cfg$years))
  check("all_model_features",all(c$features%in%names(d)))
  if(any(d$game_year>=2026)&&model%in%c("pitch_sb","swing"))stop("2026 geometry measurement hold: no SB/SWING application without reviewed definition")
  forbidden<-c("description","events","Y","result","final_event","A","pitch_type","prev_pitch_type")
  if(model!="swing")forbidden<-c(forbidden,"plate_x","plate_z","zone","release_speed","pfx_x","pfx_z","sz_top","sz_bot")
  if(model%in%c("pitch","pitch_ff"))forbidden<-c(forbidden,"pitch_group")
  check("no_forbidden_predictors",!any(c$features%in%forbidden))
  check("coarse_lag_only",all(d$prev_pitch_group%in%c("FB","NFB","START","MISSING_PREVIOUS","UNCLASSIFIED")))
  regcheck<-bc_regions(d)
  check("known_stand_for_side_reports",all(d$stand%in%c("R","L")))
  check("overlapping_regions_max_two",max(Reduce(`+`,regcheck))<=2)
  sbcheck<-d$A_pitch_sb;sbcheck[is.na(sbcheck)]<-0
  geometry_comparable<-d$game_year<=2025
  if(any(geometry_comparable))check("center_equals_geometric_SB",identical(unname(regcheck$CENTER[geometry_comparable]),unname(sbcheck[geometry_comparable]==1)))
  rm(regcheck,sbcheck)
  # Replay original game maps for reproduction. Fresh years use explicitly
  # recorded R RNG assignments and never claim NumPy seed equivalence.
  fp<-if(!is.null(cfg$input_dir))file.path(cfg$input_dir,paste0(model,"_folds.csv")) else ""
  cp<-if(!is.null(cfg$input_dir))file.path(cfg$input_dir,paste0(model,"_calibration_games.csv")) else ""
  if(nzchar(fp)&&file.exists(fp)&&file.exists(cp)) {
    fm<-fread(fp);calmap<-fread(cp);manifest$split_method<-"Original Python game fold/calibration map replay; no new randomization"
    manifest$split_inputs<-list(bc_meta(fp),bc_meta(cp))
    if(exists("transport"))for(path in c(fp,cp))check(paste0("transport_hash_",basename(path)),identical(bc_sha(path),transport$outputs[[basename(path)]]$sha256))
  } else {
    seed<-if(is.null(cfg$seed))c$seed else cfg$seed;set.seed(seed)
    games<-sort(unique(d$game_pk));shuffle<-sample(games);fm<-data.table(game_pk=shuffle,fold=(seq_along(shuffle)-1L)%%3L)
    calmap<-rbindlist(lapply(0:2,function(k){set.seed(seed+2000+k);tr<-sort(fm$game_pk[fm$fold!=k]);sh<-sample(tr);data.table(outer_fold=k,game_pk=sh[(seq_along(sh)-1L)%%5L==0L])}))
    manifest$split_method<-paste("R",RNGkind()[1],"seed",seed,"game shuffle round-robin; not NumPy equivalent")
  }
  d[,fold:=fm$fold[match(game_pk,fm$game_pk)]];check("complete_one_game_one_fold",!anyNA(d$fold)&&uniqueN(fm$game_pk)==nrow(fm)&&setequal(unique(d$fold),0:2))
  fwrite(d[,.(row_id,game_pk,at_bat_number,pitch_number,game_year,A,fold)],file.path(art,"fold_membership.csv"))
  fwrite(fm,file.path(art,"game_folds.csv"));fwrite(calmap,file.path(art,"calibration_games.csv"))
  logs<-new.env();logs$fits<-list();parts<-list();records<-list()
  for(k in 0:2) {
    label<-paste0("fold",k);train<-d[fold!=k];test<-d[fold==k];calgames<-calmap[outer_fold==k,game_pk]
    check(paste0(label,"_no_game_leakage"),!any(test$game_pk%in%train$game_pk)&&all(calgames%in%train$game_pk)&&!any(calgames%in%test$game_pk))
    records[[length(records)+1L]]<-list(fit_id=label,training_games=sort(unique(train$game_pk)),evaluation_games=sort(unique(test$game_pk)),calibration_games=sort(calgames))
    cat(bc_now(),model,label,"fitting",nrow(train),"evaluating",nrow(test),"\n");flush.console()
    nuisance<-bc_nuisance(train,calgames,c,label,logs,alphas)
    saveRDS(nuisance,file.path(art,paste0(label,"_nuisance.rds")))
    scores<-bc_score(test,nuisance,c);scores[,fold:=k]
    check(paste0(label,"_finite_scores"),all(is.finite(as.matrix(scores[,.(p,mu0,mu1,phi0,phi1)]))))
    parts[[k+1L]]<-scores
    fwrite(rbindlist(logs$fits,fill=TRUE),file.path(art,"fit_diagnostics.csv"))
    bc_json(list(completed_fold=k,at_utc=bc_now()),file.path(art,"progress.json"))
    rm(train,test,nuisance,scores);gc(FALSE)
  }
  s<-rbindlist(parts);rm(parts);setorder(s,row_id);check("all_eligible_scored_once",nrow(s)==nrow(d)&&uniqueN(s$row_id)==nrow(d));rm(d);gc(FALSE)
  bc_json(records,file.path(art,"fold_records.json"));saveRDS(s,file.path(art,"scores.rds"),compress=FALSE)
  summary<-bc_summarize(s,c);fwrite(summary,file.path(art,"action_values.csv"),bom=TRUE)
  year<-rbindlist(lapply(sort(unique(s$game_year)),function(yy){x<-bc_summarize(s[game_year==yy],c);x[,game_year:=yy];x}));fwrite(year,file.path(art,"year_values.csv"),bom=TRUE)
  check("same_action_denominator",all(summary$rows0+summary$rows1==summary$n))
  check("Q_difference_identity",max(abs(summary$Q1-summary$Q0-summary$delta),na.rm=TRUE)<1e-12)
  check("count_totals",sum(summary[level=="count",n])==sum(s$support)&&sum(summary[level=="count",n_all])==nrow(s))
  check("finite_supported_groups",all(is.finite(as.matrix(summary[n>0,.(Q0,Q1,delta,SE,family95_low,family95_high)]))))
  exclusions<-s[,.(rows=.N),by=.(game_year,count,A,reason=fifelse(!measurement_support,"measurement",fifelse(!repertoire,"entity_arm_training",fifelse(p<c$trim|p>1-c$trim,"propensity_tail","supported"))))]
  fwrite(exclusions,file.path(art,"support_exclusions.csv"));check("support_flow_total",sum(exclusions$rows)==nrow(s))
  if(setequal(unique(s$game_year),c(2024,2025))) {
    manifest$year_difference_family<-255
    keys<-c("level","count","region","pitch_group");diff<-merge(year[game_year==2024],year[game_year==2025],by=keys,suffixes=c("_2024","_2025"))
    diff[,difference_2025_minus_2024:=delta_2025-delta_2024]
    diff[,SE_difference:=sqrt(SE_2024^2+SE_2025^2)]
    diff[,df_difference:=(SE_2024^2+SE_2025^2)^2/(SE_2024^4/pmax(1,games_2024-1)+SE_2025^4/pmax(1,games_2025-1))]
    diff[,`:=`(nominal95_difference_low=difference_2025_minus_2024-qt(.975,df_difference)*SE_difference,
      nominal95_difference_high=difference_2025_minus_2024+qt(.975,df_difference)*SE_difference,
      family255_difference_low=difference_2025_minus_2024-qt(1-.05/(2*255),df_difference)*SE_difference,
      family255_difference_high=difference_2025_minus_2024+qt(1-.05/(2*255),df_difference)*SE_difference)]
    fwrite(diff,file.path(art,"year_differences.csv"),bom=TRUE)
  }
  refpath<-if(!is.null(cfg$input_dir))file.path(cfg$input_dir,paste0(model,"_reference_scores.csv")) else ""
  if(nzchar(refpath)&&file.exists(refpath)) {
    if(exists("transport"))check("transport_reference_hash",identical(bc_sha(refpath),transport$outputs[[basename(refpath)]]$sha256))
    ref<-fread(refpath);setorder(ref,row_id);check("reference_rows_match",identical(as.numeric(ref$row_id),as.numeric(s$row_id)))
    comparisons<-rbindlist(lapply(c("p","mu0","mu1","phi0","phi1"),function(f)data.table(field=f,max_absolute_error=max(abs(s[[f]]-ref[[f]])),mean_absolute_error=mean(abs(s[[f]]-ref[[f]])))))
    fwrite(comparisons,file.path(art,"python_score_comparison.csv"))
    check("python_nuisance_tolerance",all(comparisons[field%in%c("p","mu0","mu1"),max_absolute_error]<1e-6),as.list(comparisons))
    check("python_AIPW_tolerance",all(comparisons[field%in%c("phi0","phi1"),max_absolute_error]<1e-4))
    check("python_support_exact",identical(tolower(as.character(ref$support))%in%c("true","1"),s$support))
    # Recompute the reference summary in R as a second arithmetic check;
    # reference scores were exported unchanged and are never used for R fits.
    for(f in c("p","mu0","mu1","phi0","phi1"))set(s,j=paste0("r_",f),value=s[[f]])
    for(f in c("p","mu0","mu1","phi0","phi1"))set(s,j=f,value=ref[[f]])
    refs<-bc_summarize(s,c);comparison<-summary[,.(level,count,region,pitch_group,Q0,Q1,delta,SE,n,support_gate)]
    for(f in c("Q0","Q1","delta","SE"))set(comparison,j=paste0(f,"_absolute_error"),value=abs(summary[[f]]-refs[[f]]))
    fwrite(comparison,file.path(art,"python_summary_comparison.csv"))
    check("python_summary_tolerance",max(as.matrix(comparison[,.(Q0_absolute_error,Q1_absolute_error,delta_absolute_error,SE_absolute_error)]),na.rm=TRUE)<1e-6)
    original_summary_path<-if(exists("transport"))file.path(transport$references[[model]]$run,"artifacts","action_values.csv") else ""
    if(nzchar(original_summary_path)&&file.exists(original_summary_path)) {
      original_summary<-fread(original_summary_path,encoding="UTF-8")
      fields<-c("Q0","Q1","delta","SE","family95_low","family95_high","ESS0","ESS1")
      keys<-c("level","count","region","pitch_group")
      aligned<-merge(summary,original_summary,by=keys,suffixes=c("_R","_Python"),all=TRUE)
      check("original_python_summary_groups",nrow(aligned)==nrow(summary)&&!anyNA(aligned$n_R)&&!anyNA(aligned$n_Python))
      direct<-rbindlist(lapply(fields,function(f)data.table(field=f,max_absolute_error=max(abs(aligned[[paste0(f,"_R")]]-aligned[[paste0(f,"_Python")]]),na.rm=TRUE))))
      fwrite(direct,file.path(art,"original_python_aggregate_comparison.csv"))
      check("original_python_aggregate_values",all(direct[field%in%c("Q0","Q1","delta","SE","family95_low","family95_high"),max_absolute_error]<1e-6))
      check("original_python_aggregate_denominators",all(aligned$n_R==aligned$n_Python)&all(aligned$n_all_R==aligned$n_all_Python)&all(tolower(as.character(aligned$support_gate_R))==tolower(as.character(aligned$support_gate_Python))))
      manifest$original_aggregate_reference<-bc_meta(original_summary_path)
    }
    for(f in c("p","mu0","mu1","phi0","phi1")){set(s,j=f,value=s[[paste0("r_",f)]]);set(s,j=paste0("r_",f),value=NULL)}
    rm(ref,refs);gc(FALSE)
  }
  suppressPackageStartupMessages(library(ggplot2))
  plotdata<-copy(year[level=="count"]);plotdata[,count:=factor(count,levels=rev(as.vector(t(outer(0:3,0:2,paste,sep="-")))))]
  plotdata[,season:=factor(game_year)];plotdata[,supported:=ifelse(support_gate,"지원 표본 충족","비교 자료 부족")]
  gg<-ggplot(plotdata,aes(x=delta,y=count,color=season))+geom_vline(xintercept=0,linetype=2,color="grey60")+
    geom_errorbar(aes(xmin=family95_low,xmax=family95_high),orientation="y",width=.2,position=position_dodge(width=.45))+
    geom_point(aes(shape=supported),size=2.5,position=position_dodge(width=.45))+
    labs(title=paste0("카운트별 ",c$action1," − ",c$action0),subtitle="R 재계산 · 같은 관찰 표본을 보정한 공격가치 차이",
      x="최종 타석 공격가치 차이 (W)",y="투구 전 카운트",color="시즌",shape=NULL,
      caption=paste0("경기 군집 조건부 구간 · Bonferroni ",c$comparison_family," · 인과 효과·행동 추천 아님\n출처: MLB Statcast · Baseline BCAP ",c$version))+
    theme_minimal(base_size=13,base_family="Malgun Gothic")+theme(legend.position="bottom",plot.caption=element_text(hjust=0,size=9))
  ggsave(file.path(art,"count_by_year.png"),gg,width=9,height=8,dpi=180,bg="white")
  if(model=="swing") {
    heat<-copy(year[level=="region"])
    heat[,count:=factor(count,levels=as.vector(t(outer(0:3,0:2,paste,sep="-"))))]
    heat[,region_label:=factor(region,levels=c("OUTSIDE","INSIDE","LOW","HIGH","CENTER"),
      labels=c("바깥쪽","몸쪽","낮음","높음","존 안"))]
    heat[,label:=ifelse(support_gate,sprintf("%+.3f",delta),"자료 부족")]
    heat[,display_delta:=ifelse(support_gate,delta,NA_real_)]
    hp<-ggplot(heat,aes(count,region_label,fill=display_delta))+geom_tile(color="white",linewidth=.5)+
      geom_text(aes(label=label),size=3,family="Malgun Gothic")+facet_wrap(~game_year,ncol=1)+
      scale_fill_gradient2(low="#6FA8CE",mid="#FFF7EC",high="#EFA18A",midpoint=0,na.value="grey90",name="차이(W)")+
      labs(title="어느 카운트·구역에서 스윙의 관찰상 공격가치가 높았나",subtitle="스윙 − 테이크 · 양수는 스윙 쪽, 음수는 테이크 쪽 점추정",
        x="투구 전 카운트",y=NULL,caption="위·아래와 몸쪽·바깥쪽 모서리는 중복 포함 · 타일은 점추정이며 통계적 확실성을 뜻하지 않음\n고정 점수 경기 군집 구간은 CSV 참고 · 인과 효과·행동 추천 아님 · 출처: MLB Statcast / Baseline BCAP")+
      theme_minimal(base_size=12,base_family="Malgun Gothic")+theme(panel.grid=element_blank(),legend.position="bottom",plot.caption=element_text(hjust=0,size=9))
    ggsave(file.path(art,"swing_regions_by_year.png"),hp,width=12,height=7,dpi=180,bg="white")
  }
  metrics<-list(n=nrow(s),support=sum(s$support),coverage=mean(s$support),games=uniqueN(s$game_pk),
    MSE=mean((s$Y-ifelse(s$A==1,s$mu1,s$mu0))^2),Brier=mean((s$A-s$p)^2),
    logloss=-mean(s$A*log(s$p)+(1-s$A)*log1p(-s$p)),all_fit_converged=all(vapply(logs$fits,function(x)x$converged,logical(1))),
    fit_logs=length(logs$fits),summary_groups=nrow(summary),years=sort(unique(s$game_year)),policy_learning=FALSE)
  check("input_preserved_after_fit",identical(bc_sha(manifest$input$path),manifest$input$sha256))
  if(!is.null(manifest$input_preparation))check("preparation_manifest_preserved",identical(bc_sha(manifest$input_preparation$path),manifest$input_preparation$sha256))
  if(!is.null(manifest$split_inputs))for(info in manifest$split_inputs)check(paste0("split_preserved_",basename(info$path)),identical(bc_sha(info$path),info$sha256))
  bc_json(metrics,file.path(art,"metrics.json"));bc_json(list(status="PASS",checks=checks,scope="Numerical implementation and original-score reproduction; not causal validation"),file.path(art,"checks.json"))
  writeLines(capture.output(sessionInfo()),file.path(art,"sessionInfo.txt"))
  manifest$status<-"COMPLETE";manifest$finished_at_utc<-bc_now();manifest$metrics<-metrics
  manifest$outputs<-lapply(list.files(art,full.names=TRUE,recursive=TRUE),bc_meta);bc_json(manifest,file.path(run,"manifest.json"))
  writeLines(c(paste0("# ",basename(run)),"","R 계산 완료 · EXPERIMENTAL.",
    "","기존 보조 모형을 불러오지 않고 R에서 centered ridge·Platt calibration·3fold OOF AIPW를 다시 적합했다.",
    "SB는 원 개발에서 선택된 α를 고정했고 튜닝은 반복하지 않았다. 같은 게임 분할이 제공되면 이를 그대로 재생한다.",
    "","블로그용 그림: artifacts/count_by_year.png. 표: action_values.csv, year_values.csv, year_differences.csv(해당 시).",
    "","관찰상 비교이며 인과 효과나 행동 추천이 아니다. 학습 변동·경기 간 선수 의존성은 구간에 포함되지 않는다.",
    "2024·2025 연도 차이는 고정 OOF 점수의 독립 경기 근사이며, 공유된 학습 모형의 불확실성은 포함하지 않는다."),file.path(run,"README.md"),useBytes=TRUE)
  cat(bc_now(),"COMPLETE",basename(run),"n=",metrics$n,"support=",metrics$support,"\n")
},error=function(e){
  if(exists("logs")&&length(logs$fits))fwrite(rbindlist(logs$fits,fill=TRUE),file.path(art,"fit_diagnostics.csv"))
  manifest$status<-"FAILED";manifest$error<-conditionMessage(e);manifest$finished_at_utc<-bc_now()
  bc_json(manifest,file.path(run,"manifest.json"));bc_json(list(status="FAIL",checks=checks,error=conditionMessage(e)),file.path(art,"checks.json"));stop(e)
})
