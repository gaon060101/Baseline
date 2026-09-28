suppressPackageStartupMessages({library(data.table);library(ggplot2)})
D<-'columns/001-ball-count/publish/naver_20260918/main_v8'
dir.create(D,showWarnings=FALSE)
H<-'columns/001-ball-count/analysis/history_comparison_20260928_r01/tables'
a<-fread(file.path(H,'bcai_all_132.csv'))
counts<-c('0-0','0-1','0-2','1-0','1-1','1-2','2-0','2-1','2-2','3-0','3-1','3-2')
z<-a[,.(low=min(index),high=max(index),seasons=.N,PA=sum(N)),by=count][match(counts,count)]
stopifnot(nrow(z)==12,all(z$seasons==11),a[count=='0-0',sum(N)]==1896892)
z[,범위:=sprintf('%.2f–%.2f',low,high)]
fwrite(z,file.path(D,'bcai_12counts.csv'),bom=TRUE)
a[,count:=factor(count,levels=rev(counts))]
p<-ggplot(a,aes(index,count))+geom_vline(xintercept=100,colour='#9fb8b5')+geom_point(colour='#147d78',size=3,alpha=.55)+labs(title='카운트별 점수는 열한 시즌 내내 비슷한 순서였다',subtitle='MLB 2015–2025 · 한 점은 한 시즌의 BCAI',x='BCAI 점수 · 각 시즌의 타석 시작 평균=100',y=NULL,caption='출처: BCAI-OBS 연도별 저장 결과 132행\n분모: 해당 카운트를 한 번 이상 거친 고유 타석.\n점 11개는 연도별 점수이며 신뢰구간이나 11년 통합 점수가 아니다.')+theme_minimal(base_family='Malgun Gothic',base_size=15)+theme(plot.title=element_text(size=19,face='bold'),plot.subtitle=element_text(size=14),plot.caption=element_text(size=11,hjust=0),panel.grid.minor=element_blank(),plot.margin=margin(18,20,18,20))
ggsave(file.path(D,'bcai_11seasons.png'),p,width=9,height=10,dpi=100,bg='white')
cat('본문 전용 카운트 표·그림 생성 완료\n')
