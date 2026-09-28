suppressPackageStartupMessages({library(data.table);library(digest);library(jsonlite)})
D<-'columns/001-ball-count/publish/naver_20260918'
H<-'columns/001-ball-count/analysis/history_comparison_20260928_r01'
a<-fread(file.path(H,'tables/bcai_all_132.csv'));b<-fread(file.path(H,'tables/bcap_all_2552_screened.csv'))
checks<-list();ck<-function(n,v){checks[[n]]<<-isTRUE(v);stopifnot(isTRUE(v))}
ck('BCAI_11_seasons_132_counts',nrow(a)==132&&length(unique(a$year))==11)
ck('BCAI_start_denominator',sum(a[count=='0-0',N])==1896892&&sum(a[count=='0-0',games])==25193)
ck('BCAI_extrema_every_year',all(a[order(index),.(low=first(count),high=last(count)),by=year][,low=='0-2'&high=='3-0']))
ck('BCAI_11_ranges',identical(fread(file.path(D,'revision_v7_tables/bcai_11seasons.csv'))[['11시즌 지수 범위']],a[,.(r=sprintf('%.2f–%.2f',min(index),max(index))),by=count]$r))
for(c in c('0-2','1-2')){q<-b[model=='pitch_sb'&level=='count'&count==c];ck(paste0('SB_',c),nrow(q)==11&&all(q$support_gate)&all(q$delta>0)&&sum(q$family95_low>0)==if(c=='0-2')10 else 8)}
q<-b[model=='swing'&level=='region'&region=='CENTER'];ck('swing_inside',nrow(q)==132&&all(q$support_gate)&&sum(q$delta>0)==130&&sum(q$delta<0)==2&&sum(q$family95_low>0)==103)
q<-b[model=='swing'&level=='region'&region!='CENTER'];ck('swing_outside',nrow(q)==528&&sum(q$support_gate)==481&&sum(q$delta<0,na.rm=TRUE)==481&&sum(q$family95_high<0,na.rm=TRUE)==477)
q<-b[model=='pitch'&level=='count'&count=='3-0'];ck('FB_30',sum(q$support_gate)==10&&sum(q$delta>0,na.rm=TRUE)==10&&sum(q$family95_low>0,na.rm=TRUE)==10&&q[support_gate==FALSE,game_year]==2020)
q<-b[model=='pitch_ff'&level=='count'&count=='3-2'];ck('FF_32',all(q$support_gate)&&sum(q$delta>0)==11&&sum(q$family95_low>0)==5)
h<-fread(file.path(H,'audit/source_hashes.csv'));h[,verification_path:=path]
h[startsWith(path,paste0(D,'/')),verification_path:=file.path(D,'revisions/v6_before_history_v7',basename(path))]
h[,actual:=vapply(verification_path,function(p)digest(file=p,algo='sha256',serialize=FALSE),character(1))]
ck('original_manuscripts_archived_and_167_other_sources_unchanged',all(h$actual==h$sha256))
fwrite(h,file.path(D,'revision_v7_source_preservation.csv'),bom=TRUE)
write_json(list(pass=all(unlist(checks)),checks=checks,note='편집에 쓰인 저장 수치와 수정 전 원고 보관본 검산. 역사 보고서의 당시 원고 경로는 보관본으로 대조했으며 기존 감사 파일은 변경하지 않음. 재적합·새 인과 검증 아님.'),file.path(D,'revision_v7_numerical.json'),pretty=TRUE,auto_unbox=TRUE)
print(checks)
