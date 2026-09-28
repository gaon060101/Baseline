# Saved-result renderer only. Run from the repository root; never fits or downloads.
suppressPackageStartupMessages({library(data.table); library(jsonlite); library(digest); library(ggplot2)})
if (length(commandArgs(trailingOnly=TRUE))) stop("Run without arguments from repository root")
column <- "columns/001-ball-count"
runs_root <- file.path(column,"analysis/runs")
out <- file.path(column,"analysis/r_history_20260928")
fig <- file.path(column,"figures/r_history_20260928")
reference_id <- "bcai_r_check__mlb_2024_2025__20260928__r02"
target_years <- 2015:2025
counts <- as.vector(t(outer(0:3,0:2,paste,sep="-")))
required <- c("year","count","N","value","index","SE","CI95_low","CI95_high","simultaneous95_low","simultaneous95_high")
sha <- function(path) digest(file=path,algo="sha256")
metadata <- function(path) list(path=path,bytes=unname(file.info(path)$size),sha256=sha(path))
esc <- function(x) {x <- gsub("&","&amp;",as.character(x),fixed=TRUE);x <- gsub("<","&lt;",x,fixed=TRUE);x <- gsub(">","&gt;",x,fixed=TRUE);gsub('"',"&quot;",x,fixed=TRUE)}
fmt <- function(x) format(x,big.mark=",",scientific=FALSE,trim=TRUE)
candidate_dirs <- list.dirs(runs_root,recursive=FALSE,full.names=TRUE)
candidate_dirs <- candidate_dirs[basename(candidate_dirs)==reference_id | grepl("^bcai_history__mlb_[0-9]{4}__[0-9]{8}__r[0-9]{2,}$",basename(candidate_dirs))]
records <- list(); ignored <- list()
for (folder in candidate_dirs) {
  path <- file.path(folder,"manifest.json")
  if (!file.exists(path)) next
  m <- tryCatch(fromJSON(path,simplifyVector=FALSE),error=function(e) NULL)
  if (is.null(m)) {ignored[[length(ignored)+1L]] <- list(path=path,reason="보고서 생성 시 JSON 읽기 불가");next}
  if (!identical(m$status,"COMPLETE")) {ignored[[length(ignored)+1L]] <- list(path=path,status=m$status);next}
  if (!identical(m$model_id,"BCAI-OBS-v1.0.0") || !identical(m$version,"1.0.0")) stop("Unexpected model: ",folder)
  years <- as.integer(unlist(m$parameters$years))
  if (!length(years) || anyDuplicated(years) || !all(years %in% target_years)) stop("Unexpected years: ",folder)
  if (basename(folder)==reference_id && !setequal(years,c(2024L,2025L))) stop("Reference years mismatch")
  if (basename(folder)!=reference_id && (length(years)!=1 || years>=2024)) stop("History run must contain one year through 2023")
  for (year in years) records[[length(records)+1L]] <- data.table(year=year,run_id=m$run_id,folder=folder,manifest_path=path,completed_at=m$completed_at)
}
if (!length(records)) stop("No COMPLETE saved runs found")
selected <- rbindlist(records)
setorder(selected,year,completed_at,run_id)
selected <- selected[,tail(.SD,1),by=year]
if (!all(c(2024L,2025L) %in% selected$year)) stop("Required completed reference run is unavailable")
inputs <- list(); cache <- list()
for (folder in unique(selected$folder)) {
  manifest_path <- file.path(folder,"manifest.json")
  m <- fromJSON(manifest_path,simplifyVector=FALSE)
  inputs[[length(inputs)+1L]] <- metadata(manifest_path)
  if (!identical(m$validation$status,"PASS") || !isTRUE(m$validation$inputs_unchanged)) stop("Saved validation not PASS: ",folder)
  files <- c("season_indices.csv","cohorts.csv","validation.json")
  for (filename in files) {
    path <- file.path(folder,"artifacts",filename)
    registered <- Filter(function(z) identical(gsub("\\\\","/",z$path),path),m$outputs)
    if (length(registered)!=1 || !file.exists(path) || !identical(sha(path),registered[[1]]$sha256)) stop("Output hash mismatch: ",path)
    inputs[[length(inputs)+1L]] <- metadata(path)
  }
  s <- fread(file.path(folder,"artifacts/season_indices.csv"),encoding="UTF-8")
  cohorts <- fread(file.path(folder,"artifacts/cohorts.csv"),encoding="UTF-8")
  if (!all(required %in% names(s)) || anyDuplicated(s[,.(year,count)])) stop("Invalid seasonal table: ",folder)
  if (any(!is.finite(as.matrix(s[,setdiff(required,"count"),with=FALSE])))) stop("Nonfinite results: ",folder)
  if (any(s$N<=0) || any(s$CI95_low>s$CI95_high) || any(s$simultaneous95_low>s$simultaneous95_high)) stop("Invalid denominators or intervals")
  if (sum(cohorts$eligible_PA)!=m$sample$eligible_PA || sum(cohorts$games)!=m$sample$games) stop("Cohort totals mismatch")
  coverage <- rbindlist(m$coverage,fill=TRUE)
  if (!all(coverage$schedule_match) || anyDuplicated(coverage$year)) stop("Invalid coverage metadata")
  if (!setequal(s$year,cohorts$year) || !setequal(s$year,coverage$year)) stop("Season metadata mismatch")
  for (y in unique(s$year)) {
    if (!setequal(s[year==y]$count,counts) || nrow(s[year==y])!=12) stop("Missing count")
    if (abs(s[year==y & count=="0-0"]$index-100)>1e-9 || s[year==y & count=="0-0"]$N!=cohorts[year==y]$eligible_PA) stop("Baseline mismatch")
    if (cohorts[year==y]$games!=coverage[year==y]$games) stop("Game metadata mismatch")
  }
  cache[[folder]] <- list(manifest=m,season=s,cohorts=cohorts,coverage=coverage)
}
blocks <- list(); sample_blocks <- list()
for (i in seq_len(nrow(selected))) {
  item <- selected[i]; src <- cache[[item$folder]]; y <- item$year
  s <- copy(src$season[year==y]); c <- src$cohorts[year==y]; v <- src$coverage[year==y]
  note <- if(y==2020) "단축 시즌 — 기간·경기 수가 다른 시즌과 다름" else if(v$scope!="full_regular_season") "부분 기간 — cutoff와 자료 범위 확인" else "정규시즌 전체 일정 대조"
  s[,`:=`(eligible_PA=c$eligible_PA,games=c$games,first_date=v$first,last_date=v$last,
    scope=v$scope,cutoff=v$cutoff,season_note=note,run_id=item$run_id,
    source_csv=file.path(item$folder,"artifacts/season_indices.csv"),source_manifest=item$manifest_path)]
  blocks[[i]] <- s
  sample_blocks[[i]] <- data.table(year=y,eligible_PA=c$eligible_PA,games=c$games,first=v$first,last=v$last,note=note,run_id=item$run_id)
}
summary <- rbindlist(blocks); summary[,count_order:=match(count,counts)];setorder(summary,year,count_order);summary[,count_order:=NULL]
samples <- rbindlist(sample_blocks);setorder(samples,-year)
completed <- sort(unique(summary$year));pending <- setdiff(target_years,completed)
generated <- format(Sys.time(),"%Y-%m-%d %H:%M:%S %Z")
completed_text <- paste(completed,collapse="·")
pending_text <- if(length(pending)) paste(pending,collapse="·") else "없음"
gap_note <- if(length(pending)) paste0("미완료 연도: ",pending_text,". 이 표는 2015~2025의 연속 완료 결과가 아니다.") else "2015~2025의 모든 목표 시즌 계산이 완료됐다."
dir.create(out,recursive=TRUE,showWarnings=FALSE);dir.create(fig,recursive=TRUE,showWarnings=FALSE)
fwrite(summary,file.path(out,"summary.csv"),bom=TRUE)
font <- if(.Platform$OS.type=="windows") "Malgun" else "sans"
if(.Platform$OS.type=="windows") windowsFonts(Malgun=windowsFont("Malgun Gothic"))
z <- copy(summary); z[,`:=`(year_plot=factor(year,levels=rev(completed)),count_plot=factor(count,levels=rev(counts)),
  strike=factor(sub("^[0-3]-","",count),levels=0:2),balls=as.integer(substr(count,1,1)),label=sprintf("%.1f",index))]
