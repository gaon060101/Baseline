# Read-only postflight for completed BCAP R runs. Writes a separate new audit.
suppressPackageStartupMessages(library(data.table));setDTthreads(2)
args<-commandArgs(trailingOnly=TRUE)
if(length(args)<2L)stop("Usage: check_bcap_r_outputs.R new-audit-dir run-dir [run-dir...]")
output<-args[1];runs<-args[-1]
if(file.exists(output))stop("Audit path exists; choose a new path")
dir.create(output,recursive=TRUE)
sha<-function(path)digest::digest(file=path,algo="sha256",serialize=FALSE)
checks<-list();numeric<-list();references<-list();metrics<-list()
ck<-function(run,name,ok,detail=NULL){checks[[length(checks)+1L]]<<-list(run_id=run,check=name,status=if(isTRUE(ok))"PASS"else"FAIL",detail=detail);if(!isTRUE(ok))stop(paste(run,name))}
write_report<-function(status,error=NULL){
  jsonlite::write_json(list(status=status,at_utc=format(Sys.time(),"%Y-%m-%dT%H:%M:%SZ",tz="UTC"),
    checks=checks,numeric_comparisons=numeric,references=references,metrics=metrics,error=error,
    limitations="저장된 산출물의 보존·산술 검산. 통계 식별·전체 학습 불확실성·구간 실제 포함률을 검증하지 않음.",
    execution_note="SB r01은 COMPLETE 저장 이후 원 실행기 수정 중 후속 파싱 오류로 프로세스가 종료됐음. 본 감사가 동결 코드·산출물 해시 및 원 Python 집계와 수치 일치를 따로 확인함. 완료 manifest를 수정하지 않음."),
    file.path(output,"postflight.json"),pretty=TRUE,auto_unbox=TRUE,na="null",digits=16)
}
tryCatch({
for(path in runs){
  id<-basename(path);m<-jsonlite::fromJSON(file.path(path,"manifest.json"),simplifyVector=FALSE)
  ck(id,"complete_manifest",identical(m$status,"COMPLETE"))
  checkpath<-file.path(path,"artifacts/checks.json");report<-jsonlite::fromJSON(checkpath,simplifyVector=FALSE)
  ck(id,"all_runtime_checks_pass",identical(report$status,"PASS")&&all(vapply(report$checks,function(x)identical(x$status,"PASS"),logical(1))))
  ck(id,"all_artifact_hashes_match",all(vapply(m$outputs,function(x)file.exists(x$path)&&identical(sha(x$path),x$sha256),logical(1))))
  ck(id,"input_preserved",identical(sha(m$input$path),m$input$sha256))
  ck(id,"frozen_engine_matches_executed_code",identical(sha(file.path(path,"artifacts/frozen_engine.R")),m$code[[1]]$sha256))
  ck(id,"frozen_runner_matches_executed_code",identical(sha(file.path(path,"artifacts/frozen_run.R")),m$code[[2]]$sha256))
  if(!is.null(m$split_inputs))ck(id,"original_fold_maps_preserved",all(vapply(m$split_inputs,function(x)identical(sha(x$path),x$sha256),logical(1))))
  cmp<-fread(file.path(path,"artifacts/python_score_comparison.csv"));numeric[[id]]<-cmp
  ck(id,"nuisance_and_AIPW_tolerances",all(cmp[field%in%c("p","mu0","mu1"),max_absolute_error]<1e-6)&&all(cmp[field%in%c("phi0","phi1"),max_absolute_error]<1e-4))
  sum<-fread(file.path(path,"artifacts/action_values.csv"),encoding="UTF-8")
  ck(id,"same_denominator_and_Q_identity",all(sum$rows0+sum$rows1==sum$n)&&max(abs(sum$Q1-sum$Q0-sum$delta),na.rm=TRUE)<1e-12)
  provpath<-m$transport_provenance$path;prov<-jsonlite::fromJSON(provpath,simplifyVector=FALSE)
  for(f in names(prov$outputs))ck(id,paste0("transport_hash_",f),identical(sha(file.path(dirname(provpath),f)),prov$outputs[[f]]$sha256))
  model<-m$run_config$model;old<-file.path(prov$references[[model]]$run,"artifacts/action_values.csv")
  if(file.exists(old)){
    oldsum<-fread(old,encoding="UTF-8");keys<-c("level","count","region","pitch_group")
    joined<-merge(sum,oldsum,by=keys,suffixes=c("_R","_Python"),all=TRUE)
    ck(id,"original_aggregate_keys",nrow(joined)==nrow(sum)&&!anyNA(joined$n_R)&&!anyNA(joined$n_Python))
    differences<-rbindlist(lapply(c("Q0","Q1","delta","SE","family95_low","family95_high","ESS0","ESS1"),function(f)data.table(field=f,max_absolute_error=max(abs(joined[[paste0(f,"_R")]]-joined[[paste0(f,"_Python")]]),na.rm=TRUE))))
    fwrite(differences,file.path(output,paste0(model,"_original_aggregate_comparison.csv")))
    ck(id,"original_aggregate_numerics",all(differences[!field%in%c("ESS0","ESS1"),max_absolute_error]<1e-6))
    ck(id,"original_aggregate_denominators_support",all(joined$n_R==joined$n_Python)&&all(joined$n_all_R==joined$n_all_Python)&&
      all(tolower(as.character(joined$support_gate_R))==tolower(as.character(joined$support_gate_Python))))
    ck(id,"original_evidence_labels",all(joined$evidence_R==joined$evidence_Python)&&all(joined$arithmetic_direction_R==joined$arithmetic_direction_Python))
    references[[id]]<-list(path=old,sha256=sha(old),comparison="Original independently computed Python aggregate CSV")
  } else references[[id]]<-list(comparison="No original standalone aggregate; full-row original score and R recomputed aggregate comparisons passed")
  metrics[[id]]<-m$metrics
}
# Verify geometry/finite-data assumptions in the transported eligible inputs,
# including early runs completed before these prefit guards were added.
sourcepath<-file.path(dirname(provpath),"rows.csv")
cols<-c("stand","plate_x","plate_z","sz_top","sz_bot","release_speed","pfx_x","pfx_z","eligible_pitch","eligible_swing","A_pitch_sb")
d<-fread(sourcepath,select=cols,na.strings="__BCAP_NA__")
eligible<-tolower(as.character(d$eligible_pitch))%in%c("true","1")|tolower(as.character(d$eligible_swing))%in%c("true","1")
d<-d[eligible];ck("shared_input","known_handedness",all(d$stand%in%c("R","L")))
valid<-is.finite(d$plate_x)&is.finite(d$plate_z)&is.finite(d$sz_top)&is.finite(d$sz_bot)&d$sz_top>d$sz_bot
center<-valid&abs(d$plate_x)<=17/24&d$plate_z>=d$sz_bot&d$plate_z<=d$sz_top;center[is.na(center)]<-FALSE
sb<-d$A_pitch_sb;sb[is.na(sb)]<-0;ck("shared_input","geometric_SB_identity",all(center==(sb==1)))
x<-d$plate_x*ifelse(d$stand=="R",1,-1)
regions<-cbind(center,valid&d$plate_z>d$sz_top,valid&d$plate_z<d$sz_bot,valid&x< -17/24,valid&x>17/24);regions[is.na(regions)]<-FALSE
ck("shared_input","maximum_two_overlapping_regions",max(rowSums(regions))<=2)
physical<-as.matrix(d[,.(release_speed,pfx_x,pfx_z,plate_x,plate_z,sz_top,sz_bot)])
ck("shared_input","no_infinite_physical_measurements",!any(is.infinite(physical)))
write_report("PASS")
writeLines(c("# BCAP R 산출물 사후 검산","","모든 검사 PASS.",
  "","완료 manifest·실행별 검사·원본 입력·동결 실행 코드·전체 출력의 SHA256을 대조했다.",
  "PITCH·S/B·SWING의 기존 Python 요약 CSV가 있으면 R 집계와 직접 비교했다. FF는 원 행별 점수와 재집계 대조를 사용했다.",
  "S/B 완료 저장 뒤의 프로세스 종료 오류를 숨기지 않고 별도 기록했으며, 원 완료 manifest를 수정하지 않았다.",
  "","상세 근거: postflight.json 및 모델별 original_aggregate_comparison.csv."),file.path(output,"README.md"),useBytes=TRUE)
cat("PASS BCAP postflight:",length(runs),"completed runs;",length(checks),"checks\n")
},error=function(e){write_report("FAIL",conditionMessage(e));stop(e)})
