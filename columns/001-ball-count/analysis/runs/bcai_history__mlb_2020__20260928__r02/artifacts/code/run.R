# Run from repository root: tools/run_r.ps1 -Script .../run.R path/to/config.json
suppressPackageStartupMessages({library(data.table); library(jsonlite); library(digest); library(ggplot2)})
script_arg <- grep("^--file=",commandArgs(),value=TRUE)[1]
script_path <- normalizePath(sub("^--file=","",script_arg),winslash="/",mustWork=TRUE)
core_path <- file.path(dirname(script_path),"bcai.R")
source(core_path, encoding="UTF-8")
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=1) stop("Provide one run config JSON path, from repository root")
cfg <- fromJSON(args[1], simplifyVector=FALSE)
if (!identical(cfg$model_id,"BCAI-OBS-v1.0.0") || !identical(cfg$version,"1.0.0")) stop("Unsupported model")
if (!grepl("^bcai_[a-z_]+__mlb_[a-z0-9_]+__[0-9]{8}__r[0-9]{2,}$",cfg$run_id)) stop("Invalid run ID")
column <- "columns/001-ball-count"
run <- file.path(column,"analysis/runs",cfg$run_id)
art <- file.path(run,"artifacts"); figdir <- file.path(column,"figures",cfg$run_id)
if (file.exists(file.path(run,"manifest.json")) || dir.exists(art) || dir.exists(figdir)) stop("Run already has outputs; use a NEW run ID")
dir.create(art,recursive=TRUE); dir.create(figdir,recursive=TRUE)
json <- function(x,path) write_json(x,path,pretty=TRUE,auto_unbox=TRUE,na="null",digits=NA)
meta <- function(path) list(path=path,bytes=unname(file.info(path)$size),sha256=digest(file=path,algo="sha256"))
stamp <- function() format(Sys.time(),"%Y-%m-%dT%H:%M:%S%z")
# Archived schedules can mark postponed/cancelled entries abstract Final.
# Completed Early is a played final game (e.g. rain-shortened); keep it.
completed_regular_game <- function(g) {
  identical(g$gameType,"R") && identical(g$status$abstractGameState,"Final") &&
    identical(g$status$codedGameState,"F") &&
    isTRUE(g$status$detailedState %in% c("Final","Completed Early"))
}
code <- c(core_path,script_path)
paths <- unique(c(unlist(cfg$input_csv),unlist(cfg$input_provenance),args[1],
  vapply(cfg$seasons, function(s) s$schedule, character(1)),cfg$weights_source,cfg$source_notes,
  "models/bcai/observed/v1.0.0/specification.yaml"))
manifest <- list(run_id=cfg$run_id,model_id=cfg$model_id,version=cfg$version,
  role="R observational recalculation and exploratory year comparison",status="RUNNING",
  model_status="VALIDATED within prior documented scope; no promotion",started_at=stamp(),
  input=list(),code=lapply(code,meta),parameters=cfg,
  environment=list(R=R.version.string,packages=lapply(c("data.table","ggplot2","jsonlite","digest"), function(p) list(package=p,version=as.character(packageVersion(p))))))
