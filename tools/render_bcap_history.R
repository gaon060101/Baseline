# Read-only analysis inputs; writes only the BCAP history reporting hub and figures.
suppressPackageStartupMessages({library(data.table);library(jsonlite);library(digest);library(ggplot2)})
if(length(commandArgs(trailingOnly=TRUE)))stop("Run without arguments from repository root")
column<-"columns/001-ball-count";runs<-file.path(column,"analysis/runs")
out<-file.path(column,"analysis/r_bcap_history_20260928");fig<-file.path(column,"figures/r_bcap_history_20260928")
years_target<-2015:2025;counts<-as.vector(t(outer(0:3,0:2,paste,sep="-")))
models<-c("pitch","pitch_sb","swing","pitch_ff")
titles<-c(pitch="구종: FB − NFB",pitch_sb="위치: S − B",swing="타자: 스윙(번트 포함) − 테이크",pitch_ff="구종: 포심 − 비포심")
mobile_titles<-c(pitch="FB − NFB",pitch_sb="S − B",swing="스윙 − 테이크",pitch_ff="포심 − 비포심")
ids<-c(pitch="BCAP-PITCH-v0.2.0",pitch_sb="BCAP-PITCH-SB-v0.1.0",swing="BCAP-SWING-v0.2.0",pitch_ff="BCAP-PITCH-FF-v0.1.0")
explanations<-c(pitch="FB는 FF·SI·FC, NFB는 명세의 나머지 분류입니다. 음수는 FB 쪽, 양수는 NFB 쪽의 보정된 허용 공격가치가 낮습니다.",
  pitch_sb="S는 공 중심의 기하학적 존 안, B는 존 밖입니다. 음수는 S 쪽, 양수는 B 쪽의 보정된 허용 공격가치가 낮습니다. 심판 판정·투수 의도 비교가 아닙니다.",
  swing="양수는 스윙 쪽, 음수는 테이크 쪽의 보정된 공격가치가 높습니다. 스윙에는 번트, 테이크에는 판정된 공과 몸에 맞는 공이 포함됩니다.",
  pitch_ff="포심은 FF, 비포심은 명세의 나머지 허용 구종입니다. 음수는 포심 쪽, 양수는 비포심 쪽의 보정된 허용 공격가치가 낮습니다. FB/NFB와 다른 비교입니다.")
