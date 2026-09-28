# Independent, small synthetic checks. No real data, files, or model fitting.
source("models/bcap/r/engine.R",encoding="UTF-8")
spec <- jsonlite::fromJSON("models/bcap/pitch/v0.2.0/specification.yaml")
stopifnot(spec$min_rows==500,spec$min_ess==200,spec$min_arm_games==100,
  spec$min_coverage==.5,spec$max_game_share==.05)
sample <- data.table(game_pk=rep(1:120,each=5),at_bat_number=seq_len(600),
  pitcher="p",batter="b",A=rep(0:1,300),Y=.5,p=.5,
  phi0=sin(seq_len(600)),phi1=cos(seq_len(600)),mu0=0,mu1=0,support=TRUE)
summarize <- function(x) bc_group(x,spec,"overall","ALL")
base <- summarize(sample)
stopifnot(base$support_gate,base$ESS0==300,base$ESS1==300,base$games0==120,base$games1==120)

# Change one condition at a time while keeping all remaining gates satisfied.
stopifnot(summarize(sample[1:500])$support_gate,!summarize(sample[1:499])$support_gate)
ess <- copy(sample); ess[, `:=`(A=c(rep(0,200),rep(1,400)),game_pk=rep(1:100,6))]
stopifnot(summarize(ess)$support_gate,summarize(ess)$ESS0==200)
ess[1,A:=1];stopifnot(!summarize(ess)$support_gate,summarize(ess)$ESS0==199,summarize(ess)$games0==100)
games <- copy(sample);games[,game_pk:=(seq_len(.N)-1L)%%99L+1L]
stopifnot(!summarize(games)$support_gate,summarize(games)$games0==99,summarize(games)$ESS0==300)
coverage <- rbind(sample,copy(sample)[,support:=FALSE])
stopifnot(summarize(coverage)$support_gate,summarize(coverage)$coverage==.5)
coverage[1,support:=FALSE];stopifnot(!summarize(coverage)$support_gate,summarize(coverage)$n==599)
concentration <- copy(sample)
concentration[, `:=`(A=rep(0:1,each=300),game_pk=rep(c(rep(1,15),rep(2:120,length.out=285)),2))]
edge <- summarize(concentration)
stopifnot(edge$support_gate,edge$max_game_share0==.05,edge$max_game_share1==.05)
concentration <- rbind(concentration,copy(concentration[1])[,at_bat_number:=601])
over <- summarize(concentration)
stopifnot(!over$support_gate,over$max_game_share0>.05,over$ESS0>=200,over$games0==120)
empty <- summarize(copy(sample)[,support:=FALSE])
stopifnot(empty$n==0,!empty$support_gate,is.na(empty$delta),empty$evidence=="비교 자료 부족")

# Unequal game sizes: independent direct cluster-sum arithmetic, not pitch IID SE.
values <- c(1,2,4,-1,3,0,2,6)
game <- c(1,1,2,3,3,3,4,4)
groups <- split(values,game);point <- mean(values);G <- length(groups)
totals <- vapply(groups,function(x) sum(x-point),numeric(1))
se <- sqrt(G/(G-1)*sum(totals^2))/length(values)
got <- bc_cluster(values,game,family=255)
stopifnot(abs(got[1]-point)<1e-12,abs(got[2]-se)<1e-12,
  abs(got[3]-(point-qt(.975,G-1)*se))<1e-12,
  abs(got[5]-(point-qt(1-.05/(2*255),G-1)*se))<1e-12,
  got[5]<got[3],got[6]>got[4])
# A declared family upper bound may exceed the 232 displayed module groups.
stopifnot(qt(1-.05/(2*255),G-1)>=qt(1-.05/(2*232),G-1))

# A single year remains a valid category block with zero centered contribution.
one_year <- data.table(game_year=rep(2015,4),state=c("a","b","a","b"))
design <- bc_design(one_year,c("game_year","state"))
year_column <- as.numeric(design$X[,1])
stopifnot(design$sizes[1]==1,all(year_column-design$mean[1]==0))

# Recheck the finite-physical-measurement fix independently.
physical <- data.table(release_speed=rep(95,5),pfx_x=c(.1,Inf,NA,.1,.1),pfx_z=.2,
  plate_x=0,plate_z=2.5,sz_top=3.5,sz_bot=1.5,
  zone=c("INNER","INNER","INNER","MISSING","INNER"),pitch_group=c("FB","FB","FB","FB","UNCLASSIFIED"))
stopifnot(identical(bc_swing_measurement_support(physical),c(TRUE,FALSE,FALSE,FALSE,FALSE)))
cat("PASS independent BCAP review: five gate boundaries, no-support behavior, unequal-game cluster arithmetic, conservative family, single-year block and finite measurement support\n")
