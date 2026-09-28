source("models/bcap/r/prepare_raw.R")
output <- "columns/001-ball-count/analysis/r_bcap_history_20260928/legacy_headers_2015_2016_20260928.json"
if (file.exists(output)) stop("Audit already exists; preserve it")
records <- list()
for (year in c(2016L,2015L)) {
  provenance_path <- sprintf("columns/001-ball-count/data/processed/r_history_20260928/%d/pitches.provenance.json",year)
  provenance <- jsonlite::fromJSON(provenance_path)
  paths <- provenance$source_files$path
  stopifnot(length(paths)>0L,!anyDuplicated(paths),all(file.exists(paths)))
  for (path in paths) {
    fields <- names(data.table::fread(path,nrows=0L))
    missing <- setdiff(BCAP_RAW_FIELDS,fields)
    records[[length(records)+1L]] <- list(year=year,path=path,
      header_sha256=digest::digest(fields,algo="sha256"),
      required_fields=length(BCAP_RAW_FIELDS),available_fields=length(fields),
      missing_fields=unname(missing),pass=!length(missing))
  }
}
passed <- all(vapply(records,function(x)x$pass,logical(1)))
jsonlite::write_json(list(status=if(passed)"PASS" else "FAIL",
  checked_at=format(Sys.time(),"%Y-%m-%dT%H:%M:%S%z"),
  scope="저장된2015·2016 원본 CSV의 필수 열 존재만 사전 점검했다. 결측률·측정 동등성·모형 적합 통과를 뜻하지 않는다. 원자료 준비·통계 계산·다운로드는 하지 않았다.",
  preparation_code_sha256=digest::digest(file="models/bcap/r/prepare_raw.R",algo="sha256"),
  files_checked=length(records),records=records),output,pretty=TRUE,auto_unbox=TRUE)
if(!passed)stop("Required raw fields missing; see audit")
cat("PASS: required BCAP fields present in",length(records),"archived CSV headers.\n")
