source("models/bcap/r/engine.R",encoding="UTF-8")
logs<-new.env();logs$fits<-list()
d<-data.table(player=rep(c("a","b","c","d"),8),state=rep(c("u","v"),each=16))
y<-sin(seq_len(32))+.3*(d$player=="b")
m<-bc_ridge(d,y,c("player","state"),2,"synthetic",logs)
X<-as.matrix(bc_design(d,c("player","state"))$X);XC<-sweep(X,2,colMeans(X))
direct<-solve(crossprod(XC)+diag(2,ncol(XC)),crossprod(XC,y-mean(y)))
stopifnot(max(abs(direct-m$beta))<1e-10,max(abs(bc_predict(m,d)-(mean(y)+XC%*%direct)))<1e-10)
unknown<-data.table(player="unseen",state="unseen")
stopifnot(identical(unname(bc_predict(m,unknown)),unname(m$intercept)))
partial<-data.table(player="a",state="unseen");i<-match("a",m$design$levels[[1]])
expected<-m$intercept+m$beta[i]-sum(m$design$mean[1:4]*m$beta[1:4])
stopifnot(abs(bc_predict(m,partial)-expected)<1e-12)
v<-c(1,2,3,4,8,7);g<-c(1,1,2,2,3,3);st<-bc_cluster(v,g,3)
manual<-sqrt(3/2*sum(tapply(v-mean(v),g,sum)^2))/6
stopifnot(abs(st[2]-manual)<1e-12,st[5]<st[3],st[6]>st[4])
# Exact support endpoints and failure of the group gate for tiny samples.
c<-jsonlite::fromJSON("models/bcap/pitch/v0.2.0/specification.yaml")
s<-data.table(game_pk=1:4,at_bat_number=1,pitcher="p",batter="b",A=c(0,1,0,1),Y=0,
  p=c(.05,.95,.049999,.950001),phi0=0,phi1=1,mu0=0,mu1=1,repertoire=TRUE,measurement_support=TRUE)
s[,support:=p>=c$trim&p<=1-c$trim&repertoire&measurement_support]
stopifnot(identical(s$support,c(TRUE,TRUE,FALSE,FALSE)))
summary<-bc_group(s,c,"overall","ALL");stopifnot(summary$n==2,!summary$support_gate,summary$evidence=="비교 자료 부족")
# AIPW correction contributes only to the observed arm.
a<-c(0,1);p<-c(.25,.8);yy<-c(.5,1);m0<-c(.2,.3);m1<-c(.6,.7)
stopifnot(max(abs((m0+(1-a)/(1-p)*(yy-m0))-c(.6,.3)))<1e-12,
          max(abs((m1+a/p*(yy-m1))-c(.6,1.075)))<1e-12)
# A complete tiny nuisance fit also exercises string-named entity aggregation.
toy<-data.table(game_pk=rep(1:8,each=20),player=rep(c("a","b","c","d"),40),
                state=rep(c("u","v"),80),pitcher="p",batter="b",
                A=rep(c(0,1,1,0,1,0,0,1),20),Y=sin(seq_len(160)))
tc<-c;tc$features<-c("player","state");tc$support_entity<-"player";tc$min_entity_arm_training<-10
nu<-bc_nuisance(toy,1:2,tc,"tiny_nuisance",logs,list(p=2,m0=2,m1=2))
stopifnot(length(nu$repertoire)==4,all(is.finite(bc_predict(nu$prop,toy))))
measurement<-data.table(release_speed=90,pfx_x=c(1,Inf,NA_real_),pfx_z=1,
  plate_x=0,plate_z=2,sz_top=3,sz_bot=1,zone="INNER",pitch_group="FB")
stopifnot(identical(bc_swing_measurement_support(measurement),c(TRUE,FALSE,FALSE)))
cat("PASS: centered ridge/direct solve; unknown block; game cluster; support endpoints/group gate; AIPW arms\n")
