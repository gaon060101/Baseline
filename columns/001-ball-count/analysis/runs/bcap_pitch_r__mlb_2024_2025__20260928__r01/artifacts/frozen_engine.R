# BCAP R numerical implementation. Definitions remain in the versioned JSON/YAML.
suppressPackageStartupMessages({library(data.table);library(Matrix)})
options(stringsAsFactors=FALSE)
setDTthreads(2)
bc_now <- function() format(Sys.time(),"%Y-%m-%dT%H:%M:%SZ",tz="UTC")
bc_json <- function(x,path) jsonlite::write_json(x,path,auto_unbox=TRUE,pretty=TRUE,na="null",digits=16)
bc_sha <- function(path) digest::digest(file=path,algo="sha256",serialize=FALSE)
bc_meta <- function(path) list(path=gsub("\\\\","/",path),sha256=bc_sha(path),bytes=unname(file.info(path)$size))
bc_chr <- function(x) {x<-as.character(x);x[is.na(x)]<-"MISSING";x}
bc_log <- function(logs,x) logs$fits[[length(logs$fits)+1L]]<-x

bc_design <- function(d,features) {
  levels<-lapply(features,function(f) sort(unique(bc_chr(d[[f]])),method="radix"))
  sizes<-lengths(levels);offsets<-c(0L,head(cumsum(sizes),-1L));n<-nrow(d)
  jj<-unlist(lapply(seq_along(features),function(k) match(bc_chr(d[[features[k]]]),levels[[k]])+offsets[k]),use.names=FALSE)
  X<-sparseMatrix(i=rep.int(seq_len(n),length(features)),j=jj,x=1,dims=c(n,sum(sizes)))
  list(features=features,levels=levels,offsets=offsets,sizes=sizes,mean=as.numeric(colMeans(X)),X=X)
}

bc_pcg <- function(mv,b,diagonal,rtol=1e-9,atol=1e-11,maxiter=3000L) {
  x<-numeric(length(b));r<-b;tol<-max(atol,rtol*sqrt(sum(b*b)))
  if(sqrt(sum(r*r))<=tol) return(list(beta=x,iterations=0L,info=0L))
  z<-r/diagonal;p<-z;rz<-sum(r*z)
  for(it in seq_len(maxiter)) {
    ap<-mv(p);denom<-sum(p*ap)
    if(!is.finite(denom)||denom<=0) stop("PCG nonpositive curvature")
    alpha<-rz/denom;x<-x+alpha*p;r<-r-alpha*ap
    if(sqrt(sum(r*r))<=tol) return(list(beta=x,iterations=it,info=0L))
    z<-r/diagonal;rznew<-sum(r*z);p<-z+(rznew/rz)*p;rz<-rznew
  }
  list(beta=x,iterations=maxiter,info=1L)
}

bc_ridge <- function(d,y,features,alpha,label,logs) {
  design<-bc_design(d,features);X<-design$X;n<-nrow(d);u<-design$mean
  intercept<-mean(y);b<-as.numeric(crossprod(X,y-intercept));G<-crossprod(X)
  diagonal<-as.numeric(diag(G))-n*u*u+alpha
  mv<-function(v) as.numeric(G%*%v)-n*u*sum(u*v)+alpha*v
  fit<-bc_pcg(mv,b,diagonal);resid<-max(abs(mv(fit$beta)-b))/max(1,max(abs(b)))
  ok<-fit$info==0L && resid<1e-7
  bc_log(logs,list(fit_id=label,n=n,features=ncol(X),alpha=alpha,iterations=fit$iterations,
                   solver_info=fit$info,relative_gradient=resid,converged=ok))
  if(!ok) stop(paste("Ridge convergence failed",label))
  design$X<-NULL
  list(design=design,beta=fit$beta,intercept=intercept)
}

bc_predict <- function(model,d) {
  des<-model$design;out<-rep(model$intercept,nrow(d))
  for(k in seq_along(des$features)) {
    ind<-match(bc_chr(d[[des$features[k]]]),des$levels[[k]]);known<-!is.na(ind)
    block<-seq_len(des$sizes[k])+des$offsets[k]
    out[known]<-out[known]+model$beta[ind[known]+des$offsets[k]]-sum(des$mean[block]*model$beta[block])
  }
  out
}

