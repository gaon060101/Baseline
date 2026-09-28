suppressPackageStartupMessages(library(data.table))
D <- 'columns/001-ball-count/publish/naver_20260918'
H <- 'columns/001-ball-count/analysis/history_comparison_20260928_r01/tables'
O <- file.path(D,'revision_v7_tables');dir.create(O,showWarnings=FALSE)
a<-fread(file.path(H,'bcai_all_132.csv')); p<-fread(file.path(H,'bcap_pattern_counts_all_groups.csv'))
stopifnot(nrow(a)==132,all(a[, .N,by=year]$N==12))
md<-function(x,name){fwrite(x,file.path(O,paste0(name,'.csv')),bom=TRUE);writeLines(c(paste0('| ',paste(names(x),collapse=' | '),' |'),paste0('| ',paste(rep('---',ncol(x)),collapse=' | '),' |'),apply(x,1,function(r)paste0('| ',paste(r,collapse=' | '),' |'))),file.path(O,paste0(name,'.md')),useBytes=TRUE)}
bc<-a[,.(`11시즌 지수 범위`=sprintf('%.2f–%.2f',min(index),max(index)),`11시즌 도달 타석 합계`=format(sum(N),big.mark=',',scientific=FALSE,trim=TRUE)),by=count]
setnames(bc,'count','카운트');md(bc,'bcai_11seasons')
for(m in c('pitch_sb','pitch','pitch_ff')){
 q<-p[window=='all_2015_2025' & model==m & level=='count']
 x<-q[,.(카운트=count,`지원 연도/전체`=paste0(years_supported,'/',years_total),`양수/음수 점추정`=paste0(positive,'/',negative),`양수/음수/불명확 구간`=paste0(clear_positive,'/',clear_negative,'/',unclear),`지원된 ΔW 범위`=sprintf('%+.4f–%+.4f',delta_min,delta_max))]
 md(x,paste0(m,'_11seasons'))
}
stopifnot(p[window=='all_2015_2025'&model=='pitch_sb'&level=='count'&count=='0-2',positive]==11)
cat('11시즌 원고용 표 4개 생성 완료\n')

