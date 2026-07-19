"""
Application Shiny for Python - Tableau de bord Bornes de recharge électrique
Accessibilité aux bornes de recharge à Montréal

Dépendances :
    pip install shiny shinyswatch geopandas folium branca pandas numpy matplotlib
"""

from __future__ import annotations

import html
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import folium

from shiny import App, reactive, render, ui

# ---------------------------------------------------------------------------
# Chemins des données
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR    = PROJECT_ROOT / "data" / "vectors"
BORNES_PATH = DATA_DIR / "bornes_recharge_montreal.geojson"
ARR_PATH    = DATA_DIR / "arrondissements_montreal.geojson"
ZONES_PATH  = DATA_DIR / "zones_sous_desservies.geojson"
STATS_PATH  = DATA_DIR / "chargeurs_statistiques_2025.csv"
DEMO_PATH   = DATA_DIR / "demographie_quebec.geojson"
PRIORITY_CSV_PATH = DATA_DIR / "priorites_arrondissements.csv"
PARCS_PATH      = DATA_DIR / "parcs_montreal.geojson"
EPICERIES_PATH  = DATA_DIR / "epiceries_montreal.geojson"
DEMO_ARR_PATH   = PROJECT_ROOT / "data" / "demo_arrondissements.csv"


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(num / (dx * dy + 1e-9), 3)


def _bornes_a_proximite(sites_gdf: gpd.GeoDataFrame, bornes_gdf: gpd.GeoDataFrame, rayon_m: float) -> pd.Series:
    """Nombre de bornes à moins de rayon_m mètres de chaque site (parc, épicerie...)."""
    sites_m = sites_gdf.to_crs(32188).copy()
    bornes_m = bornes_gdf.to_crs(32188)
    sites_m["geometry"] = sites_m.geometry.buffer(rayon_m)
    # how="inner" : un site sans aucune borne à proximité n'apparaît simplement pas dans
    # le résultat (reindex plus bas lui donne alors 0). Avec how="left", sjoin produit une
    # ligne "fantôme" (index_right = NaN) même pour les sites sans correspondance, et
    # groupby(...).size() la compte comme une borne — d'où un bug qui donnait 0 site sans
    # borne à proximité, peu importe le rayon.
    joined = gpd.sjoin(sites_m[["geometry"]], bornes_m[["geometry"]], how="inner", predicate="intersects")
    counts = joined.groupby(level=0).size()
    return counts.reindex(sites_gdf.index, fill_value=0)


