suppressPackageStartupMessages(library(data.table))
D<-'columns/001-ball-count/analysis/history_comparison_20260928_r01'
b<-fread(file.path(D,'tables/bcap_all_2552_screened.csv')); a<-fread(file.path(D,'tables/bcai_all_132.csv'));cs<-fread(file.path(D,'tables/bcap_pattern_counts_all_groups.csv'))
show<-function(x){print(x,nrows=140,digits=5)}
cat('REGION SUMMARY\n');show(b[model=='swing'&level=='region',.(supported=sum(support_gate),positive=sum(delta>0,na.rm=T),negative=sum(delta<0,na.rm=T),clearpos=sum(family95_low>0,na.rm=T),clearneg=sum(family95_high<0,na.rm=T),missing=sum(!support_gate)),by=.(game_year,inside=region=='CENTER')])
cat('SWING EXCEPTIONS\n');show(b[game_year<2024&model=='swing'&level=='region'&((region=='CENTER'&(delta<=0|family95_low<=0|!support_gate))|(region!='CENTER'&(delta>=0|family95_high>=0|!support_gate))),.(game_year,count,region,n_all,n,delta,family95_low,family95_high,support_gate)])
cat('FINER EXCEPTIONS\n');show(b[game_year<2024&model=='swing'&level=='region_pitch'&support_gate&((region=='CENTER'&delta<0)|(region!='CENTER'&delta>0)),.(game_year,count,region,pitch_group,n_all,n,delta,family95_low,family95_high)])
cat('S/B TWO COUNTS\n');show(b[model=='pitch_sb'&level=='count'&count%in%c('0-2','1-2','2-2'),.(game_year,count,n,delta,family95_low,family95_high)])
cat('RARE FB and FF32\n');show(b[level=='count'&((model=='pitch'&count=='3-0')|(model=='pitch_ff'&count=='3-2')),.(model,game_year,count,n_all,n,coverage,rows0,rows1,ESS0,ESS1,delta,family95_low,family95_high,gcomp0,gcomp1)])
cat('FINER COVERAGE\n');show(b[model=='swing'&level=='region_pitch',.(total=.N,supported=sum(support_gate),positive=sum(delta>0,na.rm=T),negative=sum(delta<0,na.rm=T),cp=sum(family95_low>0,na.rm=T),cn=sum(family95_high<0,na.rm=T)),by=.(game_year,inside=region=='CENTER')])
cat('OVERALL COVERAGE\n');show(b[level=='overall',.(model,game_year,n_all,n,coverage,PA,games)])
cat('SENSITIVITY CORE\n');show(cs[count%in%c('0-2','1-2','3-0','3-2')&level=='count'&window%in%c('added_2015_2023','added_no2020','added_2017_2023','added_2017_2023_no2020')&model!='swing',.(model,count,window,years_total,years_supported,positive,clear_positive,delta_min,delta_max)])
