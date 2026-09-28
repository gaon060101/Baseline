# Extract and test the actual runner predicate without starting an analysis run.
suppressPackageStartupMessages({library(data.table);library(jsonlite);library(digest)})
runner <- "models/bcai/observed/v1.0.0/r/run.R"
expressions <- as.list(parse(runner,encoding="UTF-8"))
match <- Filter(function(x) is.call(x) && identical(x[[1]],as.name("<-")) &&
  identical(x[[2]],as.name("completed_regular_game")),expressions)
stopifnot(length(match)==1)
env <- new.env(parent=baseenv());eval(match[[1]],envir=env)
predicate <- env$completed_regular_game
fake <- function(coded,detail,abstract="Final",type="R") list(gameType=type,
  status=list(abstractGameState=abstract,codedGameState=coded,detailedState=detail))
cases <- list(final=list(game=fake("F","Final"),expected=TRUE),
  completed_early=list(game=fake("F","Completed Early"),expected=TRUE),
  postponed_despite_abstract_final=list(game=fake("D","Postponed"),expected=FALSE),
  cancelled_despite_abstract_final=list(game=fake("C","Cancelled"),expected=FALSE),
  suspended=list(game=fake("I","Suspended"),expected=FALSE),
  mismatched_final_detail=list(game=fake("D","Final"),expected=FALSE),
  future_status=list(game=fake("F","Unrecognized"),expected=FALSE),
  missing_status=list(game=list(gameType="R"),expected=FALSE),
  postseason=list(game=fake("F","Final",type="D"),expected=FALSE))
for(x in cases)stopifnot(identical(predicate(x$game),x$expected))
paths <- c("2020/snapshot_20260928_r_history/schedule_2020.json",
  "2021/snapshot_20260928_r_history/schedule_2021.json","2022/snapshot_20260928_r_history/schedule_2022.json",
  "2023/snapshot_20260908_ridge_v02/schedule_2023.json","2024/schedule_2024.json","2025/schedule_2025.json")
paths <- file.path("columns/001-ball-count/data/raw/mlb",paths)
counts <- c(898,2429,2430,2430,2429,2430)
status_tables <- list();results <- list()
for(i in seq_along(paths)) {
  sch <- fromJSON(paths[i],simplifyVector=FALSE)
  games <- unlist(lapply(sch$dates,function(day)day$games),recursive=FALSE)
  regular <- Filter(function(g)identical(g$gameType,"R"),games)
  old <- Filter(function(g)identical(g$status$abstractGameState,"Final") && !identical(g$status$detailedState,"Cancelled"),regular)
  new <- Filter(predicate,regular)
  old_ids <- unique(vapply(old,function(g)as.numeric(g$gamePk),numeric(1)))
  new_ids <- unique(vapply(new,function(g)as.numeric(g$gamePk),numeric(1)))
  removed <- setdiff(old_ids,new_ids);stopifnot(length(new_ids)==counts[i])
  if(i==1)stopifnot(setequal(removed,c(631471,631472))) else stopifnot(!length(removed))
  tab <- rbindlist(lapply(regular,function(g)data.table(year=2020+i-1L,
    abstract=g$status$abstractGameState,coded=g$status$codedGameState,status_code=g$status$statusCode,detailed=g$status$detailedState)))
  status_tables[[i]] <- tab[,.N,by=.(year,abstract,coded,status_code,detailed)]
  results[[i]] <- list(year=2020+i-1L,old_unique_games=length(old_ids),completed_unique_games=length(new_ids),removed_ids=as.list(removed))
  if(i==1)observed_expected <- new_ids
}
input <- "columns/001-ball-count/data/processed/r_history_20260928/2020/pitches.csv"
observed <- unique(fread(input,select="game_pk")$game_pk)
stopifnot(setequal(observed,observed_expected))
metadata <- function(path)list(path=path,sha256=digest(file=path,algo="sha256"))
result <- list(status="PASS",checked_at=format(Sys.time(),"%Y-%m-%dT%H:%M:%S%z"),
  predicate="Regular + abstract Final + coded F + detailed Final or Completed Early; distinct gamePk",
  synthetic_cases=lapply(cases,function(x)list(expected=x$expected,observed=predicate(x$game))),
  schedule_counts=results,status_combinations=rbindlist(status_tables),actual_2020_game_ids_match=TRUE,
  inputs=lapply(c(runner,paths,input),metadata))
write_json(result,"columns/001-ball-count/analysis/runs/bcai_history__mlb_2020__20260928__r02/schedule_check.json",pretty=TRUE,auto_unbox=TRUE,digits=NA)
cat("PASS: nine status cases; archived 2020-2025 schedules; 898 played 2020 games match CSV\n")
