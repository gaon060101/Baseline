# All new descriptive statistics, chart data and figures are generated in R.
source('columns/001-ball-count/analysis/history_comparison_20260928_r01/analyze.R',echo=FALSE)
md<-function(x,path){
 z<-copy(x); for(j in names(z)) z[,(j):=ifelse(is.na(get(j)),'자료 부족',as.character(get(j)))]
 lines<-c(paste0('| ',paste(names(z),collapse=' | '),' |'),paste0('| ',paste(rep('---',ncol(z)),collapse=' | '),' |'),apply(z,1,function(r)paste0('| ',paste(gsub('\n',' ',r),collapse=' | '),' |')))
 writeLines(enc2utf8(lines),file.path(out,path),useBytes=TRUE)
}
f<-function(x,d=3)formatC(x,format='f',digits=d,big.mark=',')
# Evidence detail and uncertainty records read from each frozen run.
methods<-rbindlist(lapply(names(mans),function(mp){m<-mans[[mp]];cfg<-m$configuration;rc<-m$run_config
 if(!is.null(cfg)) {
  p<-file.path(dirname(mp),'artifacts/frozen_engine.R');if(file.exists(p))track(p,'frozen interval and support implementation')
 }
 data.table(run_id=m$run_id,model_id=m$model_id,manifest=mp,status=m$status,
 family=if(!is.null(rc$comparison_family))rc$comparison_family else if(!is.null(cfg$comparison_family))cfg$comparison_family else NA_real_,
 uncertainty=if(!is.null(cfg$uncertainty))cfg$uncertainty else 'BCAI game bootstrap; per-run count family',
 seed=if(!is.null(rc$seed))rc$seed else if(!is.null(cfg$seed))cfg$seed else NA_real_)
}),fill=TRUE);save(methods,'run_methods')
summary_counts<-rbindlist(lapply(names(groups),function(g){
 z<-b[game_year%in%groups[[g]]]
 rbindlist(list(z[level=='count',.(total=.N,supported=sum(support_gate),pos=sum(delta>0,na.rm=T),neg=sum(delta<0,na.rm=T),clearpos=sum(family95_low>0,na.rm=T),clearneg=sum(family95_high<0,na.rm=T)),by=model][,scope:='count'],z[model=='swing'&level%in%c('region','region_pitch'),.(total=.N,supported=sum(support_gate),pos=sum(delta>0,na.rm=T),neg=sum(delta<0,na.rm=T),clearpos=sum(family95_low>0,na.rm=T),clearneg=sum(family95_high<0,na.rm=T)),by=.(model,level,inside=region=='CENTER')][,scope:=paste(level,ifelse(inside,'inside','outside'))]),fill=T)[,window:=g]
}));save(summary_counts,'window_totals')
denom<-yearshape[,.(years=.N,PA=sum(eligible_PA),games=sum(games)),by=.(period=ifelse(year<2024,'2015–2023','2024–2025'))];save(denom,'period_denominators')
md(profile[,.(카운트=count,`기존 2시즌 지수`=f(baseline_index,2),`추가 9시즌 범위`=paste(f(added_min,2),f(added_max,2),sep='–'),`11시즌 범위`=paste(f(index_min,2),f(index_max,2),sep='–'),`추가 9시즌 도달 PA 합계`=format(added_N,big.mark=',',trim=T),`11시즌 순위 범위`=paste(rank_min,rank_max,sep='–'))],'tables/bcai_profile.md')
for(mod in c('pitch','pitch_sb','pitch_ff')){
 z<-counts[window=='added_2015_2023'&model==mod&level=='count'];z<-z[match(count_order,count)]
 orig<-baseline[model==mod&level=='count',.(count,baseline_delta=delta)]
 z<-merge(z,orig,by='count',sort=FALSE);z<-z[match(count_order,count)]
 md(z[,.(카운트=count,`기존 2시즌 ΔW`=f(baseline_delta,4),`추가 연도 지원/전체`=paste0(years_supported,'/',years_total),`양수/음수 연도`=paste0(positive,'/',negative),`구간 양수/음수/불명확`=paste(clear_positive,clear_negative,unclear,sep='/'),`지원 추정값 범위 W`=paste(f(delta_min,4),f(delta_max,4),sep=' ~ '))],paste0('tables/',mod,'_12counts.md'))
}
sw<-b[model=='swing'&level=='region',.(지원=sum(support_gate),양수=sum(delta>0,na.rm=T),음수=sum(delta<0,na.rm=T),구간양수=sum(family95_low>0,na.rm=T),구간음수=sum(family95_high<0,na.rm=T)),by=.(연도=game_year,구역=ifelse(region=='CENTER','존 안 12칸','존 밖 48칸'))]
md(sw,'tables/swing_years.md')
sens<-counts[model=='pitch_sb'&level=='count'&count%in%c('0-2','1-2')&window%in%names(groups)[1:4]]
md(sens[,.(범위=years_used,카운트=count,`지원/검토 연도`=paste(years_supported,years_total,sep='/'),`존 밖 점추정 연도`=positive,`구간까지 존 밖 연도`=clear_positive)],'tables/sensitivity_sb.md')
md(yearshape[,.(연도=year,유효타석=format(eligible_PA,big.mark=',',trim=T),경기=games,`0-0의 W`=f(start_W,6),`2-2와 0-1의 지수 차이`=f(gap_01_22,3),`2-1과 1-0의 지수 차이`=f(gap_10_21,3))],'tables/year_denominators.md')
# BCAI historical rank of 2024/25 in each count; ties at 0-0 retained.
pos<-a[,.(year,index,N,value,historical_rank_low_to_high=frank(index,ties.method='min')),by=count][year>=2024];save(pos,'baseline_historical_position')
# Sensitivity summaries never pool BCAP contrasts. Summarize direction counts only.
ai_show<-aisens[count%in%c('0-2','1-1','3-0','3-2')&window%in%names(groups)[1:4]]
md(ai_show[,.(기간=window,카운트=count,연도수=years,`연도 지수 단순평균`=f(equal_year_mean_of_indices,3),`시작 PA 가중 연도 지수 평균`=f(start_PA_weighted_mean_of_indices,3))],'tables/sensitivity_bcai.md')
center<-counts[window=='added_2015_2023'&model=='swing'&level=='region'&region=='CENTER'][match(count_order,count)]
md(center[,.(카운트=count,`지원/검토 연도`=paste(years_supported,years_total,sep='/'),`양수/음수 연도`=paste(positive,negative,sep='/'),`구간 양수/불명확`=paste(clear_positive,unclear,sep='/'),`차이 범위 W`=paste(f(delta_min,4),f(delta_max,4),sep=' ~ '))],'tables/swing_center_12counts.md')
swexamples<-b[model=='swing'&level=='region'&count=='0-2'&region%in%c('CENTER','OUTSIDE'),.(game_year,count,region,n_all,n,coverage,delta,family95_low,family95_high)]
save(swexamples,'swing_02_examples')
cat('SWING 02 EXAMPLES\n');print(swexamples[game_year%in%c(2015,2020,2023)])
rare<-b[model=='pitch'&level=='count'&count=='3-0',.(year=game_year,n_all,n,rows_NFB=rows0,ESS_NFB=ESS0,coverage,support_gate,delta,family95_low,family95_high)]
save(rare,'fb_30_support')
# Verification of supplementary output sources (separate scope, never append to history).
suppa_mp<-file.path(an,'runs/bcai_supplement__mlb_2026_ytd_20260907__20260928__r01/manifest.json')
suppa<-verified(file.path(dirname(suppa_mp),'artifacts/season_indices.csv'),suppa_mp,'2026 YTD BCAI supplementary')
suppb<-rbindlist(lapply(c('pitch','pitch_ff'),function(mod){mp<-file.path(an,paste0('runs/bcap_',mod,'_r_supplement__mlb_2026_ytd_20260907__20260928__r01/manifest.json'));z<-verified(file.path(dirname(mp),'artifacts/action_values.csv'),mp,'2026 YTD BCAP supplementary');z[,model:=mod];z}),fill=T)
save(suppa,'supplement_2026_bcai');save(suppb,'supplement_2026_bcap')
# Korean figures. Design at 900 pixels wide, each topic separately readable.
theme_set(theme_minimal(base_size=13,base_family='Malgun Gothic')+theme(plot.title=element_text(size=19,face='bold',colour='#173e45'),plot.subtitle=element_text(size=12,lineheight=1.25),plot.caption=element_text(size=10,hjust=0,lineheight=1.25),panel.grid.minor=element_blank(),legend.position='bottom',plot.margin=margin(15,18,15,14)))
figsave<-function(p,n,h){ggsave(file.path(out,'figures',n),p,width=9,height=h,dpi=100,bg='white',limitsize=FALSE)}
aa<-copy(a);aa[,count:=factor(count,levels=rev(count_order))];aa[,시기:=ifelse(year<2024,'추가 9시즌','기준 2시즌')]
basplot<-ai0[,.(count=factor(count,levels=rev(count_order)),index)]
p1<-ggplot(aa,aes(index,count))+geom_vline(xintercept=100,colour='#b4bdc4')+geom_point(data=aa[year<2024],colour='#96aaa9',size=3,alpha=.65)+geom_point(data=aa[year>=2024],aes(shape=as.factor(year)),colour='#157c79',size=3)+geom_point(data=basplot,shape=4,colour='#ab4d35',size=3,stroke=1.3)+labs(title='카운트의 큰 순서는 11시즌 내내 같았다',subtitle='회색 점: 추가 2015–2023 각 시즌 / 청록 점: 2024·2025\n갈색 ×: 기존 2024–2025 통합 BCAI',x='BCAI · 각 시즌 0-0=100',y=NULL,shape='기준 시즌',caption='출처: BCAI-OBS 저장 결과 132행, 본 보고서 bcai_all_132.csv\n각 카운트의 도달 PA가 분모. 회색 점은 9개 연도이며 신뢰구간이 아니다.\n통합 기준점은 기존 두 시즌의 고정 PA 가중 지수. 11년 통합 지수를 만든 것이 아니다.')
figsave(p1,'01_bcai_profile.png',10)
tw<-a[count%in%c('0-2','3-0')];tw<-rbind(tw[,.(year,count,value=index,척도='시즌 시작값으로 나눈 BCAI')],tw[,.(year,count,value,척도='나누기 전의 평균 공격가치 W')])
tw[,척도:=factor(척도,levels=c('시즌 시작값으로 나눈 BCAI','나누기 전의 평균 공격가치 W'))]
p2<-ggplot(tw,aes(year,value,colour=count,group=count))+geom_line(linewidth=.8)+geom_point(size=2.6)+facet_wrap(~척도,ncol=1,scales='free_y')+scale_x_continuous(breaks=2015:2025,labels=function(x)substr(x,3,4))+scale_colour_manual(values=c('#276f96','#b36938'))+labs(title='지수와 원래 공격가치는 구별해야 한다',subtitle='같은 카운트의 연도별 값 · 2015–2025, 11시즌\n가로축 15=2015년, 25=2025년',x='시즌',y='위: 지수 / 아래: W',colour='카운트',caption='출처: BCAI-OBS 저장 결과; bcai_all_132.csv\n분모: 해당 카운트 도달 타석. 시즌별 사건 가중치가 다르다.\n두 패널의 축과 단위가 다르며, 선의 변화는 연도 차이 검정 결과가 아니다.')
figsave(p2,'02_index_and_W.png',10)
sb<-b[model=='pitch_sb'&level=='count'&count%in%c('0-2','1-2','2-2')];sb[,시기:=ifelse(game_year<2024,'추가: 연도별 적합','기준: 2시즌 공유 적합')]
p3<-ggplot(sb,aes(delta,factor(game_year,levels=2025:2015),colour=시기))+geom_vline(xintercept=0,colour='#555555')+geom_segment(aes(x=family95_low,xend=family95_high,yend=factor(game_year,levels=2025:2015)),linewidth=.8)+geom_point(size=2.5)+facet_wrap(~count,ncol=1)+scale_colour_manual(values=c('#197b78','#ad6941'))+labs(title='0-2·1-2와 2-2는 같은 두 스트라이크일까?',subtitle='S−B: 오른쪽은 존 밖, 왼쪽은 존 안의 허용 W가 낮음',x='존 안 − 존 밖 · ΔW',y='시즌',colour=NULL,caption='출처: BCAP-PITCH-SB, bcap_all_2552_screened.csv\n각 행 분모는 지원 투구; 원 CSV에 n/n_all 기록. 3카운트 모두 매년 지원.\n선: 저장된 고정 점수 경기 군집 조건부 구간(추가 255, 기준 219 보정).\n전체 학습 변동·11년 전체 동시 보장 없음. 연도 차이 검정 아님.')
figsave(p3,'03_location_years.png',16)
swfig<-b[model=='swing'&level=='region',.(n=.N),by=.(game_year,구역=ifelse(region=='CENTER','존 안 · 매년 12칸','존 밖 · 매년 48칸'),status)]
swfig[,구역:=factor(구역,levels=c('존 안 · 매년 12칸','존 밖 · 매년 48칸'))]
colors<-c('양수·구간도 양수'='#167f77','양수·구간 불명확'='#9ac8bd','음수·구간도 음수'='#b86f37','음수·구간 불명확'='#e7c39e','자료 부족'='#d2d7db')
p4<-ggplot(swfig,aes(factor(game_year),n,fill=status))+geom_col(width=.78)+coord_flip()+facet_wrap(~구역,ncol=1,scales='free_x')+scale_fill_manual(values=colors,drop=FALSE)+labs(title='존 밖 테이크는 반복됐지만, 빈칸은 남았다',subtitle='스윙−테이크: 양수는 스윙, 음수는 테이크 방향\n2024·2025는 공유 적합의 연도별 하위 결과',x='시즌',y='카운트 × 구역의 보고 칸 수',fill=NULL,caption='출처: BCAP-SWING region 660행; bcap_all_2552_screened.csv\n존 안: 12카운트. 존 밖: 12카운트×4구역; 모서리 중복, 독립 실험 아님.\n회색은 자료 부족으로 수치 보류. 구간이 0을 포함하면 방향 불명확.\n저장된 연도별 조건부 구간이며 전체 학습 변동은 미포함.')+theme(legend.text=element_text(size=10))
figsave(p4,'04_swing_support.png',13)
pg<-b[level=='count'&((model=='pitch'&count=='3-0')|(model=='pitch_ff'&count=='3-2'))];pg[,질문:=ifelse(model=='pitch','3-0 · FB−NFB','3-2 · 포심−비포심')]
p5<-ggplot(pg,aes(delta,factor(game_year,levels=2025:2015)))+geom_vline(xintercept=0,colour='#777777')+geom_segment(aes(x=family95_low,xend=family95_high,yend=factor(game_year,levels=2025:2015)),colour='#507c82',na.rm=T)+geom_point(aes(colour=game_year<2024),size=2.8,na.rm=T)+geom_text(data=pg[support_gate==FALSE],aes(x=.06,label='자료 부족'),colour='#666666',size=4)+facet_wrap(~질문,ncol=1,scales='free_x')+scale_colour_manual(values=c('#ad6941','#197b78'),labels=c('기준 공유 적합','추가 연도별 적합'))+labs(title='구종도 일부 방향은 여러 해에 반복됐다',subtitle='두 비교 모두 양수면 뒤쪽 구종의 허용 W가 낮음',x='ΔW · 구종 분류별 자체 지원 표본',y='시즌',colour=NULL,caption='출처: BCAP-PITCH / PITCH-FF 저장 결과; fb_30_support.csv 및 전체 표\n추가 9년: FB 3-0 지원 8년, FF 3-2 지원 9년. 2020 FB 수치는 숨김.\n선은 조건부 보정 구간; 두 모듈의 표본·행동 정의가 다름.\n관찰 반복이며 최적 구종·연도 효과의 인과 증명이 아니다.')
figsave(p5,'05_pitch_patterns.png',13)
fwrite(unique(rbindlist(inputs)),file.path(out,'audit/source_hashes.csv'),bom=TRUE)
cat('WINDOW TOTALS\n');print(summary_counts[window%in%c('added_2015_2023','all_2015_2025')],nrows=40)
cat('DENOMINATORS\n');print(denom)
cat('BCAI SENS\n');print(ai_show,nrows=20)
cat('2026\n');print(suppa[count%in%c('0-2','1-1','3-0','3-2')]);print(suppb[level=='count'&count%in%c('3-0','3-2'),.(model,count,n,n_all,delta,family95_low,family95_high,support_gate)])
cat('EVENTS 3-0 BB\n');print(events[count=='3-0'&result=='BB',.(period,N,pct)])
cat('BASELINE SB EDGE\n');print(b[model=='pitch_sb'&level=='count'&game_year>=2024&count%in%c('0-1','1-1','2-2'),.(game_year,count,delta,family95_low,family95_high)])
cat('SUMMARY CORE\n');print(data.table(all_PA=sum(yearshape$eligible_PA),all_games=sum(yearshape$games)))
print(counts[window=='all_2015_2025'&level=='count'&model%in%c('pitch','pitch_ff','pitch_sb')&count%in%c('0-2','1-2','3-0','3-2')])