bc_calibrate <- function(raw,a,label,logs) {
  objective<-function(b) {z<-b[1]+b[2]*raw;mean(pmax(z,0)+log1p(exp(-abs(z)))-a*z)+1e-6*b[2]^2}
  gradient<-function(b) {e<-plogis(b[1]+b[2]*raw)-a;c(mean(e),mean(e*raw)+2e-6*b[2])}
  fit<-optim(c(-2,4),objective,gradient,method="L-BFGS-B",lower=c(-Inf,0),
             control=list(factr=1e-13/.Machine$double.eps,pgtol=1e-10,maxit=1000))
  # The same objective/bound as scipy; separate optimizer implementations can
  # stop at slightly different floating-point solutions, so compare tolerantly.
  grad<-gradient(fit$par);if(fit$par[2]==0 && grad[2]>0) grad[2]<-0
  ok<-fit$convergence==0 && max(abs(grad))<1e-7
  bc_log(logs,list(fit_id=paste0(label,"/calibrator"),n=length(a),iterations=unname(fit$counts[1]),
       converged=ok,loss=fit$value,intercept=fit$par[1],slope=fit$par[2],projected_gradient=max(abs(grad))))
  if(!ok) stop(paste("Calibration failed",label,fit$message))
  fit$par
}

bc_nuisance <- function(train,cal_games,c,label,logs,alphas) {
  calidx<-train$game_pk %in% cal_games;stopifnot(any(calidx),any(!calidx))
  prop<-bc_ridge(train[!calidx],train$A[!calidx],c$features,alphas$p,paste0(label,"/prop"),logs)
  cal<-bc_calibrate(bc_predict(prop,train[calidx]),train$A[calidx],label,logs)
  out<-lapply(0:1,function(a) bc_ridge(train[A==a],train$Y[train$A==a],c$features,alphas[[paste0("m",a)]],paste0(label,"/m",a),logs))
  counts<-train[,.(n0=sum(A==0),n1=sum(A==1)),by=c$support_entity]
  supported<-bc_chr(counts[[c$support_entity]])[pmin(counts$n0,counts$n1)>=c$min_entity_arm_training]
  list(prop=prop,cal=cal,out=out,repertoire=supported,known_pitcher=unique(bc_chr(train$pitcher)),
       known_batter=unique(bc_chr(train$batter)),calibration_games=cal_games,alpha=alphas,
       training_games=sort(unique(train$game_pk)))
}

bc_features <- function(d,c) {
  if(c$variant=="swing") {
    for(f in c("release_speed","pfx_x","pfx_z","plate_x")) {
      step<-switch(f,release_speed=5,pfx_x=.5,pfx_z=.5,plate_x=.35)
      v<-floor(d[[f]]/step);v[!is.finite(v)]<--999;set(d,j=paste0(f,"_bin"),value=as.character(v))
    }
    v<-floor(((d$plate_z-d$sz_bot)/(d$sz_top-d$sz_bot))/.2);v[!is.finite(v)]<--999
    d[,relative_z_bin:=as.character(v)];d[,swing_cell:=paste(count,zone,pitch_group,sep="|")]
  }
  invisible(d)
}

bc_regions <- function(d) {
  valid<-is.finite(d$plate_x)&is.finite(d$plate_z)&is.finite(d$sz_top)&is.finite(d$sz_bot)&d$sz_top>d$sz_bot
  x<-d$plate_x*ifelse(d$stand=="R",1,ifelse(d$stand=="L",-1,NA_real_))
  masks<-list(CENTER=valid&abs(d$plate_x)<=17/24&d$plate_z>=d$sz_bot&d$plate_z<=d$sz_top,
    HIGH=valid&d$plate_z>d$sz_top,LOW=valid&d$plate_z<d$sz_bot,INSIDE=valid&x< -17/24,OUTSIDE=valid&x>17/24)
  lapply(masks,function(x) {x[is.na(x)]<-FALSE;x})
}

bc_score <- function(d,model,c) {
  cols<-c("row_id","game_pk","at_bat_number","pitch_number","game_year","game_date","count","pitcher","batter","Y","A","zone","pitch_group")
  s<-copy(d[,..cols]);s[,raw_propensity:=bc_predict(model$prop,d)]
  s[,p:=pmin(1-c$numerical_epsilon,pmax(c$numerical_epsilon,plogis(model$cal[1]+model$cal[2]*raw_propensity)))]
  s[,`:=`(mu0=bc_predict(model$out[[1]],d),mu1=bc_predict(model$out[[2]],d),
      repertoire=bc_chr(d[[c$support_entity]])%in%model$repertoire,
      known_pitcher=bc_chr(d$pitcher)%in%model$known_pitcher,known_batter=bc_chr(d$batter)%in%model$known_batter)]
  s[,`:=`(phi0=mu0+(1-A)/(1-p)*(Y-mu0),phi1=mu1+A/p*(Y-mu1),measurement_support=TRUE)]
  if(c$variant=="swing") {
    complete<-Reduce(`&`,lapply(d[,.(release_speed,pfx_x,pfx_z,plate_x,plate_z,sz_top,sz_bot)],function(x) !is.na(x)))
    s[,measurement_support:=d$zone!="MISSING"&complete&d$pitch_group%in%c("FB","NFB")]
  }
  s[,support:=p>=c$trim&p<=1-c$trim&repertoire&measurement_support]
  masks<-bc_regions(d);for(r in names(masks)) set(s,j=paste0("region_",r),value=masks[[r]])
  s
}

