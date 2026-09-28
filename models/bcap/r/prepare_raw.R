# BCAP historical raw preparation. Statistical fitting is performed by engine.R.
# Source this file for pure prepare_bcap_raw(); Rscript prepare_raw.R config.json for I/O.
suppressPackageStartupMessages(library(data.table))
# Capture the file actually loaded, including a frozen execution copy or source().
BCAP_PREP_SCRIPT <- local({
  sourced <- unlist(lapply(sys.frames(),function(frame) frame$ofile),use.names=FALSE)
  entry <- grep("^--file=",commandArgs(trailingOnly=FALSE),value=TRUE)
  path <- if (length(sourced)) tail(sourced,1L) else if (length(entry)) sub("^--file=","",entry[1L]) else NA_character_
  if (is.na(path) || !file.exists(path)) list(path=NA_character_,sha256=NA_character_) else {
    path <- normalizePath(path,winslash="/",mustWork=TRUE)
    list(path=path,sha256=if (requireNamespace("digest",quietly=TRUE)) digest::digest(file=path,algo="sha256") else NA_character_)
  }
})
BCAP_RAW_KEYS <- c("game_pk", "at_bat_number", "pitch_number")
BCAP_RAW_FIELDS <- c(BCAP_RAW_KEYS, "game_date", "game_type", "game_year", "balls", "strikes",
  "pitcher", "batter", "events", "description", "pitch_type", "pitch_name", "des", "stand",
  "p_throws", "on_1b", "on_2b", "on_3b", "outs_when_up", "inning", "bat_score_diff",
  "release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "sz_top", "sz_bot")
BCAP_RAW_FB <- c("FF", "SI", "FC")
BCAP_RAW_NFB <- c("SL", "CH", "ST", "CU", "FS", "KC", "SV", "FA", "EP", "KN", "FO", "CS", "SC")
BCAP_RAW_SWING <- c("swinging_strike", "swinging_strike_blocked", "foul", "foul_tip",
  "hit_into_play", "foul_bunt", "missed_bunt", "bunt_foul_tip")
BCAP_RAW_TAKE <- c("ball", "blocked_ball", "called_strike", "hit_by_pitch")
BCAP_RAW_EVENTS <- c(single="1B", double="2B", triple="3B", home_run="HR", walk="BB",
  hit_by_pitch="HBP", strikeout="K", strikeout_double_play="K", field_out="OUT", force_out="OUT",
  grounded_into_double_play="OUT", double_play="OUT", fielders_choice_out="OUT", sac_fly="OUT",
  sac_bunt="OUT", sac_fly_double_play="OUT", sac_bunt_double_play="OUT", triple_play="OUT",
  field_error="OTHER", fielders_choice="OTHER")

completed_regular_bcap_game <- function(g) {
  identical(g$gameType,"R") && identical(g$status$abstractGameState,"Final") &&
    identical(g$status$codedGameState,"F") && isTRUE(g$status$detailedState %in% c("Final","Completed Early"))
}

normalize_bcap_schedule <- function(schedule_games,venue_policy="legacy_last_schedule_record") {
  if (!is.character(venue_policy) || length(venue_policy)!=1L || is.na(venue_policy) ||
      !venue_policy %in% c("reject","legacy_last_schedule_record")) stop("Unknown schedule venue policy")
  sg <- copy(as.data.table(schedule_games))
  required <- c("game_pk","year","venue","official_date")
  if (!all(required %in% names(sg)) || !nrow(sg)) stop("Invalid schedule index")
  if (any(!is.finite(sg$game_pk) | sg$game_pk<=0 | sg$game_pk!=floor(sg$game_pk)) ||
      any(!is.finite(sg$year) | sg$year!=floor(sg$year)) ||
      any(!is.finite(sg$venue) | sg$venue<=0) || anyNA(sg$official_date)) stop("Invalid schedule metadata")
  metadata <- c(required,intersect("cutoff",names(sg)))
  value_fields <- setdiff(metadata,"game_pk")
  variants <- sg[,.(variants=uniqueN(.SD)),by=game_pk,.SDcols=value_fields]
  conflicts <- variants[variants>1L]$game_pk
  invariant_fields <- setdiff(value_fields,"venue")
  invariant_variants <- sg[,.(variants=uniqueN(.SD)),by=game_pk,.SDcols=invariant_fields]
  if (any(invariant_variants$variants>1L) || (length(conflicts) && venue_policy=="reject"))
    stop("Conflicting schedule records for the same game_pk")
  duplicates <- sg[,.(records=.N,duplicate_records_removed=.N-1L),by=metadata][records>1L]
  # Python data.py uses a dict comprehension over the archived schedule order.
  # Preserve that BCAP definition by default; callers may require strict reject.
  normalized <- unique(sg[,..metadata],by="game_pk",fromLast=TRUE)
  sg[,normalization_record_order:=seq_len(.N)]
  sg[,selected_schedule_record:=normalization_record_order==max(normalization_record_order),by=game_pk]
  sg[,selected_venue:=venue[.N],by=game_pk]
  venue_conflicts <- sg[game_pk %in% conflicts]
  venue_conflicts[,resolution_policy:=venue_policy]
  list(games=normalized,duplicates=duplicates,venue_conflicts=venue_conflicts,
    audit=list(records_before=nrow(sg),unique_games=nrow(normalized),
      duplicated_games=sg[,.N,by=game_pk][N>1L,.N],
      records_removed=nrow(sg)-nrow(normalized),
      identical_records_removed=nrow(sg)-nrow(unique(sg[,..metadata])),
      conflicting_games=length(conflicts),venue_conflicts_resolved=length(conflicts),
      venue_policy=venue_policy,compared_fields=metadata,
      venue_note="Legacy policy assigns the last retained archived schedule venue to every row of a game; it does not reconstruct pitch-level venues for suspended games."))
}

prepare_bcap_raw <- function(raw, weights, schedule_games,schedule_venue_policy="legacy_last_schedule_record") {
  venue_policy_explicit <- !missing(schedule_venue_policy)
  d <- copy(as.data.table(raw))
  if (!all(BCAP_RAW_FIELDS %in% names(d))) stop(paste("Missing raw fields:", paste(setdiff(BCAP_RAW_FIELDS,names(d)),collapse=", ")))
  if (!nrow(d)) stop("Empty raw input")
  d <- d[, ..BCAP_RAW_FIELDS]
  strings <- c("game_date","game_type","events","description","pitch_type","pitch_name","des","stand","p_throws")
  for (field in strings) {
    x <- as.character(d[[field]]); x[x==""] <- NA_character_; set(d,j=field,value=x)
  }
  integers <- c(BCAP_RAW_KEYS,"game_year","balls","strikes","pitcher","batter")
  for (field in integers) {
    x <- suppressWarnings(as.numeric(d[[field]]))
    if (any(!is.finite(x) | x!=floor(x))) stop(paste("Invalid integer field",field))
    set(d,j=field,value=x)
  }
  for (field in setdiff(BCAP_RAW_FIELDS,c(strings,integers))) {
    old <- d[[field]]; x <- suppressWarnings(as.numeric(as.character(old)))
    if (any(!is.na(old) & is.na(x))) stop(paste("Invalid numeric field",field))
    set(d,j=field,value=x)
  }
  if (any(d$game_year < 2015 | d$game_year > 2026)) stop("This preparation is scoped to 2015-2026")
  if (anyNA(d$game_type) || any(d$game_type!="R")) stop("Only regular-season rows are allowed")
  if (anyNA(d$game_date) || any(substr(d$game_date,1,4)!=as.character(d$game_year))) stop("Invalid game dates")
  if (any(d$balls<0 | d$balls>3 | d$strikes<0 | d$strikes>2)) stop("Invalid pre-pitch count")
  if (any(d$game_pk<=0 | d$at_bat_number<=0 | d$pitch_number<=0 | d$pitcher<=0 | d$batter<=0)) stop("Nonpositive identifier")
  if (anyDuplicated(d[, ..BCAP_RAW_KEYS])) stop("Duplicate pitch keys")
  if (any(d[, uniqueN(game_year),by=game_pk]$V1!=1L)) stop("Game spans years")
  w <- copy(as.data.table(weights)); weight_events <- c("BB","HBP","1B","2B","3B","HR")
  if (!all(c("year",weight_events)%in%names(w)) || anyDuplicated(w$year) || !setequal(w$year,unique(d$game_year))) stop("Weights must match every input year exactly")
  wm <- as.matrix(w[, ..weight_events])
  if (!is.numeric(wm) || any(!is.finite(wm) | wm<=0)) stop("Invalid external weights")
  schedule_normalization <- normalize_bcap_schedule(schedule_games,schedule_venue_policy)
  schedule_normalization$audit$venue_policy_explicit <- venue_policy_explicit
  sg <- schedule_normalization$games
  if (!setequal(sg$game_pk,unique(d$game_pk))) stop("Scheduled and observed game sets differ")
  if (any(!is.finite(sg$venue) | sg$venue<=0) || anyNA(sg$official_date)) stop("Missing schedule venue/date")
  schedule_index <- match(d$game_pk,sg$game_pk)
  if (any(d$game_year!=sg$year[schedule_index])) stop("Schedule year mismatch")

  setorderv(d,BCAP_RAW_KEYS)
  d[, count:=paste(balls,strikes,sep="-")]
  d[, pa_id:=.GRP-1L,by=.(game_pk,at_bat_number)]
  d[, row_id:=seq_len(.N)-1L]
  pa <- d[, .(game_pk=game_pk[1],at_bat_number=at_bat_number[1],pitch_number=pitch_number[1],
    game_year=game_year[1],game_date=game_date[1],count=count[1],final_event=events[.N]),by=pa_id]
  pa[, result:=unname(BCAP_RAW_EVENTS[final_event])]
  pa[, pa_exclusion:=fcase(is.na(final_event),"missing_final",final_event=="intent_walk","intentional_walk",
    final_event=="catcher_interf","catcher_interference",final_event=="truncated_pa","truncated",
    is.na(result),"unknown_event",count!="0-0","no_observed_0_0",default="included")]
  pa[, Y:=ifelse(pa_exclusion=="included",0.0,NA_real_)]
  for (yy in w$year) for (ev in weight_events) pa[game_year==yy & result==ev & pa_exclusion=="included",Y:=w[year==yy][[ev]]]
  pos <- match(d$pa_id,pa$pa_id)
  for (field in c("final_event","result","pa_exclusion","Y")) set(d,j=field,value=pa[[field]][pos])
  d[, eligible_pa:=pa_exclusion=="included"]
  pos <- match(d$game_pk,sg$game_pk)
  d[, `:=`(venue=sg$venue[pos],official_date=as.character(sg$official_date[pos]),
    matchup=paste0(fifelse(is.na(stand),"?",stand),fifelse(is.na(p_throws),"?",p_throws)),
    base_state=as.integer(!is.na(on_1b))+2L*as.integer(!is.na(on_2b))+4L*as.integer(!is.na(on_3b)),
    inning_bin=pmin(inning,10),pitch_number_bin=pmin(pitch_number,8))]
  d[, score_bin:=fcase(is.na(bat_score_diff),"nan",bat_score_diff<= -4,"trailing4+",
    bat_score_diff<= -1,"trailing1-3",bat_score_diff<=0,"tie",bat_score_diff<=3,"leading1-3",default="leading4+")]
  # Shift all observed rows BEFORE current-row action exclusions, within each PA.
  d[, `:=`(prev_pitch_number=shift(pitch_number),prev_pitch_type=shift(pitch_type),
    prev_description=shift(description),prev_release_speed=shift(release_speed)),by=pa_id]
  is_first <- !duplicated(d$pa_id)
  d[is.na(prev_pitch_type),prev_pitch_type:="MISSING_PREVIOUS"]
  d[is.na(prev_description),prev_description:="MISSING_PREVIOUS"]
  prev_bin <- rep("<NA>",nrow(d)); good <- is.finite(d$prev_release_speed)
  prev_bin[good] <- as.character(floor(d$prev_release_speed[good]/5))
  d[, prev_release_speed_bin:=prev_bin]
  for (field in c("prev_pitch_type","prev_description","prev_release_speed_bin")) set(d,i=which(is_first),j=field,value="START")
  group_map <- c(setNames(rep("FB",length(BCAP_RAW_FB)),BCAP_RAW_FB),setNames(rep("NFB",length(BCAP_RAW_NFB)),BCAP_RAW_NFB))
  d[, pitch_group:=unname(group_map[pitch_type])]
  d[is.na(pitch_group),pitch_group:="UNCLASSIFIED"]
  lag_map <- c(group_map,START="START",MISSING_PREVIOUS="MISSING_PREVIOUS")
  d[, prev_pitch_group:=unname(lag_map[prev_pitch_type])]
  d[is.na(prev_pitch_group),prev_pitch_group:="UNCLASSIFIED"]
  automatic <- d$description %in% c("automatic_ball","automatic_strike")
  pitchout <- d$pitch_type %in% "PO" | d$description %in% c("pitchout","swinging_pitchout","foul_pitchout")
  d[, reason_pitch:=fcase(!eligible_pa,"PA_EXCLUDED",automatic,"automatic_record",pitchout,"pitchout",
    is.na(pitch_type),"missing_pitch_type",!pitch_type %in% names(group_map),"unmapped_pitch_type",default="included")]
  d[, A_pitch:=fcase(pitch_type %in% BCAP_RAW_FB,1L,pitch_type %in% BCAP_RAW_NFB,0L,default=NA_integer_)]
  d[automatic | pitchout,A_pitch:=NA_integer_]
  d[, eligible_pitch:=reason_pitch=="included"]
  d[, reason_swing:=fcase(!eligible_pa,"PA_EXCLUDED",automatic,"automatic_record",pitchout,"pitchout",
    is.na(description),"missing_description",!description %in% c(BCAP_RAW_SWING,BCAP_RAW_TAKE),"unmapped_description",default="included")]
  d[, A_swing:=fcase(description %in% BCAP_RAW_SWING,1L,description %in% BCAP_RAW_TAKE,0L,default=NA_integer_)]
  d[automatic | pitchout,A_swing:=NA_integer_]
  d[, eligible_swing:=reason_swing=="included"]
  d[, `:=`(bunt_explicit=description %in% c("foul_bunt","missed_bunt","bunt_foul_tip"),
    inplay_bunt_text_flag=description %in% "hit_into_play" & grepl("\\bbunts?\\b",fifelse(is.na(des),"",des),ignore.case=TRUE),
    hbp_adjudicated_take=description %in% "hit_by_pitch")]
  height <- d$sz_top-d$sz_bot
  geometry <- is.finite(d$plate_x)&is.finite(d$plate_z)&is.finite(d$sz_top)&is.finite(d$sz_bot)&height>0
  zn <- rep(NA_real_,nrow(d)); zn[geometry] <- (d$plate_z[geometry]-d$sz_bot[geometry])/height[geometry]
  comparable <- d$game_year<=2025
  inner <- geometry & abs(d$plate_x)<=17/24-.15 & zn>=.1 & zn<=.9
  outside <- geometry & (abs(d$plate_x)>17/24+.15 | zn< -.1 | zn>1.1)
  zone <- fcase(!comparable,"WITHHELD_2026",!geometry,"MISSING",inner,"INNER",outside,"OUT",default="BOUNDARY")
  inside <- geometry & abs(d$plate_x)<=17/24 & d$plate_z>=d$sz_bot & d$plate_z<=d$sz_top
  d[, `:=`(zone_z_normalized=fifelse(comparable,zn,NA_real_),zone=zone,geometry_comparable=comparable,
    A_pitch_sb=fifelse(geometry & comparable,as.integer(inside),NA_integer_),
    eligible_pitch_sb=eligible_pitch & geometry & comparable,
    reason_pitch_sb=fcase(!eligible_pitch,reason_pitch,!comparable,"geometry_regime_withheld",!geometry,"invalid_geometry",default="included"))]
  measure <- c("release_speed","pfx_x","pfx_z","plate_x","plate_z","sz_top","sz_bot")
  d[, measurement_missing:=!Reduce(`&`,lapply(.SD,is.finite)),.SDcols=measure]
  d[, speed_measurement_regime:=fifelse(game_year<=2016,"PITCHf/x adjusted","Statcast")]
  d[, pitch_sequence_gap_before:=!is_first & pitch_number!=prev_pitch_number+1]
  known <- paste(d$game_pk,d$at_bat_number,d$pitch_number,sep="|") %in% c("746664|63|6","778541|42|6")
  d[, known_count_exception:=known]
  next_same <- d$pa_id==shift(d$pa_id,type="lead",fill=-1)
  db <- shift(d$balls,type="lead")-d$balls; ds <- shift(d$strikes,type="lead")-d$strikes
  anomalies <- next_same & !((db==1 & ds==0)|(db==0 & ds==1)|(db==0 & ds==0))
  pa_checks <- d[, .(nonmissing_events=sum(!is.na(events)),distinct_events=uniqueN(events,na.rm=TRUE),
    last_missing=is.na(events[.N]),pitchers=uniqueN(pitcher),batters=uniqueN(batter),ys=uniqueN(Y,na.rm=TRUE)),by=pa_id]
  checks <- list(duplicate_pitch_keys=0L,invalid_counts=0L,first_pitch_number_not_one_PA=sum(pa$pitch_number!=1),
    pitch_sequence_gaps=sum(d$pitch_sequence_gap_before),nonmonotonic_pitch_numbers=sum(!is_first & d$pitch_number<=d$prev_pitch_number,na.rm=TRUE),
    count_transition_anomalies=sum(anomalies),multiple_nonnull_events_PA=sum(pa_checks$nonmissing_events>1),
    multiple_distinct_nonnull_events_PA=sum(pa_checks$distinct_events>1),
    missing_last_event_with_earlier_nonnull_PA=sum(pa_checks$last_missing & pa_checks$nonmissing_events>0),
    PA_multiple_pitchers=sum(pa_checks$pitchers>1),PA_multiple_batters=sum(pa_checks$batters>1),
    prev_features_first_row_clear=all(is.na(d$prev_release_speed[is_first])),Y_constant_within_PA=all(pa_checks$ys<=1),
    eligible_pitch_label_complete=all(d$A_pitch[d$eligible_pitch] %in% 0:1),
    eligible_swing_label_complete=all(d$A_swing[d$eligible_swing] %in% 0:1),
    eligible_pitch_sb_label_complete=all(d$A_pitch_sb[d$eligible_pitch_sb] %in% 0:1))
  reason_counts <- function(x) as.list(setNames(as.integer(table(x)),names(table(x))))
  audit <- list(raw_rows=nrow(d),all_PA=nrow(pa),games=uniqueN(d$game_pk),eligible_PA=sum(pa$pa_exclusion=="included"),
    eligible_pitch_rows=sum(d$eligible_pitch),eligible_swing_rows=sum(d$eligible_swing),eligible_pitch_sb_rows=sum(d$eligible_pitch_sb),
    PA_exclusions=reason_counts(pa$pa_exclusion),pitch_exclusions=reason_counts(d$reason_pitch),
    swing_exclusions=reason_counts(d$reason_swing),pitch_sb_exclusions=reason_counts(d$reason_pitch_sb),checks=checks,
    weights=w,schedule_normalization=schedule_normalization$audit,
    geometry_2026="WITHHELD: S/B masked; raw SWING label eligibility retained for audit only; runner must withhold SWING",
    measurement_note="2015/2016 release_speed uses adjusted PITCHf/x; 2017+ Statcast. Historical physical-bin comparability is not verified.",
    coverage_note="Schedule game-set equality does not certify every pitch or PA is present.",
    category_note="Character labels preserved; nuisance feature dictionaries must be learned inside training folds only.")
  tables <- list(schedule_duplicates=schedule_normalization$duplicates,
    schedule_venue_conflicts=schedule_normalization$venue_conflicts,
    pa_index=pa,pa_exclusions=pa[,.(PA=.N),by=.(game_year,final_event,result,pa_exclusion)],
    raw_pitch_codes=d[,.(rows=.N),by=.(game_year,pitch_type,pitch_name)],
    description_action_audit=d[,.(rows=.N),by=.(game_year,description,A_swing,reason_swing)],
    sequence_anomalies=d[which(anomalies | pitch_sequence_gap_before),c(BCAP_RAW_KEYS,"count","description","prev_pitch_number","pitch_sequence_gap_before"),with=FALSE],
    selection_counts=rbindlist(lapply(c("pitch","pitch_sb","swing"),function(m) {
      tab <- d[,.(rows=.N,PA=uniqueN(pa_id),games=uniqueN(game_pk)),by=c("game_year",paste0("reason_",m))]
      setnames(tab,paste0("reason_",m),"reason"); tab[,model:=m]; tab
    })),
    missingness=rbindlist(lapply(setdiff(BCAP_RAW_FIELDS,"des"),function(f) d[,.(field=f,rows=.N,missing=sum(is.na(get(f)))),by=game_year])))
  d[,des:=NULL]
  list(data=d,audit=audit,tables=tables)
}

prepare_bcap_files <- function(config_path) {
  if (!requireNamespace("jsonlite",quietly=TRUE) || !requireNamespace("digest",quietly=TRUE)) stop("jsonlite and digest are required")
  preparation_script <- BCAP_PREP_SCRIPT$path
  if (is.na(preparation_script) || !file.exists(preparation_script) ||
      !identical(BCAP_PREP_SCRIPT$sha256,digest::digest(file=preparation_script,algo="sha256")))
    stop("The actual preparation script is unavailable or changed after loading")
  cfg <- jsonlite::fromJSON(config_path,simplifyVector=FALSE)
  venue_policy <- if(is.null(cfg$schedule_venue_policy)) "legacy_last_schedule_record" else cfg$schedule_venue_policy
  inputs <- unlist(cfg$input_csv); years <- as.integer(unlist(cfg$years))
  if (!length(inputs)||anyDuplicated(inputs)||!length(years)||anyDuplicated(years)) stop("Explicit unique input files and years required")
  if (!setequal(years,vapply(cfg$seasons,function(s) as.integer(s$year),integer(1)))) stop("Season definitions mismatch")
  targets <- c(cfg$output_rds,cfg$output_csv,cfg$audit_dir)
  if (is.null(cfg$output_rds)||is.null(cfg$audit_dir)||anyNA(targets)||any(targets=="")) stop("output_rds and audit_dir required")
  norm <- gsub("\\\\","/",normalizePath(targets,mustWork=FALSE))
  if (any(grepl("(^|/)data/raw(/|$)",tolower(norm)))) stop("Preparation cannot write inside raw-data folders")
  if (any(file.exists(targets)|dir.exists(targets))) stop("Preparation outputs already exist; choose new paths")
  source_paths <- unique(c(inputs,config_path,preparation_script,vapply(cfg$seasons,function(s) s$schedule,character(1)),cfg$weights_source,cfg$source_notes))
  if (!all(file.exists(source_paths))) stop("Missing source files")
  meta <- function(path) list(path=path,sha256=digest::digest(file=path,algo="sha256"),bytes=unname(file.info(path)$size))
  before <- lapply(source_paths,meta)
  schedules <- rbindlist(lapply(cfg$seasons,function(s) {
    if (is.null(s$cutoff)||!grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}$",s$cutoff)) stop("Explicit season cutoff required")
    sch <- jsonlite::fromJSON(s$schedule,simplifyVector=FALSE)
    games <- unlist(lapply(sch$dates,function(day) lapply(day$games,function(g) {
      g$archive_schedule_date <- day$date;g
    })),recursive=FALSE)
    for(i in seq_along(games)) games[[i]]$archive_record_index <- i
    games <- Filter(function(g) completed_regular_bcap_game(g) &&
      g$officialDate<=s$cutoff && substr(g$officialDate,1,4)==as.character(s$year),games)
    if (!length(games)) stop("No scheduled regular-season games")
    chr <- function(x) if(is.null(x))NA_character_ else as.character(x)
    rbindlist(lapply(games,function(g) data.table(game_pk=as.numeric(g$gamePk),year=as.integer(s$year),
      venue=as.numeric(g$venue$id),official_date=g$officialDate,cutoff=s$cutoff,
      schedule_source=s$schedule,schedule_record_index=g$archive_record_index,
      schedule_date=chr(g$archive_schedule_date),game_date=chr(g$gameDate),venue_name=chr(g$venue$name),
      resume_date=chr(g$resumeDate),resumed_from=chr(g$resumedFrom),description=chr(g$description),
      coded_state=chr(g$status$codedGameState),detailed_state=chr(g$status$detailedState))))
  }))
  # Postponed/resumed aliases may repeat a game in the archived API response.
  # Remove only identical numerical metadata, and fail before CSV reads on conflict.
  schedule_validation <- normalize_bcap_schedule(schedules,venue_policy)
  parts <- lapply(inputs,function(path) {
    header <- names(fread(path,nrows=0))
    if (!all(BCAP_RAW_FIELDS %in% header)) stop(paste("Missing required raw fields:",path))
    fread(path,select=BCAP_RAW_FIELDS,na.strings=c("","NA"),encoding="UTF-8")
  })
  raw <- rbindlist(parts,use.names=TRUE); rm(parts); gc(FALSE)
  if (!setequal(unique(raw$game_year),years)) stop("Input years differ from config")
  idx <- match(raw$game_pk,schedule_validation$games$game_pk)
  if (anyNA(idx)||any(as.character(raw$game_date)>schedule_validation$games$cutoff[idx])) stop("Unscheduled or after-cutoff raw rows")
  result <- prepare_bcap_raw(raw,rbindlist(cfg$weights),schedules,venue_policy); rm(raw); gc(FALSE)
  result$audit$schedule_normalization$venue_policy_explicit <- !is.null(cfg$schedule_venue_policy)
  result$audit$schedule_normalization$venue_policy_default_reason <- "Preserve models/bcap/data.py dictionary last-occurrence game-level venue assignment; no pitch-level relocation reconstruction."
  unchanged <- vapply(before,function(x) identical(x$sha256,digest::digest(file=x$path,algo="sha256")),logical(1))
  if (!all(unchanged)) stop("A preparation input changed while reading")
  dir.create(dirname(cfg$output_rds),recursive=TRUE,showWarnings=FALSE)
  dir.create(cfg$audit_dir,recursive=TRUE,showWarnings=FALSE)
  frozen_code <- file.path(cfg$audit_dir,"frozen_prepare_raw.R")
  if (!file.copy(preparation_script,frozen_code,overwrite=FALSE)) stop("Could not preserve preparation code")
  if (!identical(digest::digest(file=frozen_code,algo="sha256"),BCAP_PREP_SCRIPT$sha256)) stop("Frozen preparation code differs from executed code")
  setattr(result$data,"preparation_manifest",file.path(cfg$audit_dir,"preparation_audit.json"))
  saveRDS(result$data,cfg$output_rds,compress=FALSE)
  if (!is.null(cfg$output_csv)) {
    dir.create(dirname(cfg$output_csv),recursive=TRUE,showWarnings=FALSE)
    fwrite(result$data,cfg$output_csv,na="__BCAP_NA__",bom=TRUE)
  }
  for (nm in names(result$tables)) fwrite(result$tables[[nm]],file.path(cfg$audit_dir,paste0(nm,".csv")),na="__BCAP_NA__",bom=TRUE)
  result$audit$status <- "PASS"; result$audit$years <- years
  result$audit$inputs <- before; result$audit$outputs <- lapply(c(cfg$output_rds,cfg$output_csv),meta)
  result$audit$code <- meta(preparation_script)
  result$audit$frozen_code <- meta(frozen_code)
  result$audit$completed_at <- format(Sys.time(),"%Y-%m-%dT%H:%M:%S%z")
  result$audit$schedule <- schedule_validation$games[,.(games=.N,first=min(official_date),last=max(official_date),cutoff=cutoff[1]),by=year]
  result$audit$schedule_completion_filter <- "gameType=R; abstractGameState=Final; codedGameState=F; detailedState in {Final, Completed Early}; explicit year/cutoff"
  jsonlite::write_json(result$audit,file.path(cfg$audit_dir,"preparation_audit.json"),pretty=TRUE,auto_unbox=TRUE,na="null",digits=NA)
  cat("PASS BCAP R preparation:",nrow(result$data),"rows;",result$audit$eligible_PA,"eligible PA\n")
  invisible(result$audit)
}

if (sys.nframe()==0L) {
  args <- commandArgs(trailingOnly=TRUE)
  if (length(args)!=1L) stop("Usage: Rscript prepare_raw.R config.json (from repository root)")
  prepare_bcap_files(args[1])
}