limits <- c(min(50,floor(min(z$index)/10)*10),max(190,ceiling(max(z$index)/10)*10))
colors <- scale_fill_gradient2(low="#185A84",mid="#F7F7F2",high="#B64C30",midpoint=100,limits=limits,name="BCAI")
blog_theme <- theme_minimal(base_size=18,base_family=font)+theme(panel.grid=element_blank(),axis.title=element_text(size=16),
  axis.text=element_text(color="#233747"),plot.title=element_text(size=25,face="bold"),plot.subtitle=element_text(size=15),
  plot.caption=element_text(size=12,hjust=0,lineheight=1.2),legend.position="bottom",plot.margin=margin(22,24,18,20))
caption <- "출처: MLB Statcast · BCAI-OBS-v1.0.0 저장 결과\n각 시즌 0-0 = 100. 색·수치는 관찰 평균이며 연도 차이의 유의성·절대 리그 실력이 아닙니다."
save_plot <- function(plot,name,width,height) {png(file.path(fig,name),width=width,height=height,res=150,bg="white",type=if(.Platform$OS.type=="windows") "windows" else "cairo");print(plot);dev.off()}
overview <- ggplot(z,aes(x=factor(year,levels=completed),y=count_plot,fill=index))+geom_tile(color="white",linewidth=1)+
  geom_text(aes(label=label,color=abs(index-100)>45),size=5.1,family=font)+scale_color_manual(values=c("FALSE"="#172D3A","TRUE"="white"),guide="none")+colors+
  labs(title="볼카운트별 공격가치, 여러 해를 나란히 보기",subtitle=paste0("계산 완료 ",length(completed),"개 시즌 · 수치는 BCAI 점추정 · 미완료 연도: ",pending_text),
    x="시즌",y="투구 전 볼카운트",caption=caption)+blog_theme