sha<-function(path)digest(file=path,algo="sha256")
meta<-function(path)list(path=path,bytes=unname(file.info(path)$size),sha256=sha(path))
canon<-function(path)tolower(normalizePath(path,winslash="/",mustWork=TRUE))
esc<-function(x){x<-gsub("&","&amp;",as.character(x),fixed=TRUE);x<-gsub("<","&lt;",x,fixed=TRUE);x<-gsub(">","&gt;",x,fixed=TRUE);gsub('"',"&quot;",x,fixed=TRUE)}
fmt<-function(x)format(x,big.mark=",",scientific=FALSE,trim=TRUE)
md_table<-function(headers,rows)c(paste0("| ",paste(headers,collapse=" | ")," |"),paste0("| ",paste(rep("---",length(headers)),collapse=" | ")," |"),rows)
html_table<-function(headers,rows)paste0("<div class='table-scroll'><table><thead><tr>",paste0("<th>",headers,"</th>",collapse=""),"</tr></thead><tbody>",paste(rows,collapse="\n"),"</tbody></table></div>")
folders<-list.dirs(runs,full.names=TRUE,recursive=FALSE)
folders<-folders[grepl("^bcap_(pitch|pitch_sb|swing|pitch_ff)_r(_history)?__mlb_[0-9_]+__20260928__r[0-9]{2,}$",basename(folders))]
records<-list();ignored<-list();inputs<-list();cache<-list()
for(folder in folders){
  path<-file.path(folder,"manifest.json");if(!file.exists(path))next
  m<-tryCatch(fromJSON(path,simplifyVector=FALSE),error=function(e)NULL)
  if(is.null(m)){ignored[[length(ignored)+1L]]<-list(path=path,reason="보고서 생성 시 JSON 읽기 불가");next}
  if(!identical(m$status,"COMPLETE")){ignored[[length(ignored)+1L]]<-list(path=path,status=m$status);next}
  model<-m$run_config$model;ys<-as.integer(unlist(m$run_config$years))
  if(!model%in%models||!identical(m$model_id,unname(ids[model]))||!identical(m$model_status,"EXPERIMENTAL"))stop("Unexpected model/status: ",path)
  if(!length(ys)||anyDuplicated(ys)||!all(ys%in%years_target)){ignored[[length(ignored)+1L]]<-list(path=path,reason="2015~2025 전체 시즌 허브 범위 밖");next}
  for(y in ys)records[[length(records)+1L]]<-data.table(model=model,year=y,folder=folder,run_id=m$run_id,completed=m$finished_at_utc)
}
if(!length(records))stop("No COMPLETE R BCAP results in the requested range")
selected<-rbindlist(records);setorder(selected,model,year,completed,run_id);selected<-selected[,tail(.SD,1),by=.(model,year)]
required<-c("game_year","level","count","region","pitch_group","n_all","n","coverage","games","PA","rows0","rows1","Q0","Q1","delta","SE","nominal95_low","nominal95_high","family95_low","family95_high","action0","action1","support_gate","evidence")
for(folder in unique(selected$folder)){
  path<-file.path(folder,"manifest.json");m<-fromJSON(path,simplifyVector=FALSE);inputs[[length(inputs)+1L]]<-meta(path)
  for(filename in c("year_values.csv","action_values.csv","checks.json","metrics.json")){
    p<-file.path(folder,"artifacts",filename)
    registered<-Filter(function(z)basename(z$path)==filename,m$outputs)
    if(length(registered)!=1||!file.exists(p)||canon(p)!=canon(registered[[1]]$path)||sha(p)!=registered[[1]]$sha256)stop("Saved output hash mismatch: ",p)
    inputs[[length(inputs)+1L]]<-meta(p)
  }
  checks<-fromJSON(file.path(folder,"artifacts/checks.json"),simplifyVector=FALSE)
  metrics<-fromJSON(file.path(folder,"artifacts/metrics.json"),simplifyVector=FALSE)
  if(!identical(checks$status,"PASS")||!isTRUE(metrics$all_fit_converged))stop("Saved checks/convergence not PASS")
  d<-fread(file.path(folder,"artifacts/year_values.csv"),encoding="UTF-8")
  if(!all(required%in%names(d))||anyDuplicated(d[,.(game_year,level,count,region,pitch_group)]))stop("Invalid year table")
  d[,support_gate:=as.logical(support_gate)]
  if(anyNA(d$support_gate)||any(d$n<0|d$n_all<d$n|d$rows0+d$rows1!=d$n))stop("Invalid support or denominator")
  if(any(!is.finite(as.matrix(d[support_gate==TRUE,.(Q0,Q1,delta,SE,nominal95_low,nominal95_high,family95_low,family95_high)]))))stop("Nonfinite supported estimates")
  finite<-d[is.finite(delta)&is.finite(Q0)&is.finite(Q1)]
  if(nrow(finite)&&max(abs(finite$Q1-finite$Q0-finite$delta))>1e-10)stop("Q1-Q0 identity failure")
  if(any(d[support_gate==TRUE]$family95_low>d[support_gate==TRUE]$family95_high))stop("Invalid intervals")
  if(!setequal(d$game_year,as.integer(unlist(m$run_config$years))))stop("Manifest/year mismatch")
  for(y in unique(d$game_year)){
    z<-d[game_year==y];ct<-z[level=="count"];ov<-z[level=="overall"]
    if(nrow(ct)!=12||!setequal(ct$count,counts)||nrow(ov)!=1)stop("Missing annual overall/count results")
    if(sum(ct$n)!=ov$n||sum(ct$n_all)!=ov$n_all)stop("Annual count denominator mismatch")
  }
  if(sum(d[level=="overall"]$n)!=metrics$support||sum(d[level=="overall"]$n_all)!=metrics$n)stop("Metrics support totals mismatch")
  family<-as.numeric(m$configuration$comparison_family)
  if(length(family)!=1||!is.finite(family)||family<1)stop("Unknown comparison family")
  cache[[folder]]<-list(m=m,d=d,family=family)
}
blocks<-list();sample_blocks<-list()
for(i in seq_len(nrow(selected))){
  r<-selected[i];src<-cache[[r$folder]];d<-copy(src$d[game_year==r$year]);m<-src$m
  shared<-length(unlist(m$run_config$years))>1
  scope<-if(shared)"2024·2025 공유 적합의 연도 하위집단" else "해당 연도 안에서 별도 적합"
  first<-last<-NA_character_
  if(!is.null(m$preparation_details$schedule)){
    schedule<-rbindlist(m$preparation_details$schedule,fill=TRUE)
    if("year"%in%names(schedule)&&nrow(schedule[year==r$year])==1){s<-schedule[year==r$year];first<-s$first;last<-s$last}
  }
  measurement<-if(r$year%in%c(2015,2016))"구속은 보정 PITCHf/x 기반; Statcast와 물리량 구간의 직접 비교 미검증" else "연도 간 측정·분류·표본 차이 가능"
  d[,`:=`(model=r$model,model_id=m$model_id,model_status="EXPERIMENTAL",run_id=r$run_id,comparison_family=src$family,
    fit_scope=scope,first_date=first,last_date=last,measurement_note=measurement,
    source_csv=file.path(r$folder,"artifacts/year_values.csv"),source_manifest=file.path(r$folder,"manifest.json"))]
  blocks[[i]]<-d;ov<-d[level=="overall"]
  sample_blocks[[i]]<-data.table(model=r$model,year=r$year,n_all=ov$n_all,n=ov$n,PA=ov$PA,games=ov$games,coverage=ov$coverage,
    supported_counts=sum(d[level=="count"]$support_gate),family=src$family,fit_scope=scope,run_id=r$run_id)
}
summary<-rbindlist(blocks,fill=TRUE);setorder(summary,model,game_year,level,count,region,pitch_group)
samples<-rbindlist(sample_blocks);samples[,model_order:=match(model,models)];setorder(samples,model_order,-year);samples[,model_order:=NULL]
pending<-rbindlist(lapply(models,function(mm){missing<-setdiff(years_target,samples[model==mm]$year);data.table(model=rep(mm,length(missing)),year=missing)}))
dir.create(out,recursive=TRUE,showWarnings=FALSE);dir.create(fig,recursive=TRUE,showWarnings=FALSE)
fwrite(summary,file.path(out,"summary.csv"),bom=TRUE)
font<-if(.Platform$OS.type=="windows")"Malgun" else "sans";if(.Platform$OS.type=="windows")windowsFonts(Malgun=windowsFont("Malgun Gothic"))
png_paths<-character();chart_sections<-list();count_axis_checks<-list()
check_count_axis<-function(plot,chart){
  panels<-ggplot_build(plot)$layout$panel_params
  labels<-lapply(panels,function(panel)as.character(panel$y$get_labels()))
  if(!length(labels)||!all(vapply(labels,function(x)identical(x,rev(counts)),logical(1))))stop("Unexpected count axis order: ",chart)
  legacy_velocity<-any(plot$data$game_year%in%c(2015,2016))
  velocity_caption<-grepl("구속: 보정 PITCHf/x",plot$labels$caption,fixed=TRUE)
  if(legacy_velocity&&!velocity_caption)stop("Missing legacy velocity measurement caption: ",chart)
  count_axis_checks[[length(count_axis_checks)+1L]]<<-list(chart=chart,panels=length(labels),labels_top_to_bottom=rev(labels[[1]]),
    legacy_velocity_caption_required=legacy_velocity,legacy_velocity_caption_present=velocity_caption,passed=TRUE)
}
for(mm in models){
  z<-copy(summary[model==mm&level=="count"]);if(!nrow(z))next
  yy<-sort(unique(z$game_year));z[,count_plot:=factor(count,levels=rev(counts))]
  z[,facet_label:=factor(paste0(game_year,ifelse(grepl("공유",fit_scope)," · 공유 적합"," · 연도별 적합")),levels=paste0(yy,ifelse(yy%in%z[grepl("공유",fit_scope)]$game_year," · 공유 적합"," · 연도별 적합")))]
  p<-ggplot(z,aes(x=delta,y=count_plot))+geom_vline(xintercept=0,linetype="dashed",color="#718596")+
    geom_segment(data=z[support_gate==TRUE],aes(x=family95_low,xend=family95_high,yend=count_plot),color="#7893A8",linewidth=.9)+
    geom_point(data=z[support_gate==TRUE],color="#174D72",size=2.6)+
    geom_text(data=z[support_gate==FALSE],aes(x=0,label="자료 부족"),color="#8B5C4D",size=4,family=font)+
    facet_wrap(~facet_label,ncol=min(3,length(yy)))+scale_y_discrete(limits=rev(counts),drop=FALSE)+
    labs(title=titles[mm],subtitle="카운트별 관찰상 보정 비교 · 지원 기준을 통과한 값만 표시",x="최종 타석 공격가치 차이 (W / 선택된 현재 투구행)",y="투구 전 카운트",
      caption=paste0("선: 고정 점수 경기 군집 조건부 구간 · Bonferroni 보정수는 표 참조\n보조 모형 전체 학습 변동·경기 간 선수 의존성 미포함 · 실제 95% 포함률 미검증\n별도 연도 사이의 차이 검정 아님 · 인과 효과·행동 추천 아님 · MLB Statcast / Baseline",
        if(any(yy%in%c(2015,2016)))paste0("\n",paste(yy[yy%in%c(2015,2016)],collapse="·"),"년 구속: 보정 PITCHf/x · 2017년 이후와 측정 차이 유의") else ""))+
    theme_minimal(base_size=15,base_family=font)+theme(panel.grid.minor=element_blank(),strip.text=element_text(face="bold",size=14),
      plot.title=element_text(size=25,face="bold"),plot.subtitle=element_text(size=15),plot.caption=element_text(size=11,hjust=0),plot.margin=margin(22,24,18,20))
  path<-file.path(fig,paste0(mm,"_count_history.png"));check_count_axis(p,basename(path));png(path,width=max(1250,620*min(3,length(yy))),height=460+850*ceiling(length(yy)/3),res=150,bg="white",type=if(.Platform$OS.type=="windows")"windows" else "cairo");print(p);dev.off();png_paths<-c(png_paths,path)
  mobile<-list()
  for(y in rev(yy)){
    one<-z[game_year==y]
    fit_label<-if(any(grepl("공유",one$fit_scope)))"2024·2025 공유 적합의 연도별 결과" else "해당 연도 안에서 별도 적합"
    pm<-ggplot(one,aes(x=delta,y=count_plot))+geom_vline(xintercept=0,linetype="dashed",color="#718596")+
      geom_segment(data=one[support_gate==TRUE],aes(x=family95_low,xend=family95_high,yend=count_plot),color="#6F8EA4",linewidth=1.3)+
      geom_point(data=one[support_gate==TRUE],color="#174D72",size=4)+
      geom_text(data=one[support_gate==FALSE],aes(x=0,label="자료 부족"),color="#8B5C4D",size=6,family=font)+
      scale_x_continuous(n.breaks=4)+scale_y_discrete(limits=rev(counts),drop=FALSE)+
      labs(title=paste0(y,"년 · ",mobile_titles[mm]),subtitle=paste0(fit_label,"\n관찰상 보정 비교",if(mm=="swing")" · 번트 포함" else ""),
        x="공격가치 차이 ΔW",y=NULL,
        caption=paste0("선: 경기 군집 조건부 구간 (보정 ",unique(one$comparison_family),")\nW / 선택된 현재 투구행 · 인과 효과 아님",
          if(y%in%c(2015,2016))"\n구속: 보정 PITCHf/x · 2017년 이후와 측정 차이 유의" else "",
          "\nMLB Statcast · Baseline / EXPERIMENTAL"))+
      theme_minimal(base_size=18,base_family=font)+theme(panel.grid.minor=element_blank(),
        axis.text.y=element_text(size=20,color="#193446"),axis.text.x=element_text(size=18,color="#193446"),
        axis.title.x=element_text(size=20,margin=margin(t=14)),
        plot.title=element_text(size=25,face="bold"),plot.subtitle=element_text(size=16,lineheight=1.15,margin=margin(b=14)),
        plot.caption=element_text(size=14,hjust=0,lineheight=1.15,margin=margin(t=18)),plot.margin=margin(22,22,20,20))
    mobile_name<-paste0(mm,"_",y,"_count_mobile.png");mobile_path<-file.path(fig,mobile_name)
    check_count_axis(pm,mobile_name)
    png(mobile_path,width=900,height=1350,res=150,bg="white",type=if(.Platform$OS.type=="windows")"windows" else "cairo");print(pm);dev.off()
    png_paths<-c(png_paths,mobile_path)
    mobile[[length(mobile)+1L]]<-list(year=y,fit=fit_label,image=paste0("../../figures/r_bcap_history_20260928/",mobile_name))
  }
  chart_sections[[mm]]<-list(title=unname(titles[mm]),text=unname(explanations[mm]),image=paste0("../../figures/r_bcap_history_20260928/",mm,"_count_history.png"),mobile=mobile)
}
status_headers<-c("모델","완료 연도","미완료 연도","완료 / 목표")
status_values<-lapply(models,function(mm)c(titles[mm],if(nrow(samples[model==mm]))paste(sort(samples[model==mm]$year),collapse="·") else "없음",
  if(nrow(pending[model==mm]))paste(pending[model==mm]$year,collapse="·") else "없음",paste0(nrow(samples[model==mm])," / 11")))
