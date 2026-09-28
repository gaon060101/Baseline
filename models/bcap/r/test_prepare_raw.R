source("models/bcap/r/prepare_raw.R",encoding="UTF-8")
# API abstract Final also occurs on unplayed postponed games; only completed
# regular-season states pass, including games officially completed early.
game_fixture <- function(coded="F",detail="Final",abstract="Final",type="R")
  list(gameType=type,status=list(abstractGameState=abstract,codedGameState=coded,detailedState=detail))
stopifnot(completed_regular_bcap_game(game_fixture()),
  completed_regular_bcap_game(game_fixture(detail="Completed Early")),
  !completed_regular_bcap_game(game_fixture(coded="D",detail="Postponed")),
  !completed_regular_bcap_game(game_fixture(coded="C",detail="Cancelled")),
  !completed_regular_bcap_game(game_fixture(abstract="Live")),
  !completed_regular_bcap_game(game_fixture(coded="F",detail="Suspended")),
  !completed_regular_bcap_game(game_fixture(type="S")),
  !completed_regular_bcap_game(game_fixture(detail=NULL)),
  !completed_regular_bcap_game(list(gameType="R")))
make_row <- function(pa,pitch=1L,balls=0L,strikes=0L,event="single",description="hit_into_play",pitch_type="FF",year=2024L) {
  data.table(game_pk=100+year,at_bat_number=pa,pitch_number=pitch,game_date=paste0(year,"-06-01"),game_type="R",game_year=year,
    balls=balls,strikes=strikes,pitcher=10L,batter=20L,events=event,description=description,pitch_type=pitch_type,
    pitch_name="synthetic",des="synthetic test",stand="R",p_throws="L",on_1b=NA_real_,on_2b=NA_real_,on_3b=NA_real_,
    outs_when_up=0L,inning=1L,bat_score_diff=0L,release_speed=95,pfx_x=.1,pfx_z=.2,plate_x=0,plate_z=2.5,sz_top=3.5,sz_bot=1.5)
}
w <- data.table(year=2024L,BB=.7,HBP=.8,`1B`=.9,`2B`=1.2,`3B`=1.6,HR=2)
sch <- data.table(game_pk=2124,year=2024L,venue=1L,official_date="2024-06-01")
fixture <- rbindlist(list(
  make_row(1,1,event=NA_character_,description="ball"),
  make_row(1,2,balls=1,event=NA_character_,description="automatic_ball",pitch_type=NA_character_),
  make_row(1,3,balls=2,event="walk",description="ball",pitch_type="SL"),
  make_row(2,1,event="single"),make_row(2,2,strikes=1,event=NA_character_,description="foul"),
  make_row(3,event="intent_walk"),make_row(4,event="catcher_interf"),make_row(5,event="truncated_pa"),
  make_row(6,event="not_known"),make_row(7,balls=1),make_row(8,event="hit_by_pitch",description="hit_by_pitch"),
  make_row(9,event="strikeout",description="missed_bunt",pitch_type="FA"),
  make_row(10,event="single",pitch_type="ZZ"),make_row(11,event="single",description="unknown"),
  make_row(12,event="single",description="pitchout",pitch_type="PO")))
result <- prepare_bcap_raw(fixture,w,sch); d <- result$data
stopifnot(result$audit$all_PA==12,result$audit$eligible_PA==6,
  d[at_bat_number==1 & pitch_number==3]$prev_description=="automatic_ball",
  d[at_bat_number==1 & pitch_number==3]$prev_pitch_group=="MISSING_PREVIOUS",
  all(d[at_bat_number==2]$pa_exclusion=="missing_final"),all(is.na(d[at_bat_number==2]$Y)),
  d[at_bat_number==8]$A_swing==0,d[at_bat_number==9]$A_swing==1,d[at_bat_number==9]$A_pitch==0,
  d[at_bat_number==10]$reason_pitch=="unmapped_pitch_type",d[at_bat_number==11]$reason_swing=="unmapped_description",
  d[at_bat_number==12]$reason_swing=="pitchout",all(d[at_bat_number==1]$Y==.7),
  result$audit$checks$missing_last_event_with_earlier_nonnull_PA==1,
  all(d[pitch_number==1]$prev_pitch_group=="START"))
