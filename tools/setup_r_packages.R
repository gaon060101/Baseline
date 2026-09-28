lib <- Sys.getenv("R_LIBS_USER")
if (!nzchar(lib)) stop("R_LIBS_USER is not configured")
dir.create(lib, recursive=TRUE, showWarnings=FALSE)
.libPaths(c(lib, .libPaths()))
packages <- c("data.table", "ggplot2", "jsonlite", "digest")
missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly=TRUE)]
if (length(missing)) install.packages(missing, repos="https://cloud.r-project.org", type="binary", lib=lib)
stopifnot(all(vapply(packages, requireNamespace, logical(1), quietly=TRUE)))
cat("All required packages are available\n")