status_md<-vapply(status_values,function(x)paste0("| ",paste(x,collapse=" | ")," |"),character(1))
status_html<-vapply(status_values,function(x)paste0("<tr>",paste0("<td>",esc(x),"</td>",collapse=""),"</tr>"),character(1))
sample_headers<-c("모델·시즌","적격 투구행","지원 투구행","지원 타석","지원 경기","지원률","지원 카운트","보정수","적합 범위","근거")
sample_md<-sample_html<-character()
for(i in seq_len(nrow(samples))){s<-samples[i];x<-c(paste0(titles[s$model]," · ",s$year),fmt(s$n_all),fmt(s$n),fmt(s$PA),fmt(s$games),sprintf("%.1f%%",s$coverage*100),paste0(s$supported_counts,"/12"),s$family,s$fit_scope)
  csv<-paste0("../runs/",s$run_id,"/artifacts/year_values.csv");manifest<-paste0("../runs/",s$run_id,"/manifest.json")
  sample_md<-c(sample_md,paste0("| ",paste(c(x,paste0("[CSV](",csv,") · [기록](",manifest,")")),collapse=" | ")," |"))
  sample_html<-c(sample_html,paste0("<tr>",paste0("<td>",esc(x),"</td>",collapse=""),"<td><a href='",csv,"'>CSV</a> · <a href='",manifest,"'>기록</a></td></tr>"))
}
warnings<-c("모든 모델은 EXPERIMENTAL이다. R 수치 확인과 계산 완료가 인과성·행동 추천·외부 일반화의 검증을 뜻하지 않는다.",
  "delta = Q1 − Q0이며 단위는 W / 선택된 현재 투구행이다. BCAI처럼 0-0=100인 지수가 아니고, PA 전체 효과로 합산할 수 없다. 같은 타석의 여러 투구행이 포함될 수 있다.",
  "구간은 저장된 OOF 점수를 고정한 경기 군집 조건부 근사다. 보조 모형의 전체 학습 변동, 경기 간 같은 선수의 의존성, 외부 가중치 추정 오차는 포함하지 않는다. 실제 95% 포함률은 미검증이다.",
  "Bonferroni 보정수는 각 실행 manifest의 실제 설정을 표시했다. 전체 역사 연도·모든 모형을 합친 동시 보장을 뜻하지 않는다. 지원 기준 통과와 구간의 방향 판정은 서로 다르며, 구간이 0을 포함한다고 동등성이 입증되는 것도 아니다.",
  "2024·2025 표는 두 시즌을 함께 학습한 OOF 모형의 연도 하위집단이다. 과거 연도는 그 연도 안에서 별도로 적합한다. 서로 다른 연도의 delta나 저장 구간을 빼서 새로운 연도 차이 검정을 만들지 않았다.",
  "지원 기준을 통과하지 못한 카운트는 주 그림에서 수치·구간을 숨기고 자료 부족으로 표시한다. 원 CSV와 summary.csv에는 감사 목적의 원 수치·지원 플래그를 보존한다. 주 그림은 count 수준만 다룬다.",
  "SWING의 구역·구종별 결과가 있으면 summary.csv에 함께 남긴다. 높음/낮음과 몸쪽/바깥쪽의 모서리는 중복 포함되므로 구역 표본을 합산하지 않는다. FB/NFB에는 FA/Other 분류의 한계가 남는다.",
  "2015·2016 구속은 보정 PITCHf/x 기반이고 2017 이후 Statcast와 물리량 구간의 직접 비교는 미검증이다. 2020 단축 시즌의 표본·기간 차이를 유지한다. 2026 S/B·SWING은 좌표·존 정의 변경으로 측정 보류이며 이 허브에 포함하지 않는다.",
  "완료 타석·유효 결과·지원 표본 선택과 미측정 의도·공 품질·컨디션이 남는다. 일정 경기 집합이 맞아도 모든 투구·타석의 완전성을 보장하지 않는다.")