stopifnot(isTRUE(all.equal(as.data.frame(d),as.data.frame(prepare_bcap_raw(fixture[.N:1],w,sch)$data))))
expect_error <- function(expr) stopifnot(inherits(tryCatch({force(expr);NULL},error=identity),"error"))
expect_error(prepare_bcap_raw(rbind(fixture,fixture[1]),w,sch))
expect_error(prepare_bcap_raw(fixture,w[0],sch))
bad <- copy(fixture); bad[1,balls:=4];expect_error(prepare_bcap_raw(bad,w,sch))
expect_error(prepare_bcap_raw(fixture,w,sch[0]))
# Schedule aliases may repeat a game only when all numerical metadata agrees.
same_schedule <- rbind(copy(sch)[,cutoff:="2024-12-31"],copy(sch)[,cutoff:="2024-12-31"])
same_result <- prepare_bcap_raw(fixture,w,same_schedule)
stopifnot(isTRUE(all.equal(as.data.frame(d),as.data.frame(same_result$data))),
  same_result$audit$schedule_normalization$records_before==2,
  same_result$audit$schedule_normalization$unique_games==1,
  same_result$audit$schedule_normalization$identical_records_removed==1,
  nrow(same_result$tables$schedule_duplicates)==1)
for (field in c("year","venue","official_date","cutoff")) {
  conflict <- copy(same_schedule)
  changed <- switch(field,year=2025L,venue=2L,official_date="2024-06-02",cutoff="2024-12-30")
  set(conflict,i=2L,j=field,value=changed)
  expect_error(prepare_bcap_raw(fixture,w,conflict,"reject"))
  if(field!="venue") expect_error(prepare_bcap_raw(fixture,w,conflict,"legacy_last_schedule_record"))
}
# The legacy default resolves a venue-only conflict, in retained file
# order (not venue magnitude or a new date sort), with every record audited.
venue_aliases <- rbind(copy(sch)[,venue:=9L],copy(sch)[,venue:=2L],copy(sch)[,venue:=2L])
resolved <- prepare_bcap_raw(fixture,w,venue_aliases,"legacy_last_schedule_record")
default_resolved <- prepare_bcap_raw(fixture,w,venue_aliases)
stopifnot(all(default_resolved$data$venue==2L),
  !default_resolved$audit$schedule_normalization$venue_policy_explicit,
  resolved$audit$schedule_normalization$venue_policy_explicit)
expect_error(prepare_bcap_raw(fixture,w,venue_aliases,"reject"))
stopifnot(all(resolved$data$venue==2L),resolved$audit$schedule_normalization$conflicting_games==1L,
  resolved$audit$schedule_normalization$venue_conflicts_resolved==1L,
  resolved$audit$schedule_normalization$identical_records_removed==1L,
  nrow(resolved$tables$schedule_venue_conflicts)==3L,
  identical(resolved$tables$schedule_venue_conflicts$selected_schedule_record,c(FALSE,FALSE,TRUE)),
  all(resolved$tables$schedule_venue_conflicts$selected_venue==2L))
reverse_resolved <- prepare_bcap_raw(fixture,w,venue_aliases[.N:1],"legacy_last_schedule_record")
stopifnot(all(reverse_resolved$data$venue==9L))
expect_error(prepare_bcap_raw(fixture,w,sch,"guess"))
# Geometry includes equality and keeps the old boundary region separate from S/B.
geometry <- rbindlist(lapply(1:6,make_row))
geometry[,plate_x:=c(17/24,17/24+.01,0,0,NA_real_,0)]
geometry[,plate_z:=c(2.5,2.5,3.5,3.5001,2.5,2.5)]
geometry[6,sz_top:=sz_bot]
gd <- prepare_bcap_raw(geometry,w,sch)$data
stopifnot(identical(gd$A_pitch_sb,c(1L,0L,1L,0L,NA_integer_,NA_integer_)),
  all(gd$zone[1:4]=="BOUNDARY"),all(!gd$eligible_pitch_sb[5:6]))
