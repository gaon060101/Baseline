cat(R.version.string, "\n")
cat("R home:", R.home(), "\n")
cat("Library paths:\n", paste(.libPaths(), collapse="\n"), "\n")
stopifnot(isTRUE(all.equal(mean(c(1, 2, 3)), 2)))
for (p in c("data.table", "ggplot2", "jsonlite", "digest")) {
  cat(p, if (requireNamespace(p, quietly=TRUE)) as.character(packageVersion(p)) else "NOT INSTALLED", "\n")
}
args <- commandArgs(trailingOnly=TRUE)
if (length(args)) {
  out <- args[1]
  if (dir.exists(out)) stop("Output directory exists; choose a new check directory")
  dir.create(out, recursive=TRUE)
  packages <- c("data.table", "ggplot2", "jsonlite", "digest")
  stopifnot(all(vapply(packages, requireNamespace, logical(1), quietly=TRUE)))
  example <- data.table::data.table(label=c("가", "나", "다"), value=c(1, 2, 3))
  data.table::fwrite(example, file.path(out, "synthetic_example.csv"), bom=TRUE)
  restored <- data.table::fread(file.path(out, "synthetic_example.csv"), encoding="UTF-8")
  stopifnot(identical(restored$label, example$label), sum(restored$value)==6)
  grDevices::windowsFonts(Malgun=grDevices::windowsFont("Malgun Gothic"))
  plot <- ggplot2::ggplot(example, ggplot2::aes(label, value)) +
    ggplot2::geom_col(fill="#2563EB", width=.5) +
    ggplot2::geom_text(ggplot2::aes(label=value), vjust=-.5, family="Malgun", size=6) +
    ggplot2::scale_y_continuous(limits=c(0, 4), breaks=0:4) +
    ggplot2::labs(title="R 연결 확인 · 모의 자료", subtitle="실제 야구 분석 결과가 아닙니다", x=NULL, y="테스트 값") +
    ggplot2::theme_minimal(base_size=18, base_family="Malgun") +
    ggplot2::theme(plot.margin=ggplot2::margin(20, 20, 20, 20))
  grDevices::png(file.path(out, "synthetic_example.png"), width=1200, height=800, res=140, type="windows")
  print(plot)
  grDevices::dev.off()
  versions <- setNames(lapply(packages, function(p) as.character(packageVersion(p))), packages)
  jsonlite::write_json(list(status="PASS", scope="Synthetic connection check only; no baseball data accessed",
    checked_at=format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"), R=R.version.string, R_home=R.home(),
    packages=versions, checks=c("arithmetic", "UTF-8 CSV roundtrip", "Korean PNG creation"),
    png_sha256=digest::digest(file=file.path(out, "synthetic_example.png"), algo="sha256")),
    file.path(out, "check.json"), pretty=TRUE, auto_unbox=TRUE)
  writeLines(capture.output(sessionInfo()), file.path(out, "sessionInfo.txt"))
  cat("Connection check PASS:", normalizePath(out, winslash="/"), "\n")
}