guide<-c("report.html은 표와 그림을 함께 보는 화면, report.md는 편집 가능한 보고서다.","summary.csv는 모든 저장 집계의 복사본과 실행·원 CSV 경로를 포함한다. support_gate와 level을 확인하고 사용한다.","블로그에는 '연도별 크게 보기'의 모델·연도별 900px PNG를 사용한다. 여러 해를 한 번에 비교할 때는 기존 종합 그림을 사용한다. 제목·단위·출처·해석 주의를 함께 보존한다.","report_validation.json은 선택 실행, 집계 파일 해시, 내부 산술·분모·링크 확인을 담는다. 새 완료 실행이 생기면 아래 렌더 명령으로 허브만 갱신한다.")
generated<-format(Sys.time(),"%Y-%m-%d %H:%M:%S %Z")
lead<-sprintf("완료된 R 결과 **%s개 모델·시즌 조합 / 목표 44개**를 모았다. 계산 중·실패·미실행 조합에는 결과를 채우지 않았다. 각 모델의 현재 상태는 **EXPERIMENTAL**이다.",nrow(samples))
md<-c("# BCAP 과거 연도 결과 모음","",lead,"",paste0("갱신: ",generated),"",md_table(status_headers,status_md),"",
  "## 무엇을 비교한 값인가?","","그림은 같은 지원 표본에서 보정한 두 행동의 최종 타석 공격가치 차이다. 점은 카운트별 추정, 선은 저장된 조건부 보정 구간이다. 차이의 부호만으로 행동을 권하지 않는다.","",
  unlist(lapply(chart_sections,function(x)c(paste0("### ",x$title),"",x$text,"",paste0("![",x$title,"](",x$image,")"),"",
    "**연도별 크게 보기 — 블로그용 900px PNG**","",
    vapply(x$mobile,function(m)paste0("- [",m$year,"년 크게 보기](",m$image,") · ",m$fit),character(1)),"",
    "연도별 그림의 가로축 범위는 자료에 맞게 달라질 수 있다. 선의 단위와 눈금을 함께 읽는다. 구간은 전체 학습 변동을 포함하지 않는 조건부 근사이며 행동 추천이 아니다.",""))),
  "## 표본과 근거","","적격·지원 수는 투구행 기준이다. 지원 타석과 지원 경기는 그 행들에 포함된 고유 타석·경기이며, 모델끼리 합산하지 않는다.","",md_table(sample_headers,sample_md),"",
  "[전체 집계·지원 플래그 CSV](summary.csv) · [입력 해시·확인 기록](report_validation.json)","",
  "## 해석할 때 지킬 범위","",paste0("- ",warnings),"","## 파일을 다시 사용하는 방법","",paste0("- ",guide),"",
  "```powershell","./tools/run_r.ps1 -Script tools/render_bcap_history.R","```","",
  "이 명령은 완료 실행 중 모델·연도별 최신 결과를 선택하고 원 집계 파일의 해시를 확인한다. 통계 재적합·다운로드·과거 실행 변경·진행 기록 변경·원고 편집·외부 게시를 수행하지 않는다.")