save_plot(overview,"bcai_year_count_heatmap.png",max(1350,220+length(completed)*170),1650)
for(b in 0:3) {
  p <- ggplot(z[balls==b],aes(x=strike,y=year_plot,fill=index))+geom_tile(color="white",linewidth=1.2)+
    geom_text(aes(label=label,color=abs(index-100)>45),size=6.5,family=font)+scale_color_manual(values=c("FALSE"="#172D3A","TRUE"="white"),guide="none")+colors+
    labs(title=paste0(b,"볼에서 스트라이크가 늘어나면?"),subtitle=paste0("시즌별 관찰 BCAI · 같은 색상 기준\n미완료 연도: ",pending_text),x="스트라이크",y="시즌",
      caption="MLB Statcast · BCAI-OBS-v1.0.0\n각 시즌 0-0 = 100. 인과 효과·승률이 아닙니다.")+blog_theme
  save_plot(p,paste0("bcai_",b,"balls_blog.png"),1050,max(850,420+length(completed)*100))
}
sample_rows <- vapply(seq_len(nrow(samples)),function(i) {
  s <- samples[i];sprintf("| %s | %s | %s | %s~%s | %s | [결과](../runs/%s/artifacts/season_indices.csv) · [기록](../runs/%s/manifest.json) |",
    s$year,fmt(s$eligible_PA),fmt(s$games),s$first,s$last,s$note,s$run_id,s$run_id)
},character(1))
matrix_rows <- vapply(counts,function(count_value) {
  x <- summary[count==count_value][order(year)]
  paste0("| ",count_value," | ",paste(sprintf("%.2f",x$index),collapse=" | ")," |")
},character(1))
lead <- sprintf("**2015~2025 목표 11개 시즌 중 %s개 시즌의 R 계산이 완료됐다.** 이 화면은 완료된 저장 결과만 모으며, 계산 중·실패·미실행 연도의 수치를 채우지 않는다.",length(completed))
reproduction <- "2024·2025는 기존 Python의 BCAI 점추정·분모·제외 내역을 R로 재현했다. 과거 연도의 실행 완료는 해당 연도의 자료·내부 확인을 뜻하며 Python 교차 재현이나 모델의 검증 범위 확장을 자동으로 뜻하지 않는다."
interpretation <- c("BCAI는 해당 카운트에 도달한 타석의 최종 가중 공격가치를 그 시즌 0-0 평균과 비교한 값이다. 120은 시작점 대비 20% 높은 관찰 평균이며, 승률·인과 효과·최적 행동의 점수가 아니다.",
  "각 시즌을 서로 다른 기준 평균으로 정규화하므로 연도 간 절대 리그 실력이나 득점 환경의 우열을 읽을 수 없다. 이 표와 히트맵은 패턴을 탐색하기 위한 나란한 표시이며 연도 차이의 유의성 검정이 아니다.",
  "시즌별 개별·근사 동시 구간은 summary.csv와 원 결과표에 보존했다. 동시 구간은 각 실행의 정의를 따르며, 전체 역사 연도와 모든 비교를 한꺼번에 보장하는 구간은 아니다. 따로 실행한 단일 연도의 같은 seed 재표본을 임의로 짝지어 빼지 않았다.",
  "경기 단위 부트스트랩은 경기 안의 의존성을 반영하지만 경기 사이 동일 선수의 의존성과 외부 가중치 추정 오차까지 반영하지 않는다. 일정 경기 ID 일치는 경기 안의 투구·타석 완전성 보장이 아니다.",
  if(2020 %in% completed) "2020은 단축 시즌이며 실제 경기 수·관측 기간을 표에 별도 표시했다. 표본 크기가 다르므로 다른 시즌과 같은 정밀도로 간주하지 않는다." else "2020이 추가되면 단축 시즌의 실제 경기 수·관측 기간을 표에 별도 표시한다. 표본 크기가 다르므로 다른 시즌과 같은 정밀도로 간주하지 않는다.")