def _parse_fr_number(series: pd.Series) -> pd.Series:
    """Nombres au format CSV Données Québec : guillemets littéraux autour de la valeur
    et virgule décimale française (ex. '"79,65"' -> 79.65). Sans ce nettoyage,
    pd.to_numeric() renvoie NaN pour la quasi-totalité des lignes (guillemets et
    virgule non reconnus), et .mean() calcule silencieusement une moyenne biaisée
    sur la poignée de valeurs qui passent par hasard (ex. entiers sans décimale)."""
    cleaned = (
        series.astype(str)
        .str.replace('"', "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    minimum = float(values.min())
    maximum = float(values.max())
    if minimum == maximum:
        return pd.Series([0.0] * len(values), index=values.index)
    return (values - minimum) / (maximum - minimum)


def _priority_label(score: float) -> str:
    if score >= 0.67:
        return "elevee"
    if score >= 0.34:
        return "moyenne"
    return "faible"


def _build_priority_layer(arr_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    priority = arr_gdf.copy()
    priority["nom"] = priority["NOM"]

    if "pct_couverture" not in priority.columns or "nb_bornes" not in priority.columns:
        zone_summary = gpd.read_file(ZONES_PATH)
        zone_summary = zone_summary.rename(columns={"arrondissement": "nom"})
        priority = priority.merge(
            zone_summary[["nom", "pct_couverture", "nb_bornes"]].drop_duplicates(subset=["nom"]),
            on="nom",
            how="left",
            suffixes=("", "_zones"),
        )

    priority["pct_couverture"] = pd.to_numeric(priority.get("pct_couverture", 0.0), errors="coerce").fillna(0.0)
    priority["nb_bornes"] = pd.to_numeric(priority.get("nb_bornes", 0.0), errors="coerce").fillna(0.0)

    if PRIORITY_CSV_PATH.exists():
        priority_df = pd.read_csv(PRIORITY_CSV_PATH)
        priority = priority.merge(priority_df, on="nom", how="left", suffixes=("", "_csv"))
        if "score_priorite" in priority.columns:
            priority["score_priorite"] = pd.to_numeric(priority["score_priorite"], errors="coerce").fillna(0.0)
        if "densite_pop_km2" not in priority.columns:
            priority["densite_pop_km2"] = pd.NA
    else:
        priority["deficit_couverture"] = 100.0 - pd.to_numeric(priority["pct_couverture"], errors="coerce").fillna(0.0)
        priority["densite_pop_km2"] = 0.0

        if DEMO_PATH.exists():
            demo = gpd.read_file(DEMO_PATH)
            dens_col = next((col for col in ["densite_hab_km2", "Habkm2", "densite", "density"] if col in demo.columns), None)
            if dens_col is not None and not demo.empty:
                arr_4326 = priority[["nom", "geometry"]].to_crs(epsg=4326)
                demo_4326 = demo[[dens_col, "geometry"]].to_crs(epsg=4326)
                joined = gpd.overlay(demo_4326, arr_4326, how="intersection")
                if not joined.empty:
                    joined_m = joined.to_crs(epsg=32188)
                    joined_m["area_m2"] = joined_m.geometry.area
                    joined_m["dens_weighted"] = pd.to_numeric(joined_m[dens_col], errors="coerce").fillna(0.0) * joined_m["area_m2"]
                    density = (
                        joined_m.groupby("nom", as_index=False)
                        .agg(total_area_m2=("area_m2", "sum"), dens_weighted=("dens_weighted", "sum"))
                    )
                    density["densite_pop_km2"] = density["dens_weighted"] / density["total_area_m2"]
                    priority = priority.merge(density[["nom", "densite_pop_km2"]], on="nom", how="left", suffixes=("", "_calc"))
                    priority["densite_pop_km2"] = pd.to_numeric(priority["densite_pop_km2_calc"], errors="coerce").fillna(priority["densite_pop_km2"])
                    priority = priority.drop(columns=["densite_pop_km2_calc"], errors="ignore")

        priority["n_deficit"] = _minmax(priority["deficit_couverture"])
        priority["n_population"] = _minmax(priority["densite_pop_km2"])
        priority["score_priorite"] = 0.6 * priority["n_deficit"] + 0.4 * priority["n_population"]
        priority["priorite"] = priority["score_priorite"].apply(_priority_label)

    priority["score_priorite"] = pd.to_numeric(priority.get("score_priorite", 0.0), errors="coerce").fillna(0.0)
    priority["score_priorite_pct"] = (priority["score_priorite"] * 100.0).round(1)
    priority["densite_pop_km2"] = pd.to_numeric(priority.get("densite_pop_km2", 0.0), errors="coerce").fillna(0.0).round(1)
    priority["deficit_couverture"] = pd.to_numeric(priority.get("deficit_couverture", 100.0 - priority["pct_couverture"]), errors="coerce").fillna(0.0).round(1)
    if "priorite" not in priority.columns:
        priority["priorite"] = priority["score_priorite"].apply(_priority_label)
    return priority

# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------
try:
    BORNES = gpd.read_file(BORNES_PATH)   # déjà WGS84
    ARR    = gpd.read_file(ARR_PATH)
    # DATEMODIF est lu comme un Timestamp par geopandas ; Folium ne sait pas le
    # sérialiser en JSON pour les tooltips (ARR.__geo_interface__ plus bas plante
    # sinon avec "Object of type Timestamp is not JSON serializable").
    if "DATEMODIF" in ARR.columns:
        ARR["DATEMODIF"] = ARR["DATEMODIF"].astype(str)
    ZONES  = gpd.read_file(ZONES_PATH)
    STATS  = pd.read_csv(STATS_PATH)
    PRIORITES = _build_priority_layer(ARR)

    # Nettoyage colonnes vides du CSV
    STATS = STATS.loc[:, ~STATS.columns.str.startswith("Column")]
    STATS.columns = STATS.columns.str.strip()

    # ── Questions gestionnaires : parcs, épiceries, profil socio-démographique ──
    # (le prof a explicitement demandé ces analyses en commentaires : pourquoi
    # certaines zones ont plus de bornes, lien avec le profil de la population,
    # les parcs, les épiceries — sans ça la localisation seule n'est pas utile.)
    PARCS = gpd.read_file(PARCS_PATH)
    PARCS["nb_bornes_500m"] = _bornes_a_proximite(PARCS, BORNES, 500)

    EPICERIES = gpd.read_file(EPICERIES_PATH)
    EPICERIES["nb_bornes_300m"] = _bornes_a_proximite(EPICERIES, BORNES, 300)
    EPICERIES["has_borne_300m"] = EPICERIES["nb_bornes_300m"] > 0

    # Jointure démographique par arrondissement (revenu, motorisation, faible
    # revenu) — le tiret cadratin (–) du CSV diffère du trait d'union simple (-)
    # utilisé dans le GeoJSON des arrondissements, sinon la jointure échoue
    # silencieusement sur les arrondissements à nom composé.
    DEMO_ARR = pd.read_csv(DEMO_ARR_PATH)
    DEMO_ARR["arrondissement"] = DEMO_ARR["arrondissement"].str.replace("–", "-", regex=False)
    DEMO_ARR = DEMO_ARR.rename(columns={"arrondissement": "nom"})

    _parcs_par_arr = gpd.sjoin(PARCS[["geometry"]], ARR[["NOM", "geometry"]], how="left", predicate="within")
    _nb_parcs = _parcs_par_arr.groupby("NOM").size().rename("nb_parcs")

    _epic_par_arr = gpd.sjoin(EPICERIES[["geometry"]], ARR[["NOM", "geometry"]], how="left", predicate="within")
    _nb_epiceries = _epic_par_arr.groupby("NOM").size().rename("nb_epiceries")

    CORR_DF = PRIORITES[["nom", "pct_couverture", "nb_bornes"]].merge(
        DEMO_ARR, on="nom", how="inner"
    ).merge(_nb_parcs, left_on="nom", right_index=True, how="left").merge(
        _nb_epiceries, left_on="nom", right_index=True, how="left"
    )
    CORR_DF["nb_parcs"] = CORR_DF["nb_parcs"].fillna(0)
    CORR_DF["nb_epiceries"] = CORR_DF["nb_epiceries"].fillna(0)

    # Listes de choix
    niveaux         = ["Tous"] + sorted(BORNES["NIVEAU_RECHARGE"].dropna().unique().tolist())
    modes           = ["Tous"] + sorted(BORNES["MODE_TARIFICATION"].dropna().unique().tolist())
    types_empl      = ["Tous"] + sorted(BORNES["TYPE_EMPLACEMENT"].dropna().unique().tolist())
    arrondissements = ["Tous"] + sorted(ARR["NOM"].dropna().unique().tolist())

    DATA_OK     = True
    _load_error = ""
except Exception as _e:
    DATA_OK     = False
    _load_error = str(_e)
    niveaux = modes = types_empl = arrondissements = ["Tous"]

# Couleurs fixes par niveau
COULEUR_NIVEAU = {"Niveau 2": "#2196F3", "BRCC": "#FF5722"}
COULEUR_PRIORITE = {
    "elevee": "#b42318",
    "moyenne": "#e67e22",
    "faible": "#2f7d32",
}

# ---------------------------------------------------------------------------
# Interface utilisateur
# ---------------------------------------------------------------------------
app_ui = ui.page_fluid(
    ui.panel_title("⚡ Tableau de bord — Bornes de recharge électrique · Montréal"),

    ui.layout_sidebar(
        # ── Sidebar ─────────────────────────────────────────────────────────
        ui.sidebar(
            ui.h5("Filtres"),
            ui.input_select("niveau",    "Niveau de recharge",   choices=niveaux),
            ui.input_select("mode",      "Mode de tarification",  choices=modes),
            ui.input_select("type_empl", "Type d'emplacement",   choices=types_empl),
            ui.input_select("arrond",    "Arrondissement",        choices=arrondissements),
            ui.hr(),
            ui.input_switch("show_priorites", "Zones prioritaires (population + couverture)", value=True),
            ui.input_slider("priority_threshold", "Seuil de priorite (%)", min=0, max=100, value=50, step=1),
            ui.input_switch("show_zones", "Zones sous-desservies", value=True),
            ui.input_switch("show_arr",   "Arrondissements",        value=True),
        ),

        # ── Corps ───────────────────────────────────────────────────────────
        ui.div(

            # Description
            ui.card(
                ui.card_header("Description"),
                ui.p(
                    "Cette application présente une analyse spatiale de l'accessibilité "
                    "aux bornes de recharge électriques publiques sur l'île de Montréal."
                ),
                ui.p(
                    "Elle permet d'explorer la distribution des bornes par arrondissement, "
                    "niveau de charge, mode de tarification et type d'emplacement, "
                    "ainsi que les zones géographiques sous-desservies."
                ),
                ui.p(
                    "Les données proviennent de la Ville de Montréal "
                    "(Données Québec, CC-BY 4.0)."
                ),
            ),

            # ── Value boxes ──────────────────────────────────────────────────
            ui.layout_columns(
                ui.value_box(
                    "Bornes totales",
                    ui.output_text("vbox_total"),
                    showcase=ui.tags.span("⚡"),
                    theme="success",
                ),
                ui.value_box(
                    "Niveau 2",
                    ui.output_text("vbox_niv2"),
                    showcase=ui.tags.span("🔵"),
                    theme="primary",
                ),
                ui.value_box(
                    "BRCC (rapide)",
                    ui.output_text("vbox_brcc"),
                    showcase=ui.tags.span("🔴"),
                    theme="danger",
                ),
                ui.value_box(
                    "Arrondissements couverts",
                    ui.output_text("vbox_arr"),
                    showcase=ui.tags.span("🏙️"),
                    theme="warning",
                ),
                col_widths=[3, 3, 3, 3],
            ),

            # ── Carte + Niveau ───────────────────────────────────────────────
            ui.layout_columns(
                ui.card(
                    ui.card_header("Carte interactive des bornes et priorites"),
                    ui.output_ui("map"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Bornes par niveau de recharge"),
                    ui.output_plot("plot_niveau"),
                ),
                col_widths=[8, 4],
            ),

            # ── Arrondissement + Tarification ────────────────────────────────
            ui.layout_columns(
                ui.card(
                    ui.card_header("Bornes par arrondissement (Top 15)"),
                    ui.output_plot("plot_arrond"),
                ),
                ui.card(
                    ui.card_header("Bornes par mode de tarification"),
                    ui.output_plot("plot_tarif"),
                ),
                col_widths=[7, 5],
            ),

            # ── Type emplacement + Zones sous-desservies ─────────────────────
            ui.layout_columns(
                ui.card(
                    ui.card_header("Bornes par type d'emplacement"),
                    ui.output_plot("plot_type"),
                ),
                ui.card(
                    ui.card_header("Zones sous-desservies — couverture (%)"),
                    ui.output_plot("plot_zones"),
                ),
                col_widths=[5, 7],
            ),

            ui.card(
                ui.card_header("Lecture automatique des priorites"),
                ui.output_text_verbatim("priority_summary"),
            ),

            # ── Questions des gestionnaires ───────────────────────────────────
            ui.card(
                ui.card_header("🏛️ Questions des gestionnaires"),
                ui.p(
                    "Pourquoi certaines zones ont-elles plus de bornes que d'autres ? "
                    "Est-ce lié au profil de la population, à la présence de parcs ou "
                    "d'épiceries ? Trois questions concrètes, avec les données réelles.",
                    style="font-size:0.85rem; color:#555;",
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("① Parcs — couverture en bornes"),
                        ui.input_numeric("g1_seuil", "Seuil minimal de bornes à 500 m", 20, min=1, max=100),
                        ui.output_ui("g1_resume"),
                        ui.output_data_frame("g1_table"),
                    ),
                    ui.card(
                        ui.card_header("② Épiceries — bornes à proximité (300 m)"),
                        ui.output_ui("g2_resume"),
                        ui.output_data_frame("g2_table"),
                    ),
                    col_widths=[6, 6],
                ),
                ui.card(
                    ui.card_header("③ Corrélation — le profil de la population explique-t-il la distribution des bornes ?"),
                    ui.output_plot("g3_correlation_plot"),
                    ui.output_ui("g3_interpretation"),
                ),
            ),

            # ── Statistiques d'utilisation 2025 ─────────────────────────────
            ui.card(
                ui.card_header("📊 Statistiques d'utilisation 2025"),
                ui.layout_columns(
                    ui.value_box(
                        "Total recharges",
                        ui.output_text("stat_recharges"),
                        showcase=ui.tags.span("🔋"),
                        theme="success",
                    ),
                    ui.value_box(
                        "kWh consommés (total)",
                        ui.output_text("stat_kwh"),
                        showcase=ui.tags.span("⚡"),
                        theme="primary",
                    ),
                    ui.value_box(
                        "Taux d'utilisation moyen",
                        ui.output_text("stat_taux"),
                        showcase=ui.tags.span("📈"),
                        theme="warning",
                    ),
                    ui.value_box(
                        "Moy. usagers/jour/borne",
                        ui.output_text("stat_users"),
                        showcase=ui.tags.span("👤"),
                        theme="danger",
                    ),
                    col_widths=[3, 3, 3, 3],
                ),
            ),

            # ── Tables synthèse ──────────────────────────────────────────────
            ui.layout_columns(
                ui.card(
                    ui.card_header("Synthèse par arrondissement"),
                    ui.output_data_frame("table_synthese"),
                ),
                ui.card(
                    ui.card_header("Top zones prioritaires"),
                    ui.output_data_frame("table_priorites"),
                ),
                ui.card(
                    ui.card_header("Zones sous-desservies"),
                    ui.output_data_frame("table_zones"),
                ),
                col_widths=[4, 4, 4],
            ),

            # ── Table complète ───────────────────────────────────────────────
            ui.card(
                ui.card_header("Données complètes des bornes"),
                ui.output_data_frame("table_bornes"),
                full_screen=True,
            ),

            # ── Signalement citoyen ──────────────────────────────────────────
            ui.card(
                ui.card_header("📸 Signaler un problème / une borne manquante"),
                ui.layout_columns(
                    ui.input_file(
                        "photo", "Photo (optionnel)",
                        accept=[".jpg", ".jpeg", ".png"],
                    ),
                    ui.input_text("email",     "Adresse courriel"),
                    ui.input_text("telephone", "Numéro de téléphone"),
                    col_widths=[4, 4, 4],
                ),
                ui.layout_columns(
                    ui.input_select(
                        "type_signal", "Type de signalement",
                        choices=[
                            "Borne hors service",
                            "Emplacement mal indiqué",
                            "Borne manquante",
                            "Autre",
                        ],
                    ),
                    ui.input_text("commentaire", "Commentaire"),
                    col_widths=[4, 8],
                ),
                ui.input_action_button("gps", "📍 Obtenir ma localisation"),
                ui.output_text("position"),
                ui.br(),
                ui.input_action_button(
                    "envoyer", "Envoyer le signalement", class_="btn btn-success"
                ),
                ui.output_text("confirm_envoi"),
            ),
        ),
    ),

    # Géolocalisation JavaScript
    ui.tags.script("""
        Shiny.addCustomMessageHandler('getLocation', function(x) {
            navigator.geolocation.getCurrentPosition(function(p) {
                Shiny.setInputValue('gps_lat', p.coords.latitude);
                Shiny.setInputValue('gps_lon', p.coords.longitude);
            }, function(err) {
                Shiny.setInputValue('gps_lat', null);
                Shiny.setInputValue('gps_lon', null);
            });
        });
    """),
)


# ---------------------------------------------------------------------------
# Serveur
# ---------------------------------------------------------------------------
def server(input, output, session):

    @reactive.calc
    def priorites_classees():
        if not DATA_OK:
            return gpd.GeoDataFrame()

        priority = PRIORITES.copy()
        if input.arrond() != "Tous":
            priority = priority[priority["nom"] == input.arrond()]

        priority = priority.sort_values("score_priorite", ascending=False).reset_index(drop=True)
        priority["rang_affiche"] = priority.index + 1
        return priority

    @reactive.calc
    def priorites_filtrees():
        priority = priorites_classees().copy()
        if len(priority) == 0:
            return priority

        minimum_score = float(input.priority_threshold()) / 100.0
        priority = priority[priority["score_priorite"] >= minimum_score]
        priority = priority.reset_index(drop=True)
        return priority

    # ── Données filtrées ─────────────────────────────────────────────────────
    @reactive.calc
    def bornes_filtre():
        if not DATA_OK:
            return gpd.GeoDataFrame()
        df = BORNES.copy()
        if input.niveau() != "Tous":
            df = df[df["NIVEAU_RECHARGE"] == input.niveau()]
        if input.mode() != "Tous":
            df = df[df["MODE_TARIFICATION"] == input.mode()]
        if input.type_empl() != "Tous":
            df = df[df["TYPE_EMPLACEMENT"] == input.type_empl()]
        if input.arrond() != "Tous":
            arr_geom = ARR[ARR["NOM"] == input.arrond()][["geometry"]]
            df = gpd.sjoin(df, arr_geom, how="inner", predicate="within")
            df = df.drop(
                columns=[c for c in df.columns if c.startswith("index_")],
                errors="ignore",
            )
        return df

    # ── Value boxes ──────────────────────────────────────────────────────────
    @output
    @render.text
    def vbox_total():
        return str(len(bornes_filtre()))

    @output
    @render.text
    def vbox_niv2():
        df = bornes_filtre()
        return str((df["NIVEAU_RECHARGE"] == "Niveau 2").sum()) if len(df) else "0"

    @output
    @render.text
    def vbox_brcc():
        df = bornes_filtre()
        return str((df["NIVEAU_RECHARGE"] == "BRCC").sum()) if len(df) else "0"

    @output
    @render.text
    def vbox_arr():
        df = bornes_filtre()
        if len(df) == 0:
            return "0"
        joined = gpd.sjoin(df, ARR[["NOM", "geometry"]], how="left", predicate="within")
        return str(joined["NOM"].nunique())

    # ── Carte Folium ─────────────────────────────────────────────────────────
    @output
    @render.ui
    def map():
        if not DATA_OK:
            return ui.p(f"Erreur de chargement : {_load_error}")

        df = bornes_filtre()
        priority_df = priorites_filtrees()
        m  = folium.Map(location=[45.53, -73.62], zoom_start=11,
                        tiles="CartoDB positron")

        def priority_style(feature):
            score = float(feature["properties"].get("score_priorite", 0.0) or 0.0)
            if score >= 0.67:
                fill = COULEUR_PRIORITE["elevee"]
            elif score >= 0.34:
                fill = COULEUR_PRIORITE["moyenne"]
            else:
                fill = COULEUR_PRIORITE["faible"]
            return {
                "color": fill,
                "weight": 2.5,
                "fillColor": fill,
                "fillOpacity": 0.42,
            }

        if input.show_priorites() and len(priority_df) > 0:
            folium.GeoJson(
                priority_df[["nom", "rang_affiche", "score_priorite", "score_priorite_pct", "pct_couverture", "deficit_couverture", "densite_pop_km2", "priorite", "geometry"]].__geo_interface__,
                name="Priorites nouvelles bornes",
                style_function=priority_style,
                tooltip=folium.GeoJsonTooltip(
                    fields=["rang_affiche", "nom", "priorite", "score_priorite_pct", "pct_couverture", "deficit_couverture", "densite_pop_km2"],
                    aliases=[
                        "Rang :",
                        "Arrondissement :",
                        "Priorite :",
                        "Score priorite (%) :",
                        "Couverture actuelle (%) :",
                        "Deficit de couverture (%) :",
                        "Densite population (hab/km2) :",
                    ],
                ),
            ).add_to(m)

            for _, row in priority_df.head(10).iterrows():
                point = row.geometry.representative_point()
                color = COULEUR_PRIORITE.get(row["priorite"], COULEUR_PRIORITE["faible"])
                folium.Marker(
                    location=[point.y, point.x],
                    icon=folium.DivIcon(
                        html=(
                            "<div style='"
                            f"background:{color};color:white;border:2px solid white;"
                            "border-radius:999px;width:26px;height:26px;line-height:22px;"
                            "text-align:center;font-size:12px;font-weight:700;box-shadow:0 2px 8px rgba(0,0,0,0.35);'>"
                            f"{int(row['rang_affiche'])}</div>"
                        )
                    ),
                    tooltip=(
                        f"#{int(row['rang_affiche'])} {row['nom']} | "
                        f"priorite {row['priorite']} | score {row['score_priorite_pct']}%"
                    ),
                ).add_to(m)

        # Arrondissements
        if input.show_arr():
            folium.GeoJson(
                ARR.__geo_interface__,
                name="Arrondissements",
                style_function=lambda _: {
                    "color": "#555", "weight": 1.5, "fillOpacity": 0.05,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["NOM"], aliases=["Arrondissement :"]
                ),
            ).add_to(m)

        # Zones sous-desservies
        if input.show_zones():
            folium.GeoJson(
                ZONES.__geo_interface__,
                name="Zones sous-desservies",
                style_function=lambda _: {
                    "color": "#FF9800",
                    "weight": 1,
                    "fillColor": "#FF9800",
                    "fillOpacity": 0.25,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["arrondissement", "nb_bornes", "pct_couverture"],
                    aliases=["Arrondissement :", "Nb bornes :", "Couverture (%) :"],
                ),
            ).add_to(m)

        # Points bornes
        for _, row in df.iterrows():
            if row.geometry is None:
                continue
            lon   = row.geometry.x
            lat   = row.geometry.y
            color = COULEUR_NIVEAU.get(row.get("NIVEAU_RECHARGE", ""), "#888888")
            popup = (
                f"<b>{row.get('NOM_BORNE_RECHARGE', '')}</b><br>"
                f"<b>Adresse :</b> {row.get('ADRESSE', '')}<br>"
                f"<b>Niveau :</b> {row.get('NIVEAU_RECHARGE', '')}<br>"
                f"<b>Tarification :</b> {row.get('MODE_TARIFICATION', '')}<br>"
                f"<b>Emplacement :</b> {row.get('TYPE_EMPLACEMENT', '')}"
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(popup, max_width=280),
            ).add_to(m)

        # Légende
        leg = (
            "<div style='position:fixed;bottom:30px;right:30px;background:white;"
            "padding:10px;border:1px solid #ccc;border-radius:6px;"
            "z-index:1000;font-size:12px'>"
            "<b>Niveau de recharge</b><br>"
        )
        for niv, col in COULEUR_NIVEAU.items():
            leg += (
                f"<span style='background:{col};width:12px;height:12px;"
                f"display:inline-block;margin-right:6px;border-radius:50%'>"
                f"</span>{niv}<br>"
            )
        leg += (
            "<span style='background:#FF9800;width:12px;height:12px;"
            "display:inline-block;margin-right:6px;opacity:0.5'></span>"
            "Zone sous-desservie"
        )
        leg += "<br><b>Priorite nouvelles bornes</b><br>"
        leg += "<span style='background:#b42318;width:12px;height:12px;display:inline-block;margin-right:6px;opacity:0.85'></span>Elevee<br>"
        leg += "<span style='background:#e67e22;width:12px;height:12px;display:inline-block;margin-right:6px;opacity:0.85'></span>Moyenne<br>"
        leg += "<span style='background:#2f7d32;width:12px;height:12px;display:inline-block;margin-right:6px;opacity:0.85'></span>Faible<br>"
        leg += "<span style='background:#111;width:12px;height:12px;display:inline-block;margin-right:6px;border-radius:50%'></span>Rang 1-10"
        leg += "</div>"
        m.get_root().html.add_child(folium.Element(leg))

        html_str = html.escape(m.get_root().render(), quote=True)
        return ui.HTML(
            f'<iframe srcdoc="{html_str}" '
            f'style="width:100%;height:600px;border:none;"></iframe>'
        )

    # ── Graphique : niveau de recharge ────────────────────────────────────────
    @output
    @render.plot
    def plot_niveau():
        df = bornes_filtre()
        if len(df) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center")
            return fig
        counts = df["NIVEAU_RECHARGE"].value_counts()
        colors = [COULEUR_NIVEAU.get(n, "#888") for n in counts.index]
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.bar(counts.index, counts.values, color=colors)
        ax.set_ylabel("Nombre de bornes")
        ax.set_title("Par niveau")
        plt.tight_layout()
        return fig

    # ── Graphique : arrondissement ────────────────────────────────────────────
    @output
    @render.plot
    def plot_arrond():
        df = bornes_filtre()
        if len(df) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center")
            return fig
        joined = gpd.sjoin(df, ARR[["NOM", "geometry"]], how="left", predicate="within")
        counts = joined["NOM"].value_counts().head(15).sort_values()
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.barh(counts.index, counts.values, color="steelblue")
        ax.set_xlabel("Nombre de bornes")
        ax.set_title("Top 15 arrondissements")
        plt.tight_layout()
        return fig

    # ── Graphique : tarification ──────────────────────────────────────────────
    @output
    @render.plot
    def plot_tarif():
        df = bornes_filtre()
        if len(df) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center")
            return fig
        counts = df["MODE_TARIFICATION"].value_counts().sort_values()
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.barh(counts.index, counts.values, color="#4CAF50")
        ax.set_xlabel("Nombre de bornes")
        ax.set_title("Par mode de tarification")
        plt.tight_layout()
        return fig

    # ── Graphique : type d'emplacement ────────────────────────────────────────
    @output
    @render.plot
    def plot_type():
        df = bornes_filtre()
        if len(df) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center")
            return fig
        counts = df["TYPE_EMPLACEMENT"].fillna("Non précisé").value_counts()
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            counts.values,
            labels=counts.index,
            autopct="%1.1f%%",
            colors=["#2196F3", "#FF5722", "#9E9E9E"],
        )
        ax.set_title("Type d'emplacement")
        plt.tight_layout()
        return fig

    # ── Graphique : zones sous-desservies ─────────────────────────────────────
    @output
    @render.plot
    def plot_zones():
        df = ZONES.copy()
        if len(df) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center")
            return fig
        df = df.sort_values("pct_couverture")
        colors = [
            "#FF5722" if p < 30 else "#FF9800" if p < 60 else "#4CAF50"
            for p in df["pct_couverture"]
        ]
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.barh(df["arrondissement"], df["pct_couverture"], color=colors)
        ax.axvline(50, color="grey", linestyle="--", linewidth=0.8, label="Seuil 50%")
        ax.set_xlabel("Couverture (%)")
        ax.set_title("Zones sous-desservies")
        ax.legend(fontsize=8)
        plt.tight_layout()
        return fig

    # ── Statistiques 2025 ─────────────────────────────────────────────────────
    @output
    @render.text
    def stat_recharges():
        try:
            total = int(STATS["NOMBRE DE RECHARGE"].sum())
            return f"{total:,}".replace(",", "\u202f")
        except Exception:
            return "N/D"

    @output
    @render.text
    def stat_kwh():
        try:
            total = _parse_fr_number(STATS["KWH total"]).sum()
            return f"{int(round(total)):,}\u202fkWh".replace(",", "\u202f")
        except Exception:
            return "N/D"

    @output
    @render.text
    def stat_taux():
        try:
            vals = _parse_fr_number(STATS["Taux d'utilisation"])
            return f"{vals.mean():.1f}\u202f%"
        except Exception:
            return "N/D"

    @output
    @render.text
    def stat_users():
        try:
            vals = _parse_fr_number(STATS["MOYENNE UTILISATEUR/ JOUR"])
            return f"{vals.mean():.2f}"
        except Exception:
            return "N/D"

    # ── Table : synthèse par arrondissement ───────────────────────────────────
    @output
    @render.data_frame
    def table_synthese():
        df = bornes_filtre()
        if len(df) == 0:
            return render.DataGrid(pd.DataFrame())
        joined = gpd.sjoin(df, ARR[["NOM", "geometry"]], how="left", predicate="within")
        summary = (
            joined.groupby("NOM")
            .agg(
                Nb_bornes=("NOM_BORNE_RECHARGE", "count"),
                Niveau2=("NIVEAU_RECHARGE", lambda x: (x == "Niveau 2").sum()),
                BRCC=("NIVEAU_RECHARGE", lambda x: (x == "BRCC").sum()),
            )
            .reset_index()
            .rename(columns={"NOM": "Arrondissement"})
            .sort_values("Nb_bornes", ascending=False)
        )
        return render.DataGrid(summary, filters=True)

    @output
    @render.data_frame
    def table_priorites():
        df = priorites_classees()
        if len(df) == 0:
            return render.DataGrid(pd.DataFrame())

        summary = (
            df[["rang_affiche", "nom", "priorite", "score_priorite_pct", "pct_couverture", "densite_pop_km2"]]
            .rename(
                columns={
                    "rang_affiche": "Rang",
                    "nom": "Arrondissement",
                    "priorite": "Priorite",
                    "score_priorite_pct": "Score priorite (%)",
                    "pct_couverture": "Couverture (%)",
                    "densite_pop_km2": "Densite pop. (hab/km2)",
                }
            )
            .sort_values("Score priorite (%)", ascending=False)
            .head(10)
        )
        return render.DataGrid(summary, filters=True)

    @output
    @render.text
    def priority_summary():
        df = priorites_classees()
        if len(df) == 0:
            return (
                "Aucune zone prioritaire disponible dans les donnees actuelles."
            )

        top = df.head(3)
        lines = [
            "Les secteurs a renforcer en premier combinent faible couverture et forte densite de population.",
            "",
        ]
        for _, row in top.iterrows():
            lines.append(
                f"#{int(row['rang_affiche'])} {row['nom']} : score {row['score_priorite_pct']}%, couverture {row['pct_couverture']}%, densite {row['densite_pop_km2']} hab/km2."
            )

        filtered_count = len(priorites_filtrees())
        if len(df) > 3:
            lines.append("")
            lines.append(f"{filtered_count} zones depassent actuellement le seuil de {input.priority_threshold()}% sur la carte.")

        return "\n".join(lines)

    # ── Question ① : parcs sous le seuil de bornes à 500 m ────────────────────
    @output
    @render.ui
    def g1_resume():
        seuil = input.g1_seuil()
        insuffisants = PARCS[PARCS["nb_bornes_500m"] < seuil]
        total = len(PARCS)
        count = len(insuffisants)
        pct_ok = round(100 * (total - count) / max(total, 1), 1)
        couleur = "success" if pct_ok >= 80 else "warning" if pct_ok >= 50 else "danger"
        return ui.div(
            ui.strong(f"{count}"),
            f" parcs sur {total} ont moins de {seuil} bornes à 500 m.",
            class_=f"alert alert-{couleur}",
            style="font-size:0.85rem; padding:8px 12px;",
        )

    @output
    @render.data_frame
    def g1_table():
        seuil = input.g1_seuil()
        df = (
            PARCS[PARCS["nb_bornes_500m"] < seuil][["nom", "superficie_ha", "nb_bornes_500m"]]
            .sort_values("nb_bornes_500m")
            .head(25)
            .rename(columns={"nom": "Parc", "superficie_ha": "Superficie (ha)", "nb_bornes_500m": f"Bornes à 500 m (< {seuil})"})
        )
        return render.DataGrid(df.reset_index(drop=True), filters=True)

    # ── Question ② : épiceries sans borne à 300 m ─────────────────────────────
    @output
    @render.ui
    def g2_resume():
        sans = EPICERIES[~EPICERIES["has_borne_300m"]]
        total = len(EPICERIES)
        count = len(sans)
        pct_ok = round(100 * (total - count) / max(total, 1), 1)
        couleur = "success" if pct_ok >= 80 else "warning" if pct_ok >= 50 else "danger"
        return ui.div(
            ui.strong(f"{count}"),
            f" épiceries sur {total} n'ont aucune borne à 300 m.",
            class_=f"alert alert-{couleur}",
            style="font-size:0.85rem; padding:8px 12px;",
        )

    @output
    @render.data_frame
    def g2_table():
        df = (
            EPICERIES[~EPICERIES["has_borne_300m"]][["nom", "type", "adresse"]]
            .head(25)
            .rename(columns={"nom": "Épicerie", "type": "Type", "adresse": "Adresse"})
        )
        return render.DataGrid(df.reset_index(drop=True), filters=True)

    # ── Question ③ : corrélation couverture ↔ profil socio-démographique ─────
    @reactive.calc
    def _correlations():
        facteurs = {
            "densite_pop_km2": "Densité de population",
            "revenu_median_menage": "Revenu médian des ménages",
            "tx_voiture_pct": "Taux de motorisation",
            "tx_faible_revenu_pct": "Taux de faible revenu",
            "nb_parcs": "Zones de loisirs (parcs)",
            "nb_epiceries": "Commerces alimentaires (épiceries)",
        }
        resultats = []
        for col, label in facteurs.items():
            sub = CORR_DF.dropna(subset=[col, "pct_couverture"])
            r = pearson(sub[col].tolist(), sub["pct_couverture"].tolist())
            resultats.append({"variable": col, "label": label, "r": r})
        return sorted(resultats, key=lambda x: -abs(x["r"]))

    @output
    @render.plot
    def g3_correlation_plot():
        cors = _correlations()
        labels = [c["label"] for c in cors][::-1]
        values = [c["r"] for c in cors][::-1]
        colors = ["#2e7d32" if v > 0 else "#c62828" for v in values]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh(labels, values, color=colors)
        ax.axvline(0, color="grey", linewidth=0.8)
        ax.set_xlim(-1, 1)
        ax.set_xlabel("Corrélation de Pearson (r) avec la couverture en bornes")
        plt.tight_layout()
        return fig

    @output
    @render.ui
    def g3_interpretation():
        cors = _correlations()
        if not cors:
            return ui.p("Données insuffisantes.")
        top = cors[0]
        absR = abs(top["r"])
        if absR >= 0.4:
            direction = "positive" if top["r"] > 0 else "négative"
            texte = (
                f"Facteur dominant : « {top['label']} » (r = {top['r']}) — corrélation "
                f"{direction} forte avec la couverture en bornes."
            )
            classe = "alert alert-info"
        elif absR >= 0.2:
            texte = f"Facteur le plus lié : « {top['label']} » (r = {top['r']}) — corrélation modérée."
            classe = "alert alert-warning"
        else:
            texte = "Aucun facteur isolé n'explique clairement la distribution des bornes."
            classe = "alert alert-secondary"
        return ui.div(texte, class_=classe, style="font-size:0.85rem; padding:8px 12px;")

    # ── Table : zones sous-desservies ─────────────────────────────────────────
    @output
    @render.data_frame
    def table_zones():
        df = ZONES.drop(columns="geometry", errors="ignore").rename(
            columns={
                "arrondissement": "Arrondissement",
                "nb_bornes":      "Nb bornes",
                "pct_couverture": "Couverture (%)",
            }
        )
        return render.DataGrid(df.sort_values("Couverture (%)"), filters=True)

    # ── Table : données complètes ─────────────────────────────────────────────
    @output
    @render.data_frame
    def table_bornes():
        df = bornes_filtre().drop(columns="geometry", errors="ignore")
        return render.DataGrid(df, filters=True, height="400px")

    # ── GPS ──────────────────────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.gps)
    async def _trigger_gps():
        await session.send_custom_message("getLocation", {})

    @output
    @render.text
    def position():
        try:
            lat = input.gps_lat()
            lon = input.gps_lon()
            if lat and lon:
                return f"Latitude : {lat}   Longitude : {lon}"
        except Exception:
            pass
        return ""

    # ── Envoi signalement ─────────────────────────────────────────────────────
    @output
    @render.text
    @reactive.event(input.envoyer)
    def confirm_envoi():
        email  = input.email()
        type_s = input.type_signal()
        if not email:
            return "⚠️ Veuillez renseigner votre adresse courriel."
        return f"✅ Signalement envoyé ! Type : {type_s} | Courriel : {email}"


# ---------------------------------------------------------------------------
# Lancement
# ---------------------------------------------------------------------------
app = App(app_ui, server)