writeLines(enc2utf8(md),file.path(out,"report.md"),useBytes=TRUE)
style<-"body{margin:0;background:#f3f5f7;color:#193446;font:17px/1.75 'Malgun Gothic',sans-serif}main{max-width:1120px;margin:auto;padding:36px 24px 64px}h1{font-size:2.1rem;line-height:1.35}h2{margin-top:2.4rem}h3{margin-top:1.8rem}a{color:#19658a;text-underline-offset:3px}.card,figure{background:white;border:1px solid #d8e3e8;border-radius:14px;padding:22px;margin:22px 0}.badge{display:inline-block;background:#ead8ce;color:#703b22;padding:4px 12px;border-radius:8px;font-weight:bold}.muted,figcaption{font-size:.88rem;color:#5b6d78}.table-scroll{overflow-x:auto;border:1px solid #d8e3e8;border-radius:10px}table{border-collapse:collapse;width:100%;background:white;font-size:.88rem}th,td{padding:10px 14px;white-space:nowrap;border-bottom:1px solid #e5edf1;text-align:left}thead{background:#e9f0f3}figure img{width:100%;height:auto;display:block}figcaption{margin-top:10px}li{margin:12px 0}pre{white-space:pre-wrap;background:#e7eef2;padding:16px;border-radius:10px}code{font:14px/1.6 Consolas,monospace;overflow-wrap:anywhere}.year-group{margin:20px 0 36px}.year-group h4{margin:12px 0;font-size:1.15rem}.year-panel{background:white;border:1px solid #cadbe5;border-radius:12px;margin:10px 0;overflow:hidden}.year-panel summary{cursor:pointer;padding:15px 18px;font-weight:bold;color:#174D72;background:#eaf2f7}.mobile-figure{padding:0;border:0;margin:0 auto;max-width:900px;border-radius:0}.mobile-figure figcaption{padding:0 16px 16px}.year-note{font-size:.92rem;color:#536b7b}@media(max-width:620px){main{padding:24px 16px 44px}h1{font-size:1.65rem}.card,figure{padding:12px}.mobile-figure{padding:0}.year-panel summary{padding:13px 14px}}"
html<-c("<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>BCAP 과거 연도 결과 모음</title><style>",style,"</style></head><body><main>",
  "<p class='muted'>Baseline · R 저장 결과 보고서</p><h1>카운트에 따른 행동 비교,<br>여러 해의 결과 모음</h1><span class='badge'>EXPERIMENTAL</span>",
  sprintf("<div class='card'><strong>목표 44개 모델·시즌 조합 중 %s개 완료</strong><p>완료된 저장 결과만 표시합니다. 계산 중·실패·미실행 조합에 수치를 채우지 않았습니다. 관찰상 보정 비교이며 행동 추천이 아닙니다.</p><p class='muted'>갱신: %s</p></div>",nrow(samples),generated),
  html_table(status_headers,status_html),"<h2>무엇을 비교한 값인가?</h2><p>같은 지원 표본에서 보정한 두 행동의 최종 타석 공격가치 차이입니다. 점은 카운트별 추정, 선은 저장된 조건부 보정 구간입니다. 부호만으로 행동을 권하지 않습니다.</p>",
  unlist(lapply(chart_sections,function(x)c(paste0("<h3>",esc(x$title),"</h3><p>",esc(x$text),"</p><figure><a href='",x$image,"'><img src='",x$image,"' alt='",esc(x$title),"'></a><figcaption>여러 해를 나란히 보는 종합 그림입니다. 자료 부족인 카운트의 수치·구간은 표시하지 않았습니다.</figcaption></figure>"),
    "<section class='year-group'><h4>연도별 크게 보기</h4><p class='year-note'>블로그용 900px 그림입니다. 연도를 누르면 크게 펼쳐집니다. 최신 완료 연도부터 표시합니다.</p>",
    vapply(seq_along(x$mobile),function(i){m<-x$mobile[[i]];paste0("<details class='year-panel'",if(i==1)" open" else "","><summary>",m$year,"년 · 크게 보기</summary><figure class='mobile-figure'><a href='",m$image,"'><img src='",m$image,"' alt='",m$year,"년 ",esc(x$title)," 모바일용 그림'></a><figcaption>",esc(m$fit)," · <a href='",m$image,"'>PNG 원본 열기</a></figcaption></figure></details>")},character(1)),
    "<p class='year-note'>연도별 그림의 가로축 범위는 자료에 맞게 달라질 수 있습니다. 선의 단위와 눈금을 함께 읽습니다. 구간은 전체 학습 변동을 포함하지 않는 조건부 근사이며 행동 추천이 아닙니다.</p></section>"))),
  "<h2>표본과 근거</h2><p>적격·지원 수는 투구행 기준입니다. 지원 타석·경기는 그 행들의 고유 타석·경기이며 모델끼리 합산하지 않습니다.</p>",html_table(sample_headers,sample_html),
  "<p><a href='summary.csv'>전체 집계·지원 플래그 CSV</a> · <a href='report_validation.json'>입력 해시·확인 기록</a></p><h2>해석할 때 지킬 범위</h2><ul>",paste0("<li>",esc(warnings),"</li>"),"</ul><h2>파일을 다시 사용하는 방법</h2><ul>",paste0("<li>",esc(guide),"</li>"),
  "</ul><pre><code>./tools/run_r.ps1 -Script tools/render_bcap_history.R</code></pre><p class='muted'>완료 실행 중 모델·연도별 최신 결과를 선택하고 집계 파일 해시를 확인합니다. 통계 재적합·다운로드·실행·진행 기록·원고·외부 게시물을 변경하지 않습니다. <a href='report.md'>보고서 Markdown</a></p></main></body></html>")