bc_cluster <- function(v,game,family=1) {
  n<-length(v);if(!n) return(rep(NA_real_,7))
  point<-mean(v);sums<-rowsum(v-point,game,reorder=FALSE);G<-nrow(sums)
  se<-sqrt(G/max(1,G-1)*sum(sums*sums))/n;z<-qt(.975,max(1,G-1));zs<-qt(1-.05/(2*family),max(1,G-1))
  c(point,se,point-z*se,point+z*se,point-zs*se,point+zs*se,G)
}

bc_group <- function(whole,c,level,count,region="ALL",pitchgroup="ALL") {
  d<-whole[support==TRUE];n<-nrow(d);nall<-nrow(whole)
  out<-list(level=level,count=count,region=region,pitch_group=pitchgroup,n_all=nall,n=n,
      coverage=if(nall)n/nall else NA_real_,games=uniqueN(d$game_pk),PA=uniqueN(d[,.(game_pk,at_bat_number)]),
      pitchers=uniqueN(d$pitcher),batters=uniqueN(d$batter),action1_rate_all=mean(whole$A),action1_rate=mean(d$A),
      action0_rate_all=1-mean(whole$A),action0_rate=1-mean(d$A),observed_Y=mean(d$Y),action0=c$action0,action1=c$action1)
  for(a in 0:1) {
    w<-(d$A==a)/(if(a)d$p else 1-d$p);ss<-sum(w*w);wg<-rowsum(w,d$game_pk,reorder=FALSE)
    out[[paste0("rows",a)]]<-sum(d$A==a);out[[paste0("ESS",a)]]<-if(ss)sum(w)^2/ss else 0
    out[[paste0("games",a)]]<-uniqueN(d$game_pk[d$A==a])
    out[[paste0("max_game_share",a)]]<-if(sum(w))max(wg)/sum(w) else NA_real_
  }
  enough<-n>=c$min_rows&&min(out$ESS0,out$ESS1)>=c$min_ess&&min(out$games0,out$games1)>=c$min_arm_games&&
      out$coverage>=c$min_coverage&&max(out$max_game_share0,out$max_game_share1)<=c$max_game_share
  if(n) {
    st<-bc_cluster(d$phi1-d$phi0,d$game_pk,c$comparison_family)
    raw<-if(st[1]==0) "TIE" else if(if(c$better=="higher")st[1]>0 else st[1]<0)c$action1 else c$action0
    out<-c(out,list(Q0=mean(d$phi0),Q1=mean(d$phi1),gcomp0=mean(d$mu0),gcomp1=mean(d$mu1),delta=st[1],SE=st[2],
      nominal95_low=st[3],nominal95_high=st[4],family95_low=st[5],family95_high=st[6],arithmetic_direction=raw,
      point_direction=if(enough)raw else NA_character_,evidence=if(!enough)"비교 자료 부족" else if(st[5]<=0&&st[6]>=0)"차이 불명확" else "관찰상 방향 뚜렷",
      large_point_difference=abs(st[1])>=c$practical_delta_W))
  } else out<-c(out,list(Q0=NA_real_,Q1=NA_real_,delta=NA_real_,point_direction=NA_character_,evidence="비교 자료 부족"))
  c(out,list(support_gate=enough,recommendation=NA_character_,unit="W per selected current decision; not PA sum"))
}

bc_summarize <- function(s,c,regions=TRUE) {
  counts<-as.vector(t(outer(0:3,0:2,paste,sep="-")));out<-list(bc_group(s,c,"overall","ALL"))
  for(ct in counts) {
    sub<-s[count==ct];out[[length(out)+1L]]<-bc_group(sub,c,"count",ct)
    if(c$variant=="swing" && regions) for(r in c("HIGH","LOW","INSIDE","OUTSIDE","CENTER")) {
      z<-sub[get(paste0("region_",r))==TRUE];out[[length(out)+1L]]<-bc_group(z,c,"region",ct,r)
      for(pg in c("FB","NFB"))out[[length(out)+1L]]<-bc_group(z[pitch_group==pg],c,"region_pitch",ct,r,pg)
    }
  }
  rbindlist(out,fill=TRUE)
}
