# Small archival schedule check; no pitch data preparation or model fitting.
source("models/bcap/r/prepare_raw.R",encoding="UTF-8")
suppressPackageStartupMessages(library(jsonlite))
bcai_source <- "models/bcai/observed/v1.0.0/r/run.R"
expressions <- as.list(parse(bcai_source,encoding="UTF-8"))
definition <- Filter(function(x) is.call(x) && identical(x[[1L]],as.name("<-")) &&
  identical(x[[2L]],as.name("completed_regular_game")),expressions)
stopifnot(length(definition)==1L)
env <- new.env(parent=baseenv());eval(definition[[1L]],envir=env)
paths <- c("2020/snapshot_20260928_r_history/schedule_2020.json",
  "2021/snapshot_20260928_r_history/schedule_2021.json",
  "2022/snapshot_20260928_r_history/schedule_2022.json",
  "2023/snapshot_20260908_ridge_v02/schedule_2023.json",
  "2024/schedule_2024.json","2025/schedule_2025.json",
  "2026/snapshot_20260908_ridge_v02/schedule_2026.json")
paths <- file.path("columns/001-ball-count/data/raw/mlb",paths)
expected <- c(898L,2429L,2430L,2430L,2429L,2430L,2165L)
checks <- lapply(seq_along(paths),function(i) {
  yy <- 2019L+i; cutoff <- if (yy==2026) "2026-09-07" else paste0(yy,"-12-31")
  sch <- fromJSON(paths[i],simplifyVector=FALSE)
  games <- unlist(lapply(sch$dates,function(day)day$games),recursive=FALSE)
  ours <- vapply(games,completed_regular_bcap_game,logical(1))
  theirs <- vapply(games,env$completed_regular_game,logical(1))
  stopifnot(identical(ours,theirs))
  scoped <- Filter(function(g)g$officialDate<=cutoff && substr(g$officialDate,1,4)==as.character(yy),games)
  old <- Filter(function(g)identical(g$gameType,"R") && identical(g$status$abstractGameState,"Final") &&
    !identical(g$status$detailedState,"Cancelled"),scoped)
  new <- Filter(completed_regular_bcap_game,scoped)
  ids <- function(x) unique(vapply(x,function(g)as.numeric(g$gamePk),numeric(1)))
  removed <- setdiff(ids(old),ids(new)); added <- setdiff(ids(new),ids(old))
  stopifnot(length(ids(new))==expected[i],!length(added))
  if (yy==2020) stopifnot(setequal(removed,c(631471,631472))) else stopifnot(!length(removed))
  schedule_table <- rbindlist(lapply(new,function(g)data.table(
    game_pk=as.numeric(g$gamePk),year=yy,venue=as.numeric(g$venue$id),official_date=g$officialDate,cutoff=cutoff)))
  normalized <- tryCatch(normalize_bcap_schedule(schedule_table),error=identity)
  conflicts <- schedule_table[,.(variants=uniqueN(.SD)),by=game_pk,.SDcols=c("year","venue","official_date","cutoff")][variants>1L]
  if(yy %in% c(2020,2021)) {
    stopifnot(inherits(normalized,"error"),identical(conditionMessage(normalized),"Conflicting schedule records for the same game_pk"),
      identical(conflicts$game_pk,if(yy==2020)630882 else 633224))
  } else stopifnot(!inherits(normalized,"error"),nrow(conflicts)==0L)
  list(year=yy,path=paths[i],sha256=digest::digest(file=paths[i],algo="sha256"),
    matches_bcai_on_all_records=TRUE,old_records=length(old),completed_records=length(new),
    old_unique_games=length(ids(old)),completed_unique_games=length(ids(new)),
    removed_ids=as.list(removed),preparation_gate=if(inherits(normalized,"error"))"BLOCKED_CONFLICTING_VENUE" else "PASS",
    normalization=if(inherits(normalized,"error"))NULL else normalized$audit,
    conflicting_records=unique(schedule_table[game_pk %in% conflicts$game_pk]))
})
output <- "columns/001-ball-count/analysis/r_bcap_history_20260928/preparation_schedule_check.json"
if(file.exists(output))stop("Check output already exists")
write_json(list(status="PASS_PREDICATE_WITH_PREPARATION_BLOCKERS",checked_at=format(Sys.time(),"%Y-%m-%dT%H:%M:%S%z"),
  code=BCAP_PREP_SCRIPT,bcai_code=list(path=bcai_source,sha256=digest::digest(file=bcai_source,algo="sha256")),
  checks=checks),output,pretty=TRUE,auto_unbox=TRUE,digits=NA)
cat("PASS: completion predicates and expected 2020-2026 game sets; preparation safely BLOCKS conflicting venue aliases in 2020 and 2021\n")