md <- c("# BCAI 과거 연도 결과 모음", "",lead,"",paste0("**",gap_note,"**"),"",paste0("- 완료: ",completed_text," (",length(completed),"개 시즌)"),
  paste0("- 미완료: ",pending_text," (",length(pending),"개 시즌; 계산 중·대기·실패 여부는 [진행 기록](progress.json) 확인)"),
  "- 2026은 이 전체 시즌 표에 포함하지 않는다. 별도 보조 비교의 실행 기록이 필요하다.",paste0("- 갱신: ",generated),"",
  "## 여러 해의 모양은 어떤가?","","색과 셀 안 숫자는 저장된 점추정값이다. 아래 비교만으로 변화가 확실하거나 차이가 없다고 판단하지 않는다.","",
  "![완료 연도별 12카운트 BCAI 히트맵](../../figures/r_history_20260928/bcai_year_count_heatmap.png)","",
  "## 표본과 결과의 출처","",reproduction,"","| 시즌 | 유효 타석 | 경기 | 관측 날짜 | 기간 구분 | 근거 |","| --- | ---: | ---: | --- | --- | --- |",sample_rows,"",
  "[합친 수치·구간 CSV](summary.csv) · [보고서 입력 해시와 확인 기록](report_validation.json) · [2024·2025 재현·연도 차이 해설](../runs/bcai_r_check__mlb_2024_2025__20260928__r02/report.md)","",
  "## 카운트별 점추정 표","",paste0("| 카운트 | ",paste(completed,collapse=" | ")," |"),paste0("| --- | ",paste(rep("---:",length(completed)),collapse=" | ")," |"),matrix_rows,"",
  "## 모바일 블로그용 그림","","연도 수가 늘어도 세 칸씩 읽도록 볼 수에 따라 나눴다. 네 그림은 같은 색상 범위를 쓴다.","",
  unlist(lapply(0:3,function(b) c(paste0("![",b,"볼에서 시즌별 BCAI](../../figures/r_history_20260928/bcai_",b,"balls_blog.png)"),""))),
  "## 해석할 때 남겨둘 선","",paste0("- ",interpretation),"",
  "## 파일 사용과 갱신 방법","","report.html은 그림과 표를 함께 보는 화면, report.md는 편집 가능한 보고서다. summary.csv는 시즌·카운트별 점추정·구간·분모와 원 실행 경로를 담으며, report_validation.json은 입력 해시와 확인 범위를 기록한다. 블로그에는 전체 히트맵이나 모바일용 0·1·2·3볼 PNG를 사용하고 단위·출처·해석 주의를 함께 남긴다.","","저장소 루트에서 아래 명령을 다시 실행하면 새로 완료된 연도를 읽고 이 허브와 그림만 갱신한다. 통계 재계산·다운로드·기존 실행 변경은 하지 않는다.","",
  "```powershell","./tools/run_r.ps1 -Script tools/render_bcai_history.R","```","",
  "연도별로 가장 최근 완료된 `bcai_history` 실행을 선택한다. 2024·2025의 기준 실행은 r02로 고정했다. 실패 기록은 포함하지 않고 보존한다. 원 결과 CSV·표본·검증 JSON의 해시와 12카운트·0-0 기준을 확인한 뒤 저장 결과만 표시한다. 기존 발행 원고·외부 게시물은 자동으로 변경하지 않는다.")
