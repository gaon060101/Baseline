# Verify the default venue policy against the legacy Python dict's last occurrence.
source("models/bcap/r/prepare_raw.R",encoding="UTF-8")
suppressPackageStartupMessages(library(jsonlite))
paths <- c("2020/snapshot_20260928_r_history/schedule_2020.json",
 "2021/snapshot_20260928_r_history/schedule_2021.json",
 "2022/snapshot_20260928_r_history/schedule_2022.json",
 "2023/snapshot_20260908_ridge_v02/schedule_2023.json",
 "2024/schedule_2024.json","2025/schedule_2025.json",
 "2026/snapshot_20260908_ridge_v02/schedule_2026.json")
paths <- file.path("columns/001-ball-count/data/raw/mlb",paths)
expected <- c(898L,2429L,2430L,2430L,2429L,2430L,2165L)
chr <- function(x)if(is.null(x))NA_character_ else as.character(x)
checks <- lapply(seq_along(paths),function(i) {
 yy<-2019L+i;cutoff<-if(yy==2026)"2026-09-07" else paste0(yy,"-12-31")
 sch<-fromJSON(paths[i],simplifyVector=FALSE)
 games<-unlist(lapply(sch$dates,function(day)lapply(day$games,function(g){g$archive_date<-day$date;g})),recursive=FALSE)
 for(j in seq_along(games))games[[j]]$archive_index<-j
 scoped<-Filter(function(g)g$officialDate<=cutoff && substr(g$officialDate,1,4)==as.character(yy),games)
 old<-Filter(function(g)identical(g$gameType,"R") && identical(g$status$abstractGameState,"Final") &&
  !identical(g$status$detailedState,"Cancelled"),scoped)
 new<-Filter(completed_regular_bcap_game,scoped)
 tab<-rbindlist(lapply(new,function(g)data.table(game_pk=as.numeric(g$gamePk),year=yy,venue=as.numeric(g$venue$id),
  official_date=g$officialDate,cutoff=cutoff,schedule_record_index=g$archive_index,schedule_date=g$archive_date,
  game_date=chr(g$gameDate),venue_name=chr(g$venue$name),resume_date=chr(g$resumeDate),resumed_from=chr(g$resumedFrom),
  description=chr(g$description))))
 resolved<-normalize_bcap_schedule(tab)
 legacy<-list()
 for(g in old)legacy[[as.character(g$gamePk)]]<-as.numeric(g$venue$id)
 legacy_values<-vapply(as.character(resolved$games$game_pk),function(id)legacy[[id]],numeric(1))
 stopifnot(nrow(resolved$games)==expected[i],identical(resolved$games$venue,unname(legacy_values)))
 if(yy %in% c(2020,2021)) {
  id<-if(yy==2020)630882 else 633224;selected<-if(yy==2020)2 else 2680
  stopifnot(resolved$games[game_pk==id]$venue==selected,nrow(resolved$venue_conflicts)==2L,
   inherits(tryCatch(normalize_bcap_schedule(tab,"reject"),error=identity),"error"))
 } else stopifnot(nrow(resolved$venue_conflicts)==0L)
 list(year=yy,path=paths[i],sha256=digest::digest(file=paths[i],algo="sha256"),
  games=nrow(resolved$games),all_selected_venues_match_legacy_dictionary=TRUE,
  normalization=resolved$audit,conflicting_records=resolved$venue_conflicts)
})
output<-"columns/001-ball-count/analysis/r_bcap_history_20260928/legacy_venue_policy_check.json"
if(file.exists(output))stop("Output already exists")
write_json(list(status="PASS",checked_at=format(Sys.time(),"%Y-%m-%dT%H:%M:%S%z"),
 code=BCAP_PREP_SCRIPT,legacy_code=list(path="models/bcap/data.py",sha256=digest::digest(file="models/bcap/data.py",algo="sha256")),
 policy="legacy_last_schedule_record",scope="Game-level venue only; no pitch-level relocation reconstruction.",
 checks=checks),output,pretty=TRUE,auto_unbox=TRUE,digits=NA)
cat("PASS: 2020-2026 selected game venues equal the legacy last-record dictionary; conflicting records are retained in audit and strict reject remains available\n")

