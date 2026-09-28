# BCAI-OBS-v1.0.0 R implementation. No I/O at source time.
suppressPackageStartupMessages(library(data.table))
COUNTS <- as.vector(t(outer(0:3, 0:2, paste, sep="-")))
EVENT_MAP <- c(single="1B", double="2B", triple="3B", home_run="HR", walk="BB",
  hit_by_pitch="HBP", strikeout="K", strikeout_double_play="K", field_out="OUT",
  force_out="OUT", grounded_into_double_play="OUT", double_play="OUT",
  fielders_choice_out="OUT", sac_fly="OUT", sac_bunt="OUT", sac_fly_double_play="OUT",
  sac_bunt_double_play="OUT", triple_play="OUT", field_error="OTHER", fielders_choice="OTHER")
WEIGHT_EVENTS <- c("BB", "HBP", "1B", "2B", "3B", "HR")

prepare_bcai <- function(pitches, weights) {
  d <- copy(as.data.table(pitches))
  required <- c("game_pk", "at_bat_number", "pitch_number", "game_year", "balls", "strikes", "events")
  if (!all(required %in% names(d))) stop("Missing required pitch columns")
  for (field in setdiff(required, "events")) {
    x <- suppressWarnings(as.numeric(d[[field]]))
    if (any(!is.finite(x) | x != floor(x))) stop(paste("Invalid integer field", field))
    set(d, j=field, value=x)
  }
  if (any(d$balls < 0 | d$balls > 3 | d$strikes < 0 | d$strikes > 2)) stop("Invalid pre-pitch count")
  if (any(d$game_pk <= 0 | d$at_bat_number <= 0 | d$pitch_number <= 0)) stop("Invalid pitch key")
  if (anyDuplicated(d[, .(game_pk, at_bat_number, pitch_number)])) stop("Duplicate pitch key")
  if (d[, any(uniqueN(game_year) != 1L), by=game_pk]$V1 |> any()) stop("Game spans multiple years")
  w <- copy(as.data.table(weights))
  if (!all(c("year", WEIGHT_EVENTS) %in% names(w)) || anyDuplicated(w$year)) stop("Invalid weight table")
  if (!setequal(unique(d$game_year), w$year)) stop("Weights must exactly match input years")
  if (any(!is.finite(as.matrix(w[, ..WEIGHT_EVENTS]))) || any(as.matrix(w[, ..WEIGHT_EVENTS]) <= 0)) stop("Invalid weights")
  d[, events := as.character(events)]
  d[is.na(events) | events == "", events := NA_character_]
  setorder(d, game_pk, at_bat_number, pitch_number)
  d[, `:=`(count=paste(balls, strikes, sep="-"), pa_id=.GRP), by=.(game_pk, at_bat_number)]
  pa <- d[, .(game_pk=game_pk[1], game_year=game_year[1], first_count=count[1], event=events[.N]), by=pa_id]
  pa[, result := unname(EVENT_MAP[event])]
  pa[, exclusion := fcase(is.na(event), "missing_final", event == "intent_walk", "intentional_walk",
    event == "catcher_interf", "catcher_interference", event == "truncated_pa", "truncated",
    is.na(result), "unknown_event", first_count != "0-0", "no_observed_0_0", default="included")]
  audit <- pa[, .(PA=.N), by=.(game_year, event, exclusion)]
  p <- pa[exclusion == "included"]
  p[, value := 0.0]
  for (year_value in w$year) {
    for (ev in WEIGHT_EVENTS) {
      p[game_year == year_value & result == ev, value := w[year == year_value][[ev]]]
    }
  }
  if (!setequal(unique(p$game_year), w$year)) stop("Year without eligible plate appearances")
  reached <- merge(unique(d[, .(pa_id, count)]), p[, .(pa_id, game_pk, game_year, result, value)], by="pa_id")
  reached[, ci := match(count, COUNTS)]
  repeated <- nrow(d) - nrow(unique(d[, .(pa_id, count)]))
  season <- reached[, .(N=.N, value=mean(value)), by=.(year=game_year, count, ci)]
  if (nrow(season) != nrow(w) * 12L) stop("Each year must support all 12 counts")
  season[, index := 100 * value / value[count == "0-0"], by=year]
  if (any(!is.finite(season$index))) stop("Nonpositive or invalid baseline")
  setorder(season, year, ci)
  cohorts <- p[, .(eligible_PA=.N, games=uniqueN(game_pk), baseline_value=mean(value)), by=.(year=game_year)]
  cohorts[, mix_weight := eligible_PA / sum(eligible_PA)]
  setorder(cohorts, year)
  combined <- merge(season, cohorts[, .(year, mix_weight)], by="year")[,
    .(index=sum(index * mix_weight), N_PA=sum(N)), by=.(count, ci)]
  setorder(combined, ci)
  events <- reached[, .(N=.N), by=.(count, result)]
  events[, pct := 100 * N / sum(N), by=count]
  matrices <- setNames(lapply(cohorts$year, function(y) {
    tab <- reached[game_year == y, .(n=.N, v=sum(value)), by=.(game_pk, ci)]
    games <- sort(unique(tab$game_pk)); loc <- cbind(match(tab$game_pk, games), tab$ci)
    n <- v <- matrix(0, length(games), 12)
    n[loc] <- tab$n; v[loc] <- tab$v
    list(n=n, v=v, games=games)
  }), as.character(cohorts$year))
  list(season=season, combined=combined, cohorts=cohorts, events=events, audit=audit,
    matrices=matrices, sample=list(raw_rows=nrow(d), all_PA=nrow(pa), eligible_PA=nrow(p),
      games=uniqueN(p$game_pk), repeated_count_rows_removed=repeated,
      exclusions=as.list(setNames(pa[, .N, by=exclusion]$N, pa[, .N, by=exclusion]$exclusion))))
}