writeLines(enc2utf8(md),file.path(out,"report.md"),useBytes=TRUE)
html_sample_rows <- vapply(seq_len(nrow(samples)),function(i) {
  s<-samples[i];paste0("<tr><th>",s$year,"</th><td>",fmt(s$eligible_PA),"</td><td>",fmt(s$games),"</td><td>",s$first,"<br>~",s$last,"</td><td>",esc(s$note),"</td><td><a href='../runs/",s$run_id,"/artifacts/season_indices.csv'>CSV</a> · <a href='../runs/",s$run_id,"/manifest.json'>실행 기록</a></td></tr>")
},character(1))
html_matrix_rows <- vapply(counts,function(count_value) {x<-summary[count==count_value][order(year)];paste0("<tr><th>",count_value,"</th>",paste0("<td>",sprintf("%.2f",x$index),"</td>",collapse=""),"</tr>")},character(1))
html <- c("<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>BCAI 과거 연도 결과 모음</title>",
  "<style>body{margin:0;background:#f3f5f7;color:#183244;font:17px/1.75 'Malgun Gothic',sans-serif}main{max-width:1080px;margin:auto;padding:40px 26px 70px}h1{font-size:2.1rem;line-height:1.35}h2{font-size:1.4rem;margin-top:2.4rem}a{color:#176692;text-underline-offset:3px}.card,figure{background:white;border:1px solid #d9e3e9;border-radius:14px;padding:22px;margin:22px 0}.lead{font-size:1.15rem;font-weight:700}.muted{color:#576b79;font-size:.88rem}.status{display:flex;gap:14px;flex-wrap:wrap}.status div{background:#e6eef2;border-radius:10px;padding:12px 20px}.status strong{font-size:1.4rem}figure img{width:100%;height:auto;display:block}figcaption{font-size:.87rem;color:#576b79;margin-top:10px}.table-scroll{overflow-x:auto;border:1px solid #d9e3e9;border-radius:10px}table{border-collapse:collapse;width:100%;background:white;font-size:.9rem}th,td{padding:10px 14px;white-space:nowrap;border-bottom:1px solid #e5edf1;text-align:right}th:first-child,td:first-child{text-align:left}thead{background:#e8eff3}p{margin:1em 0;overflow-wrap:anywhere}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid figure{margin:0;padding:8px}li{margin:10px 0}code{font:14px/1.6 Consolas,monospace;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:#e6eef2;padding:16px;border-radius:10px}@media(max-width:620px){main{padding:24px 16px 46px}h1{font-size:1.7rem}.grid{grid-template-columns:1fr}.card,figure{padding:12px}.status div{padding:10px 14px}}</style></head><body><main>",
  "<p class='muted'>Baseline · BCAI-OBS-v1.0.0 · 저장 결과 보고서</p><h1>볼카운트의 가치,<br>여러 해를 나란히 보기</h1>",
  sprintf("<div class='card'><p class='lead'>목표 11개 시즌 중 %s개 시즌의 R 계산을 완료했습니다.</p><div class='status'><div>완료 <strong>%s</strong>개</div><div>미완료 <strong>%s</strong>개</div></div><p>완료: %s</p><p>미완료: %s</p><p class='muted'>완료 결과만 표시합니다. 계산 중·대기·실패의 구분은 <a href='progress.json'>진행 기록</a>을 따릅니다. 2026 보조 비교는 이 표에 포함하지 않았습니다.<br>갱신: %s</p></div>",length(completed),length(completed),length(pending),completed_text,pending_text,generated),
  paste0("<p class='lead'>",esc(gap_note),"</p>"),
  "<h2>여러 해의 모양은 어떤가?</h2><p>색과 숫자는 카운트별 관찰 BCAI입니다. 각 시즌의 0-0이 100이며, 아래 그림만으로 연도 차이가 확실하거나 차이가 없다고 판단하지 않습니다.</p>",
  "<figure><a href='../../figures/r_history_20260928/bcai_year_count_heatmap.png'><img src='../../figures/r_history_20260928/bcai_year_count_heatmap.png' alt='완료 연도별 12카운트 BCAI 히트맵'></a><figcaption>작은 화면에서는 그림을 눌러 원본 크기로 볼 수 있습니다. 시즌별 구간은 아래 CSV에 보존했습니다.</figcaption></figure>",
  "<h2>표본과 결과의 출처</h2>",paste0("<p>",reproduction,"</p>"),
  "<div class='table-scroll'><table><thead><tr><th>시즌</th><th>유효 타석</th><th>경기</th><th>관측 날짜</th><th>기간 구분</th><th>근거</th></tr></thead><tbody>",html_sample_rows,"</tbody></table></div>",
  "<p><a href='summary.csv'>합친 수치·구간 CSV</a> · <a href='report_validation.json'>입력 해시·확인 기록</a> · <a href='../runs/bcai_r_check__mlb_2024_2025__20260928__r02/report.md'>2024·2025 재현·연도 차이 해설</a></p>",
  "<h2>카운트별 점추정 표</h2><div class='table-scroll'><table><thead><tr><th>카운트</th>",paste0("<th>",completed,"</th>",collapse=""),"</tr></thead><tbody>",html_matrix_rows,"</tbody></table></div>",
  "<h2>모바일 블로그용 그림</h2><p>연도 수가 늘어도 세 칸씩 읽도록 볼 수에 따라 나눴습니다. 네 그림은 같은 색상 범위를 씁니다.</p><div class='grid'>",
  vapply(0:3,function(b) paste0("<figure><a href='../../figures/r_history_20260928/bcai_",b,"balls_blog.png'><img src='../../figures/r_history_20260928/bcai_",b,"balls_blog.png' alt='",b,"볼에서 시즌별 BCAI'></a></figure>"),character(1)),"</div>",
  "<h2>해석할 때 남겨둘 선</h2><ul>",paste0("<li>",esc(interpretation),"</li>"),"</ul>",
  "<h2>파일 사용과 갱신 방법</h2><p>report.html은 그림과 표를 함께 보는 화면, report.md는 편집 가능한 보고서입니다. summary.csv에는 점추정·구간·분모와 원 실행 경로, report_validation.json에는 입력 해시와 확인 범위가 있습니다. 블로그에는 전체 히트맵이나 모바일용 0·1·2·3볼 PNG를 사용하고 단위·출처·해석 주의를 함께 남깁니다.</p><p>새로 완료된 실행이 생기면 저장소 루트에서 다시 실행합니다. 이 허브와 그림만 갱신하며 통계 재계산·다운로드·기존 실행 변경은 하지 않습니다.</p><pre><code>./tools/run_r.ps1 -Script tools/render_bcai_history.R</code></pre>",
  "<p class='muted'>연도별 최신 COMPLETE 과거 실행과 고정된 2024·2025 r02를 선택합니다. 원 CSV·표본·검증 JSON의 해시, 12카운트와 0-0 기준을 확인합니다. 실패 실행·기존 원고·외부 게시물은 변경하지 않습니다. <a href='report.md'>보고서 Markdown</a></p></main></body></html>")