writeLines(enc2utf8(html),file.path(out,"report.html"),useBytes=TRUE)
mdtext<-paste(md,collapse="\n");htmltext<-paste(html,collapse="\n")
links<-regmatches(mdtext,gregexpr("\\]\\([^)]+\\)",mdtext))[[1]];links<-sub("^\\]\\(","",sub("\\)$","",links))
hl<-regmatches(htmltext,gregexpr("(?:href|src)='[^']+'",htmltext,perl=TRUE))[[1]];hl<-sub("^(?:href|src)='","",sub("'$","",hl),perl=TRUE)
links<-unique(c(links,hl));links<-links[!grepl("^(https?://|#)",links)]
missing<-links[links!="report_validation.json" & !file.exists(file.path(out,links))];if(length(missing))stop("Missing links: ",paste(missing,collapse=","))
if(!all(vapply(inputs,function(x)identical(x$sha256,sha(x$path)),logical(1))))stop("Saved inputs changed during rendering")
outputs<-c(file.path(out,c("report.md","report.html","summary.csv")),png_paths)
validation<-list(status="PASS",generated_at=generated,role="완료된 BCAP R 집계 결과 보고서; 재적합·연도 차이 추론 없음",model_status="EXPERIMENTAL",
  selected_model_years=as.data.frame(samples[,.(model,year,run_id)]),complete_model_years=nrow(samples),pending_model_years=as.data.frame(pending),target_model_years=44,
  summary_rows=nrow(summary),main_chart_rows=nrow(summary[level=="count"]),main_chart_supported_rows=nrow(summary[level=="count"&support_gate==TRUE]),
  main_chart_insufficient_rows=nrow(summary[level=="count"&support_gate==FALSE]),mobile_charts=nrow(samples),mobile_chart_width_px=900,
  inputs=inputs,inputs_unchanged=TRUE,ignored_runs=ignored,count_axis_checks=count_axis_checks,
  checks=list(complete_only=TRUE,source_hashes_match=TRUE,saved_checks_pass=TRUE,fit_convergence_pass=TRUE,unique_group_keys=TRUE,
    all_twelve_counts=TRUE,all_plot_count_axes_ordered=TRUE,unsupported_counts_keep_axis_position=TRUE,legacy_velocity_caption_present_where_required=TRUE,action_denominators_match=TRUE,annual_count_totals_match=TRUE,Q1_minus_Q0_identity=TRUE,supported_estimates_finite=TRUE,
    unsupported_points_hidden=TRUE,cross_year_difference_inference=FALSE,scores_or_bootstraps_loaded=FALSE,missing_local_links=as.list(missing),checked_links=length(links)),
  code=meta("tools/render_bcap_history.R"),outputs=lapply(outputs,meta))
write_json(validation,file.path(out,"report_validation.json"),pretty=TRUE,auto_unbox=TRUE,na="null",digits=NA)
cat("PASS: BCAP completed model-years",nrow(samples),"/44; summary rows",nrow(summary),"; main supported",validation$main_chart_supported_rows,"; insufficient",validation$main_chart_insufficient_rows,"\n")