# Numeric category string labels match historical pandas preparation.
bins <- rbindlist(lapply(1:6,function(i) make_row(i)))
bins[,bat_score_diff:=c(-4,-1,0,3,4,NA_real_)];bins[1,`:=`(inning=11,on_1b=2,on_3b=3,stand=NA_character_)]
bd <- prepare_bcap_raw(bins,w,sch)$data
stopifnot(identical(bd$score_bin,c("trailing4+","trailing1-3","tie","leading1-3","leading4+","nan")),
  bd$base_state[1]==5,bd$inning_bin[1]==10,bd$matchup[1]=="?L")
# Explicit year weights; 2015 measurement marker and 2026 geometry withholding.
historic <- rbind(make_row(1,year=2015),make_row(1,year=2026))
hw <- rbind(copy(w)[,year:=2015L],copy(w)[,`:=`(year=2026L,`1B`=1.1)])
hs <- data.table(game_pk=c(2115,2126),year=c(2015L,2026L),venue=1L,official_date=c("2015-06-01","2026-06-01"))
hd <- prepare_bcap_raw(historic,hw,hs)$data
stopifnot(identical(hd$Y,c(.9,1.1)),hd$speed_measurement_regime[1]=="PITCHf/x adjusted",
  hd$zone[2]=="WITHHELD_2026",is.na(hd$A_pitch_sb[2]),!hd$eligible_pitch_sb[2],hd$eligible_swing[2])
# A copied source must record and freeze itself, not the mutable repository file.
local({
  sandbox <- tempfile("bcap_prepare_source_"); dir.create(sandbox)
  on.exit(unlink(sandbox,recursive=TRUE),add=TRUE)
  source_copy <- file.path(sandbox,"execution_snapshot.R")
  stopifnot(file.copy(BCAP_PREP_SCRIPT$path,source_copy))
  env <- new.env(parent=globalenv()); source(source_copy,local=env,encoding="UTF-8")
  stopifnot(identical(env$BCAP_PREP_SCRIPT$path,normalizePath(source_copy,winslash="/")))
  raw_path <- file.path(sandbox,"raw.csv"); fwrite(fixture,raw_path,na="")
  schedule_path <- file.path(sandbox,"schedule.json")
  g <- game_fixture();g$gamePk <- 2124;g$officialDate <- "2024-06-01";g$venue <- list(id=1)
  jsonlite::write_json(list(dates=list(list(games=list(g)))),schedule_path,auto_unbox=TRUE)
  config <- list(input_csv=list(raw_path),years=list(2024L),
    seasons=list(list(year=2024L,schedule=schedule_path,cutoff="2024-12-31")),
    weights=list(as.list(w[1])),output_rds=file.path(sandbox,"prepared.rds"),audit_dir=file.path(sandbox,"audit"))
  config_path <- file.path(sandbox,"config.json"); jsonlite::write_json(config,config_path,auto_unbox=TRUE)
  audit <- env$prepare_bcap_files(config_path)
  stopifnot(identical(audit$code$path,normalizePath(source_copy,winslash="/")),
    identical(audit$code$sha256,audit$frozen_code$sha256),
    identical(audit$code$sha256,env$BCAP_PREP_SCRIPT$sha256),
    !audit$schedule_normalization$venue_policy_explicit,
    identical(audit$schedule_normalization$venue_policy,"legacy_last_schedule_record"))
  expect_error(env$prepare_bcap_files(config_path))
  cat("\n# changed after load\n",file=source_copy,append=TRUE)
  expect_error(env$prepare_bcap_files(config_path))
})
cat("PASS BCAP raw R: completed schedule states, immutable execution source, exclusions, terminal event, lag before filtering, closed labels, geometry edges, categories, year weights, schedule aliases/conflicts and 2026 gate\n")