writeLines(enc2utf8(html),file.path(out,"report.html"),useBytes=TRUE)
all_text <- paste(c(md,html),collapse="\n")
md_links <- regmatches(paste(md,collapse="\n"),gregexpr("\\]\\([^)]+\\)",paste(md,collapse="\n")))[[1]]
md_links <- sub("^\\]\\(","",sub("\\)$","",md_links))
html_links <- regmatches(paste(html,collapse="\n"),gregexpr("(?:href|src)='[^']+'",paste(html,collapse="\n"),perl=TRUE))[[1]]
html_links <- sub("^(?:href|src)='","",sub("'$","",html_links),perl=TRUE)
links <- unique(c(md_links,html_links));links <- links[!grepl("^(https?://|#)",links)]
# The validation document is written below; every other local target must exist now.
missing <- links[links!="report_validation.json" & !file.exists(file.path(out,links))]
if(length(missing)) stop("Missing report links: ",paste(missing,collapse=", "))
if(!all(vapply(inputs,function(x) identical(x$sha256,sha(x$path)),logical(1)))) stop("A saved input changed during rendering")
outputs <- c(file.path(out,c("report.md","report.html","summary.csv")),file.path(fig,c("bcai_year_count_heatmap.png",paste0("bcai_",0:3,"balls_blog.png"))))
validation <- list(status="PASS",generated_at=generated,role="완료된 저장 결과만 모은 보고서; 통계 재계산 없음",model_id="BCAI-OBS-v1.0.0",
  completed_years=completed,pending_years=pending,completed_seasons=length(completed),pending_seasons=length(pending),summary_rows=nrow(summary),
  coverage_note_ko=gap_note,continuous_target_coverage=!length(pending),
  selected_runs=as.list(unique(selected$run_id)),inputs=inputs,inputs_unchanged=TRUE,ignored_runs=ignored,
  checks=list(complete_manifests_only=TRUE,saved_validation_pass=TRUE,source_output_hashes_match=TRUE,all_twelve_counts=TRUE,
    no_duplicate_year_count=TRUE,baseline_100=TRUE,baseline_PA_matches=TRUE,cohort_totals_match=TRUE,missing_local_links=as.list(missing),checked_local_links=length(links),
    cross_year_inference_computed=FALSE,bootstrap_draws_loaded=FALSE),code=metadata("tools/render_bcai_history.R"),outputs=lapply(outputs,metadata))
write_json(validation,file.path(out,"report_validation.json"),pretty=TRUE,auto_unbox=TRUE,na="null",digits=NA)
cat("PASS: completed years",paste(completed,collapse=","),"; pending",length(pending),"; rows",nrow(summary),"; links",length(links),"\n")