intervals_bcai <- function(point, draws, fixed=integer()) {
  if (any(!is.finite(draws))) stop("Non-finite bootstrap replicate")
  se <- apply(draws, 2, sd)
  active <- setdiff(which(se > 1e-12), fixed)
  constant <- setdiff(seq_along(point), active)
  if (length(constant) && any(abs(sweep(draws[, constant, drop=FALSE], 2, point[constant])) > 1e-8)) stop("Unstable zero-variance bootstrap")
  critical <- if (length(active)) unname(quantile(apply(abs(sweep(sweep(draws[, active, drop=FALSE], 2, point[active]), 2, se[active], "/")), 1, max), .95, type=7)) else 0
  result <- data.table(index=point, SE=se,
    CI95_low=apply(draws, 2, quantile, probs=.025, type=7),
    CI95_high=apply(draws, 2, quantile, probs=.975, type=7),
    simultaneous95_low=point-critical*se, simultaneous95_high=point+critical*se)
  if (length(fixed)) result[fixed, `:=`(SE=0, CI95_low=point[fixed], CI95_high=point[fixed],
    simultaneous95_low=point[fixed], simultaneous95_high=point[fixed])]
  list(table=result, critical=critical, family_size=length(setdiff(seq_along(point), fixed)))
}

bootstrap_bcai <- function(prepared, B=2000L, seed=20260928L, comparisons=list()) {
  if (length(B)!=1 || B < 20 || B != floor(B)) stop("At least 20 bootstrap replicates required")
  if (length(seed)!=1 || !is.finite(seed)) stop("Invalid seed")
  RNGkind("Mersenne-Twister", "Inversion", "Rejection"); set.seed(seed)
  draws <- list(); seasons <- list(); criticals <- list()
  for (y in names(prepared$matrices)) {
    m <- prepared$matrices[[y]]; G <- nrow(m$n)
    if (G < 2) stop("Need at least two games per year")
    boot <- matrix(NA_real_, B, 12)
    for (start in seq.int(1, B, by=100L)) {
      idx <- start:min(start+99L, B)
      weights <- rmultinom(length(idx), size=G, prob=rep(1/G, G))
      values <- (t(weights) %*% m$v) / (t(weights) %*% m$n)
      boot[idx, ] <- 100 * values / values[, 1]
    }
    boot[, 1] <- 100
    out <- intervals_bcai(prepared$season[year == as.integer(y)]$index, boot, fixed=1)
    seasons[[y]] <- cbind(prepared$season[year == as.integer(y), .(year, count, N, value)], out$table)
    draws[[y]] <- boot; criticals[[y]] <- out$critical
  }
  combined_draws <- Reduce(`+`, lapply(names(draws), function(y) draws[[y]] * prepared$cohorts[year == as.integer(y)]$mix_weight))
  combined <- intervals_bcai(prepared$combined$index, combined_draws, fixed=1)
  combined$table <- cbind(prepared$combined[, .(count, N_PA)], combined$table)
  comparison_table <- data.table(comparison=character(),count=character(),difference=numeric(),
    SE=numeric(),CI95_low=numeric(),CI95_high=numeric(),simultaneous95_low=numeric(),
    simultaneous95_high=numeric(),excludes_zero_simultaneous=logical())
  contrast_draws <- NULL; contrast_critical <- NULL
  if (length(comparisons)) {
    labels <- character(); blocks <- list(); points <- numeric(); fixed <- integer()
    for (i in seq_along(comparisons)) {
      pair <- comparisons[[i]]; a <- as.character(pair[[1]]); b <- as.character(pair[[2]])
      if (length(pair)!=2 || a==b || !all(c(a,b) %in% names(draws))) stop("Invalid comparison years")
      labels <- c(labels, paste(b, a, sep=" minus "))
      blocks[[i]] <- draws[[b]] - draws[[a]]
      points <- c(points, prepared$season[year==as.integer(b)]$index - prepared$season[year==as.integer(a)]$index)
      fixed <- c(fixed, (i-1L)*12L+1L)
    }
    if (anyDuplicated(labels)) stop("Duplicate comparison")
    contrast_draws <- do.call(cbind, blocks)
    inter <- intervals_bcai(points, contrast_draws, fixed)
    comparison_table <- cbind(data.table(comparison=rep(labels, each=12), count=rep(COUNTS, length(labels))), inter$table)
    setnames(comparison_table, "index", "difference")
    comparison_table[, excludes_zero_simultaneous := simultaneous95_low > 0 | simultaneous95_high < 0]
    contrast_critical <- list(value=inter$critical, family_size=inter$family_size)
  }
  list(season=rbindlist(seasons), combined=combined$table, differences=comparison_table,
    critical=list(season=criticals, combined=combined$critical, contrasts=contrast_critical),
    draws=list(season=draws, combined=combined_draws, differences=contrast_draws))
}
