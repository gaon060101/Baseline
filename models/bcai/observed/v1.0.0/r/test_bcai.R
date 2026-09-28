source("models/bcai/observed/v1.0.0/r/bcai.R", encoding="UTF-8")
options(datatable.auto.index=FALSE)
row <- function(game, pa, pitch, count, event=NA_character_, year=2030L) {
  parts <- as.numeric(strsplit(count, "-")[[1]])
  data.table(game_pk=game, at_bat_number=pa, pitch_number=pitch, game_year=year,
             balls=parts[1], strikes=parts[2], events=event)
}
# Constructed data, not baseball results. Two games with complete count support.
fixture <- rbindlist(lapply(1:2, function(game) rbindlist(lapply(seq_along(COUNTS), function(i) {
  if (i==1) row(game, i, 1, "0-0", "single") else
    rbind(row(game,i,1,"0-0"), row(game,i,2,COUNTS[i], if (game==1) "walk" else "home_run"))
}))))
weights <- data.table(year=2030L, BB=.7, HBP=.8, `1B`=.9, `2B`=1.2, `3B`=1.6, HR=2)
base <- prepare_bcai(fixture, weights)
stopifnot(base$sample$eligible_PA==24, base$combined[count=="0-0"]$index==100)
expected_base <- (2*.9 + 11*.7 + 11*2)/24
stopifnot(abs(base$season[count=="0-1"]$index - 100*1.35/expected_base) < 1e-10)
stopifnot(isTRUE(all.equal(base$season, prepare_bcai(fixture[.N:1], weights)$season)))
repeat_row <- copy(fixture[game_pk==1 & at_bat_number==3 & pitch_number==2]); repeat_row[, pitch_number:=3]
dupcount <- prepare_bcai(rbind(fixture, repeat_row), weights)
stopifnot(dupcount$sample$repeated_count_rows_removed==1, isTRUE(all.equal(base$season, dupcount$season)))
expect_error <- function(expr) stopifnot(inherits(tryCatch({force(expr); NULL}, error=identity), "error"))
expect_error(prepare_bcai(rbind(fixture, fixture[1]), weights))
badcount <- copy(fixture); badcount[1, balls:=4]; expect_error(prepare_bcai(badcount, weights))
expect_error(prepare_bcai(fixture, weights[0]))
bad <- rbind(row(1,100,1,"0-0","single"), row(1,100,2,"0-1"),
  row(1,101,1,"0-0","intent_walk"), row(1,102,1,"0-0","catcher_interf"),
  row(1,103,1,"0-0","truncated_pa"), row(1,104,1,"0-0","unrecognized"),
  row(1,105,1,"0-1","single"))
filtered <- prepare_bcai(rbind(fixture,bad), weights)
stopifnot(filtered$sample$eligible_PA==24, filtered$sample$exclusions$missing_final==1,
  filtered$sample$exclusions$no_observed_0_0==1, isTRUE(all.equal(base$season, filtered$season)))
# A second arbitrary year confirms that years are not hard-coded.
other <- copy(fixture); other[, `:=`(game_year=2031L, game_pk=game_pk+100)]
other[events=="walk", events:="single"]
otherw <- copy(weights); otherw[, year:=2031L]
both <- prepare_bcai(rbind(fixture,other), rbind(weights,otherw))
b1 <- bootstrap_bcai(both, 40, 15, list(c(2030,2031)))
b2 <- bootstrap_bcai(both, 40, 15, list(c(2030,2031)))
stopifnot(identical(b1,b2), all(b1$season[count=="0-0"]$index==100),
  b1$differences[count=="0-0"]$difference==0, b1$critical$contrasts$family_size==11,
  all(b1$combined$simultaneous95_low <= b1$combined$index),
  all(b1$combined$simultaneous95_high >= b1$combined$index))
expect_error(bootstrap_bcai(both, 40, 15, list(c(2030,2032))))
one_year <- bootstrap_bcai(base,40,15)
stopifnot(nrow(one_year$differences)==0, "comparison" %in% names(one_year$differences))
cat("PASS: hand calculation, order invariance, repeated counts, six exclusions, invalid inputs, arbitrary years, reproducible clustered bootstrap\n")
