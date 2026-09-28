suppressPackageStartupMessages(library(data.table))
p<-'columns/001-ball-count/publish/naver_20260918/main_v10'
h<-'columns/001-ball-count/analysis/history_comparison_20260928_r01/tables'
a<-fread(file.path(h,'bcai_all_132.csv'))
z<-a[,.(seasons=.N,mean_index=mean(index),display=round(mean(index)),PA=sum(N)),by=count]
stopifnot(nrow(z)==12,all(z$seasons==11))
fwrite(z,file.path(p,'bcai_means.csv'));print(z)
b<-fread(file.path(h,'bcap_all_2552_screened.csv'))
y<-b[model=='swing' & count %in% c('0-2','1-2','2-2','3-2') & level=='region',.(groups=.N,supported=sum(support_gate),positive=sum(delta>0 & support_gate),negative=sum(delta<0 & support_gate)),by=.(count,region)]
fwrite(y,file.path(p,'two_strike_swing.csv'));print(y)
e<-b[model=='swing' & game_year==2023 & count=='0-2' & level=='region',.(region,n,Q0,Q1,delta,family95_low,family95_high,support_gate)]
fwrite(e,file.path(p,'swing_example_2023.csv'));print(e)