json(manifest,file.path(run,"manifest.json"))
tryCatch({
  if (!all(file.exists(paths))) stop(paste("Missing inputs:",paste(paths[!file.exists(paths)],collapse=", ")))
  manifest$input <- lapply(paths,meta)
  dir.create(file.path(art,"code"))
  if(!all(file.copy(code,file.path(art,"code",basename(code))))) stop("Code snapshot copy failed")
  manifest$code_snapshot <- lapply(file.path(art,"code",basename(code)),meta)
  csv_paths <- normalizePath(unlist(cfg$input_csv),winslash="/",mustWork=TRUE)
  linked <- character()
  for(prov_path in unlist(cfg$input_provenance)) {
    prov <- fromJSON(prov_path,simplifyVector=FALSE)
    op <- if(is.list(prov$output)) prov$output$path else prov$output
    expected_hash <- if(is.list(prov$output)) prov$output$sha256 else prov$output_sha256
    if(is.null(op) || is.null(expected_hash)) stop("Provenance lacks output path/hash")
    actual_path <- normalizePath(op,winslash="/",mustWork=TRUE)
    if(!actual_path %in% csv_paths || !identical(expected_hash,digest(file=actual_path,algo="sha256"))) stop("Provenance CSV link or hash mismatch")
    linked <- c(linked,actual_path)
  }
  if(!setequal(csv_paths,linked) || anyDuplicated(csv_paths)) stop("Every input CSV needs matching provenance")
  json(manifest,file.path(run,"manifest.json"))
  cat("Reading R inputs\n")
  d <- rbindlist(lapply(unlist(cfg$input_csv),fread,encoding="UTF-8"),use.names=TRUE)
  years <- as.integer(unlist(cfg$years))
  if (!setequal(d$game_year,years) || anyDuplicated(years)) stop("Input years differ from config")
  if (!setequal(vapply(cfg$seasons, function(s) as.integer(s$year), integer(1)),years)) stop("Season definitions mismatch")
  if (!"game_date" %in% names(d)) stop("game_date required for coverage verification")
  coverage <- lapply(cfg$seasons,function(s) {
    sch <- fromJSON(s$schedule,simplifyVector=FALSE)
    games <- unlist(lapply(sch$dates,function(day) day$games),recursive=FALSE)
    games <- Filter(function(g) completed_regular_game(g) &&
      g$officialDate<=s$cutoff && substr(g$officialDate,1,4)==as.character(s$year),games)
    expected <- unique(vapply(games,function(g) as.numeric(g$gamePk),numeric(1)))
    observed <- unique(d[game_year==s$year]$game_pk)
    if (!length(expected) || !setequal(expected,observed)) stop(paste("Schedule mismatch",s$year,
      "missing",length(setdiff(expected,observed)),"extra",length(setdiff(observed,expected))))
    dates <- as.character(d[game_year==s$year]$game_date)
    if (anyNA(dates) || any(substr(dates,1,4)!=as.character(s$year)) || any(dates>s$cutoff)) stop("Invalid observed dates")
    list(year=s$year,scope=s$scope,cutoff=s$cutoff,games=length(observed),first=min(dates),last=max(dates),schedule_match=TRUE)
  })
  weights <- rbindlist(cfg$weights)
  cat("Calculating plate-appearance eligibility and BCAI\n")
  p <- prepare_bcai(d,weights)
  checks <- list(input_schedule_coverage=coverage,sample=p$sample,comparison_scope="points, denominators, exclusions; bootstrap RNG differs from Python")
  if (!is.null(cfg$reference_run)) {
    ref <- file.path(cfg$reference_run,"artifacts")
    previous <- fread(file.path(ref,"advantage_count_results.csv"),encoding="UTF-8")
    prior_season <- fread(file.path(ref,"advantage_season_sensitivity.csv"))
    prior_audit <- fromJSON(file.path(ref,"advantage_audit.json"))
    combined <- merge(p$combined,previous,by="count",suffixes=c("_R","_Python"))
    season <- merge(p$season,prior_season,by=c("year","count"),suffixes=c("_R","_Python"))
    checks$max_combined_index_error <- max(abs(combined$index_R-combined$index_Python))
    checks$max_season_index_error <- max(abs(season$index_R-season$index_Python))
    checks$max_season_value_error <- max(abs(season$value_R-season$value_Python))
    stopifnot(nrow(combined)==12,nrow(season)==12*length(years),
      all(combined$N_PA_R==combined$N_PA_Python),all(season$N_R==season$N_Python),
      checks$max_combined_index_error<cfg$tolerance,checks$max_season_index_error<cfg$tolerance,
      checks$max_season_value_error<cfg$tolerance)
    for (name in c("raw_rows","all_PA","eligible_PA","games","repeated_count_rows_removed")) stopifnot(p$sample[[name]]==prior_audit[[name]])
    stopifnot(setequal(names(p$sample$exclusions),names(prior_audit$exclusions)))
    for (name in names(prior_audit$exclusions)) stopifnot(p$sample$exclusions[[name]]==prior_audit$exclusions[[name]])
    checks$historical_reference <- cfg$reference_run
    checks$reference_hashes <- lapply(file.path(ref,c("advantage_count_results.csv","advantage_season_sensitivity.csv","advantage_audit.json")),meta)
    fwrite(combined[,.(count,R=index_R,Python=index_Python,difference=index_R-index_Python,N_PA=N_PA_R)],file.path(art,"point_reproduction.csv"),bom=TRUE)
    cat("Historical point estimates and sample audit match\n")
  }
  json(checks,file.path(art,"pre_bootstrap_check.json"))
  cat("Game-cluster bootstrap:",cfg$bootstrap_replicates,"replicates per year\n")
  result <- bootstrap_bcai(p,as.integer(cfg$bootstrap_replicates),as.integer(cfg$seed),cfg$comparisons)
  fwrite(result$season,file.path(art,"season_indices.csv"),bom=TRUE)
  fwrite(result$combined,file.path(art,"combined_indices.csv"),bom=TRUE)
  fwrite(result$differences,file.path(art,"year_differences.csv"),bom=TRUE)
  fwrite(p$cohorts,file.path(art,"cohorts.csv"),bom=TRUE)
  fwrite(p$audit,file.path(art,"exclusion_audit.csv"),bom=TRUE)
  fwrite(p$events,file.path(art,"event_rates.csv"),bom=TRUE)
  saveRDS(result$draws,file.path(art,"bootstrap_draws.rds"))
  writeLines(capture.output(sessionInfo()),file.path(art,"sessionInfo.txt"))
  font <- if (.Platform$OS.type=="windows") "Malgun" else "sans"
  if (.Platform$OS.type=="windows") windowsFonts(Malgun=windowsFont("Malgun Gothic"))
  save_plot <- function(plot,name,height=1100) {
    png(file.path(figdir,name),width=1600,height=height,res=160,type=if(.Platform$OS.type=="windows") "windows" else "cairo",bg="white")
    print(plot); dev.off()
  }
  theme_blog <- theme_minimal(base_size=16,base_family=font)+theme(plot.title=element_text(face="bold",size=23),
    plot.subtitle=element_text(size=13),plot.caption=element_text(size=10,hjust=0),
    panel.grid.minor=element_blank(),legend.position="top",plot.margin=margin(20,30,20,20))
  sd <- copy(result$season)
  sd[, year_label:=factor(year)]
  offsets <- seq(-.22,.22,length.out=length(years)); if(length(years)==1) offsets<-0
  sd[, ypos:=13-match(count,COUNTS)+offsets[match(year,sort(years))]]
  caption <- paste0("출처: MLB Statcast · BCAI-OBS-v1.0.0 / 시즌별 유효 타석: ",
    paste(sprintf("%s년 %s개",p$cohorts$year,format(p$cohorts$eligible_PA,big.mark=",")),collapse=" · "),
    "\n각 카운트 도달 타석의 최종 공격가치. 인과 효과·승률이 아닙니다.")
  chart_title <- if(length(years)==1) paste0(years,"년, 볼카운트별 공격가치는?") else "볼카운트별 공격가치, 해가 바뀌어도 비슷할까?"
  plot <- ggplot(sd,aes(x=index,y=ypos,color=year_label))+
    geom_vline(xintercept=100,linetype="dashed",color="#64748B")+
    geom_segment(aes(x=simultaneous95_low,xend=simultaneous95_high,yend=ypos),linewidth=.8)+
    geom_point(size=2.7)+scale_y_continuous(breaks=12:1,labels=COUNTS)+
    labs(title=chart_title,
      subtitle="각 시즌 0-0 = 100 · 선은 시즌별 11개 카운트의 근사 동시 95% 구간",
      x="BCAI 지수",y="투구 전 볼카운트",color="시즌",caption=caption)+theme_blog
  save_plot(plot,"season_comparison.png")
  if(nrow(result$differences)) {
    dif <- copy(result$differences); dif[, ypos:=13-match(count,COUNTS)]
    plot2 <- ggplot(dif,aes(x=difference,y=ypos))+
      geom_vline(xintercept=0,linetype="dashed",color="#64748B")+
      geom_segment(aes(x=simultaneous95_low,xend=simultaneous95_high,yend=ypos),linewidth=.8,color="#94A3B8")+
      geom_segment(aes(x=CI95_low,xend=CI95_high,yend=ypos),linewidth=2,color="#2563EB")+
      geom_point(size=2.5,color="#172554")+scale_y_continuous(breaks=12:1,labels=COUNTS)+
      facet_wrap(~comparison)+labs(title="연도 차이, 어느 정도까지 확실하게 말할 수 있을까?",
      subtitle="회색: 전체 지정 비교의 근사 동시 95% 구간 · 파랑: 개별 95% 구간",
      x="뒤 연도 − 앞 연도 (BCAI 지수 포인트)",y="투구 전 볼카운트",caption=paste0(caption,
      "\n0을 포함한다고 두 시즌이 같다는 뜻은 아닙니다. 0-0의 차이는 정의상 0입니다."))+theme_blog
    save_plot(plot2,"year_difference.png")
  }
  preserved <- vapply(manifest$input,function(m) identical(m$sha256,digest(file=m$path,algo="sha256")),logical(1))
  if (!all(preserved)) stop("An input changed during the run")
  checks$status <- "PASS"; checks$inputs_unchanged <- TRUE; checks$bootstrap_criticals <- result$critical
  checks$RNG <- RNGkind(); checks$bootstrap_scope <- "fixed external weights; within-season game clusters; no cross-game/player dependence correction"
  json(checks,file.path(art,"validation.json"))
  manifest$status <- "COMPLETE"; manifest$completed_at <- stamp(); manifest$sample <- p$sample
  manifest$coverage <- coverage; manifest$critical <- result$critical
  manifest$outputs <- lapply(c(list.files(art,full.names=TRUE,recursive=TRUE),list.files(figdir,full.names=TRUE)),meta)
  manifest$figures <- figdir; manifest$validation <- checks
  json(manifest,file.path(run,"manifest.json"))
  cat("COMPLETE:",cfg$run_id,"eligible PA",p$sample$eligible_PA,"\n")
  if(nrow(result$differences)) print(result$differences[,.(comparison,count,difference,simultaneous95_low,simultaneous95_high,excludes_zero_simultaneous)])
},error=function(e) {
  manifest$status <- "FAILED"; manifest$failed_at <- stamp(); manifest$error <- conditionMessage(e)
  json(manifest,file.path(run,"manifest.json")); stop(e)
})
