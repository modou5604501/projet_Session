#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(sf)
  library(dplyr)
  library(jsonlite)
})

# Configuration cache/reseau pour les appels Cancensus
Sys.setenv(CM_CACHE_PATH = "C:/cancensus_cache")
dir.create("C:/cancensus_cache", recursive = TRUE, showWarnings = FALSE)
options(cancensus.cache_path = "C:/cancensus_cache")
options(cancensus.use_cache = FALSE)
options(timeout = 600)

# Dossiers de sortie analytiques
dir.create("Resultats", showWarnings = FALSE)
dir.create("Resultats/RData", recursive = TRUE, showWarnings = FALSE)

out_path <- "data/vectors/demographie_quebec.geojson"
dataset <- "CA21"
rdata_default <- "c:/Users/Utilisateur/Desktop/hiver2026/Eté 2026/Démographie spatiale/labo3/Data/DataRMR_MTL.Rdata"

dq_url <- Sys.getenv("DQ_DEMOGRAPHIE_URL")
dq_dataset_id <- Sys.getenv("DQ_DEMOGRAPHIE_DATASET_ID")
api_key <- Sys.getenv("CANCENSUS_API_KEY")
rdata_path <- Sys.getenv("DEMOGRAPHIE_RDATA_PATH", unset = rdata_default)

pick_population_column <- function(df) {
  candidates <- c("population_totale", "population", "pop_total", "pop")
  for (nm in candidates) {
    if (nm %in% names(df)) return(nm)
  }
  NULL
}

download_from_donnees_quebec <- function() {
  if (dq_url == "" && dq_dataset_id == "") {
    return(FALSE)
  }

  resource_url <- dq_url
  if (resource_url == "" && dq_dataset_id != "") {
    api <- sprintf(
      "https://www.donneesquebec.ca/recherche/api/3/action/package_show?id=%s",
      dq_dataset_id
    )
    payload <- fromJSON(api)
    if (!isTRUE(payload$success)) {
      stop("Echec API CKAN pour Donnees Quebec")
    }

    resources <- payload$result$resources
    if (is.null(resources) || nrow(resources) == 0) {
      stop("Aucune ressource dans le dataset Donnees Quebec")
    }

    fmt <- toupper(ifelse(is.na(resources$format), "", resources$format))
    title <- tolower(ifelse(is.na(resources$name), "", resources$name))
    is_geo <- fmt %in% c("GEOJSON", "JSON", "SHP", "GPKG") |
      grepl("geojson|population|demograph", title)
    idx <- which(is_geo)
    if (length(idx) == 0) {
      idx <- 1
    }
    resource_url <- resources$url[idx[1]]
  }

  if (is.null(resource_url) || resource_url == "") {
    stop("URL de ressource Donnees Quebec introuvable")
  }

  tmp <- tempfile(fileext = ".geojson")
  download.file(resource_url, tmp, mode = "wb", quiet = TRUE)
  demo <- st_read(tmp, quiet = TRUE)

  pop_col <- pick_population_column(demo)
  if (is.null(pop_col)) {
    stop("Impossible d'identifier une colonne de population dans Donnees Quebec")
  }

  keep_name <- if ("nom" %in% names(demo)) "nom" else if ("name" %in% names(demo)) "name" else names(demo)[1]
  demo <- demo %>%
    mutate(population_totale = as.numeric(.data[[pop_col]])) %>%
    select(any_of(c(keep_name, "population_totale")), geometry)

  st_write(demo, out_path, delete_dsn = TRUE, quiet = TRUE)
  message(sprintf("Fichier genere depuis Donnees Quebec: %s", out_path))
  TRUE
}

download_from_rdata <- function() {
  if (rdata_path == "" || !file.exists(rdata_path)) {
    return(FALSE)
  }

  e <- new.env()
  objs <- load(rdata_path, envir = e)
  if (!("RMR_CT" %in% objs)) {
    stop("Objet RMR_CT introuvable dans le fichier RData")
  }

  x <- e[["RMR_CT"]]
  if (!inherits(x, "sf")) {
    stop("RMR_CT doit etre un objet sf")
  }

  cols <- names(x)
  required <- c("Habkm2")
  missing <- setdiff(required, cols)
  if (length(missing) > 0) {
    stop(sprintf("Colonnes requises manquantes dans RMR_CT: %s", paste(missing, collapse = ", ")))
  }

  # Export strictement a partir des donnees existantes (aucune valeur inventee).
  out <- x %>%
    mutate(densite_hab_km2 = as.numeric(Habkm2)) %>%
    select(any_of(c("SRIDU", "densite_hab_km2", "age20_34", "age35_49", "age50_64", "age65plus")), geometry)

  st_write(out, out_path, delete_dsn = TRUE, quiet = TRUE)
  message(sprintf("Fichier genere depuis RData local: %s", out_path))
  TRUE
}

download_from_cancensus <- function() {
  if (api_key == "") {
    stop("CANCENSUS_API_KEY manquant pour le fallback Cancensus")
  }

  suppressPackageStartupMessages(library(cancensus))
  set_cancensus_api_key(api_key, install = FALSE, overwrite = TRUE)

  message("Recherche du vecteur de population totale (Cancensus)...")
  vec <- search_census_vectors("Population, 2021", dataset = dataset)
  if (nrow(vec) == 0) {
    vec <- search_census_vectors("Population", dataset = dataset)
  }
  if (nrow(vec) == 0) {
    stop("Impossible de trouver un vecteur population dans Cancensus")
  }

  population_vector <- vec$vector[1]
  message(sprintf("Vecteur utilise: %s", population_vector))

  demo <- get_census(
    dataset = dataset,
    regions = list(PR = "24"),
    level = "CSD",
    vectors = population_vector,
    geo_format = "sf"
  )

  if (!(population_vector %in% names(demo))) {
    stop("Colonne de population absente du resultat Cancensus")
  }

  demo <- demo %>%
    mutate(population_totale = as.numeric(.data[[population_vector]])) %>%
    select(CSDUID, CSDNAME, population_totale, geometry)

  st_write(demo, out_path, delete_dsn = TRUE, quiet = TRUE)
  message(sprintf("Fichier genere depuis Cancensus: %s", out_path))
  TRUE
}

ok <- FALSE
try({ ok <- download_from_rdata() }, silent = TRUE)

if (!ok) {
  try({ ok <- download_from_donnees_quebec() }, silent = TRUE)
}

if (!ok) {
  message("RData local et Donnees Quebec indisponibles. Fallback Cancensus...")
  download_from_cancensus()
}
