"""
GeoCharge Montréal — Application Python Shiny
GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke

Remplace Django+Docker+PostGIS par une app autonome :
  - geopandas : requêtes spatiales (sjoin, buffer, within)
  - folium    : carte Leaflet interactive
  - shiny     : interface réactive

Lancer : shiny run app.py --reload
"""

import os, math, warnings
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shiny import App, ui, render, reactive

warnings.filterwarnings("ignore", category=FutureWarning)

# ═══════════════════════════════════════════════════════════════════════════
# CHEMINS DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════
_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VEC  = os.path.join(_BASE, "data", "vectors")
DATA = os.path.join(_BASE, "data")


# ═══════════════════════════════════════════════════════════════════════════
# CHARGEMENT ET PRÉ-CALCUL (exécuté une fois au démarrage)
# ═══════════════════════════════════════════════════════════════════════════
print("⏳ Chargement des données GeoJSON…", flush=True)

bornes_gdf    = gpd.read_file(os.path.join(VEC, "bornes_recharge_montreal.geojson")).to_crs(4326)
arrond_gdf    = gpd.read_file(os.path.join(VEC, "arrondissements_montreal.geojson")).to_crs(4326)
parcs_gdf     = gpd.read_file(os.path.join(VEC, "parcs_montreal.geojson")).to_crs(4326)
epiceries_gdf = gpd.read_file(os.path.join(VEC, "epiceries_montreal.geojson")).to_crs(4326)
demo_df       = pd.read_csv(os.path.join(DATA, "demo_arrondissements.csv"))

# Normaliser la colonne nom dans arrond_gdf
for col in arrond_gdf.columns:
    if col.upper() == "NOM" and col != "nom":
        arrond_gdf = arrond_gdf.rename(columns={col: "nom"})
        break

print(f"  → {len(bornes_gdf)} bornes · {len(arrond_gdf)} arrondissements · "
      f"{len(parcs_gdf)} parcs · {len(epiceries_gdf)} épiceries", flush=True)

# ── Projeter en MTM-8 (EPSG:32188) pour les calculs de distance ────────────
bornes_p    = bornes_gdf.to_crs(32188)
arrond_p    = arrond_gdf.to_crs(32188)
parcs_p     = parcs_gdf.to_crs(32188)
epiceries_p = epiceries_gdf.to_crs(32188)

# ── Couverture 500 m par arrondissement ────────────────────────────────────
print("⏳ Calcul couverture 500 m…", flush=True)
buf_union = bornes_p.geometry.buffer(500).unary_union
arrond_p["pct_couverture"] = arrond_p.geometry.apply(
    lambda g: round(min(100.0, 100.0 * buf_union.intersection(g).area / g.area), 1)
)
arrond_gdf["pct_couverture"] = arrond_p["pct_couverture"].values

# ── Nombre de bornes par arrondissement ────────────────────────────────────
_b_in_a = gpd.sjoin(bornes_p[["geometry"]], arrond_p[["nom", "geometry"]],
                    how="left", predicate="within")
_nb = _b_in_a.groupby("nom").size().reset_index(name="nb_bornes")
arrond_gdf = arrond_gdf.merge(_nb, on="nom", how="left")
arrond_gdf["nb_bornes"] = arrond_gdf["nb_bornes"].fillna(0).astype(int)

# ── Fusion données socio-démographiques ────────────────────────────────────
demo_df = demo_df.rename(columns={"arrondissement": "nom"})
arrond_gdf = arrond_gdf.merge(
    demo_df[["nom", "pop_2021", "densite_pop_km2", "revenu_median_menage",
             "tx_voiture_pct", "tx_faible_revenu_pct"]],
    on="nom", how="left"
)

# ── Bornes à 500 m pour chaque parc ────────────────────────────────────────
print("⏳ Requête spatiale parcs ↔ bornes (500 m)…", flush=True)
_buf_bornes_500 = bornes_p.copy()
_buf_bornes_500["geometry"] = _buf_bornes_500.geometry.buffer(500)
_buf_bornes_500["_bid"] = range(len(_buf_bornes_500))
_pj = gpd.sjoin(parcs_p[["geometry"]], _buf_bornes_500[["geometry", "_bid"]],
                how="left", predicate="intersects")
parcs_gdf["nb_bornes_500m"] = (
    _pj.groupby(level=0)["_bid"].count().reindex(parcs_p.index, fill_value=0).values
)

# ── Épiceries sans borne à 300 m ───────────────────────────────────────────
print("⏳ Requête spatiale épiceries ↔ bornes (300 m)…", flush=True)
_buf_bornes_300_union = bornes_p.geometry.buffer(300).unary_union
epiceries_gdf["has_borne_300m"] = epiceries_p.geometry.within(_buf_bornes_300_union)

# ── Parcs et épiceries par arrondissement (pour G6) ───────────────────────
_pa = gpd.sjoin(parcs_p[["geometry"]], arrond_p[["nom", "geometry"]],
                how="left", predicate="within")
_nb_parcs = _pa.groupby("nom").size().reset_index(name="nb_parcs")

_ea = gpd.sjoin(epiceries_p[["geometry"]], arrond_p[["nom", "geometry"]],
                how="left", predicate="within")
_nb_epic = _ea.groupby("nom").size().reset_index(name="nb_epiceries")

g6_df = arrond_gdf[["nom", "nb_bornes", "pct_couverture",
                     "densite_pop_km2", "revenu_median_menage",
                     "tx_voiture_pct", "tx_faible_revenu_pct"]].copy()
g6_df = g6_df.merge(_nb_parcs, on="nom", how="left")
g6_df = g6_df.merge(_nb_epic,  on="nom", how="left")
g6_df["nb_parcs"]     = g6_df["nb_parcs"].fillna(0).astype(int)
g6_df["nb_epiceries"] = g6_df["nb_epiceries"].fillna(0).astype(int)

print("✅ Données prêtes.", flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════

def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx  = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy  = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(num / (dx * dy + 1e-9), 3)


def coul_couverture(pct):
    if pct >= 60: return "#00c96e"
    if pct >= 30: return "#ffd700"
    if pct >= 15: return "#ff8c00"
    return "#e8273e"


DEMO_LABELS = {
    "revenu_median_menage": "Revenu médian des ménages ($)",
    "tx_voiture_pct":       "Taux de motorisation (%)",
    "densite_pop_km2":      "Densité de population (hab/km²)",
    "tx_faible_revenu_pct": "Faible revenu (% ménages < 40 k$)",
}

DEMO_PALETTES = {
    "revenu_median_menage": "RdYlGn",
    "tx_voiture_pct":       "YlGnBu",
    "densite_pop_km2":      "Blues",
    "tx_faible_revenu_pct": "YlOrRd",
}

VAR_LABELS_G6 = {
    "nb_parcs":             "Zones de loisirs (parcs)",
    "nb_epiceries":         "Commerces alimentaires (épiceries)",
    "revenu_median_menage": "Revenu médian des ménages",
    "densite_pop_km2":      "Densité de population",
    "tx_voiture_pct":       "Taux de motorisation (proxy demande EV)",
    "tx_faible_revenu_pct": "Taux de faible revenu",
}

QUESTIONS_G6 = {
    "nb_parcs":             "est-ce lié à la proximité de zones de loisirs ?",
    "nb_epiceries":         "est-ce la présence de commerces ?",
    "revenu_median_menage": "est-ce lié au profil économique ?",
    "densite_pop_km2":      "est-ce lié à la densité de population ?",
    "tx_voiture_pct":       "est-ce lié à l'accès en voiture ?",
    "tx_faible_revenu_pct": "est-ce lié à la vulnérabilité socio-éco ?",
}


# ═══════════════════════════════════════════════════════════════════════════
# CONSTRUCTEUR DE CARTE FOLIUM
# ═══════════════════════════════════════════════════════════════════════════

def build_map(show_bornes=True, show_arrond=True, demo_var="couverture"):
    m = folium.Map(location=[45.53, -73.62], zoom_start=11, tiles=None,
                   prefer_canvas=True)

    # Fond de carte sombre
    folium.TileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© OpenStreetMap, © CARTO",
        name="Plan sombre",
        max_zoom=19,
    ).add_to(m)

    # ── Arrondissements ────────────────────────────────────────────────────
    if show_arrond:
        if demo_var in DEMO_LABELS:
            # Choroplèthe démographique
            _col = demo_var
            _valid = arrond_gdf[["nom", _col, "geometry"]].dropna(subset=[_col])
            folium.Choropleth(
                geo_data=_valid.to_json(),
                data=_valid,
                columns=["nom", _col],
                key_on="feature.properties.nom",
                fill_color=DEMO_PALETTES.get(_col, "YlOrRd"),
                fill_opacity=0.65,
                line_opacity=0.8,
                line_color="#1e3a5f",
                nan_fill_color="#222",
                legend_name=DEMO_LABELS[_col],
                name="Arrondissements (démographie)",
            ).add_to(m)
            # Tooltip overlay
            folium.GeoJson(
                _valid.to_json(),
                style_function=lambda x: {"fillOpacity": 0, "weight": 0},
                tooltip=folium.GeoJsonTooltip(
                    fields=["nom", _col],
                    aliases=["Arrondissement", DEMO_LABELS[_col]],
                    localize=True,
                ),
                name="_tooltip_demo",
            ).add_to(m)
        else:
            # Couverture en bornes
            def _style(feat):
                pct = feat["properties"].get("pct_couverture") or 0
                return {
                    "fillColor": coul_couverture(pct),
                    "color": "#1e3a5f",
                    "weight": 1.2,
                    "fillOpacity": 0.45,
                }
            folium.GeoJson(
                arrond_gdf[["nom", "nb_bornes", "pct_couverture", "geometry"]].to_json(),
                name="Arrondissements (couverture)",
                style_function=_style,
                tooltip=folium.GeoJsonTooltip(
                    fields=["nom", "nb_bornes", "pct_couverture"],
                    aliases=["Arrondissement", "Bornes", "Couverture (%)"],
                    localize=True,
                ),
            ).add_to(m)

    # ── Bornes de recharge ─────────────────────────────────────────────────
    if show_bornes:
        _pts = [[r.geometry.y, r.geometry.x] for _, r in bornes_gdf.iterrows()]
        plugins.FastMarkerCluster(
            _pts,
            name="Bornes de recharge",
            options={"maxClusterRadius": 40, "disableClusteringAtZoom": 15},
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE UTILISATEUR SHINY
# ═══════════════════════════════════════════════════════════════════════════

app_ui = ui.page_navbar(

    # ── TAB 1 : CARTE ──────────────────────────────────────────────────────
    ui.nav_panel(
        "🗺️ Carte interactive",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h6("Calques"),
                ui.input_checkbox("show_bornes", "Bornes de recharge", True),
                ui.input_checkbox("show_arrond", "Arrondissements",    True),
                ui.hr(),
                ui.h6("Coloration arrondissements"),
                ui.input_select(
                    "demo_var", None,
                    choices={
                        "couverture":             "📊 Couverture en bornes",
                        "revenu_median_menage":   "💰 Revenu médian",
                        "tx_voiture_pct":         "🚗 Motorisation (%)",
                        "densite_pop_km2":        "👥 Densité pop. (hab/km²)",
                        "tx_faible_revenu_pct":   "📉 Faible revenu (%)",
                    },
                    selected="couverture",
                ),
                ui.hr(),
                ui.p(
                    ui.strong(f"{len(bornes_gdf):,}"),
                    " bornes · ",
                    ui.strong(f"{len(arrond_gdf)}"),
                    " arrondissements",
                    style="font-size:0.8rem; color:#666;",
                ),
                ui.p(
                    "Source : Données de Montréal (CC-BY 4.0) · StatCan 2021",
                    style="font-size:0.7rem; color:#999;",
                ),
                width=260,
            ),
            ui.output_ui("map_output"),
        ),
    ),

    # ── TAB 2 : QUESTIONS GESTIONNAIRES ────────────────────────────────────
    ui.nav_panel(
        "🏛 Questions gestionnaires",
        ui.layout_column_wrap(

            # G1 — Parcs
            ui.card(
                ui.card_header("① Parcs — couverture en bornes"),
                ui.p(
                    "Un gestionnaire aimerait savoir si tous les parcs de Montréal "
                    "disposent d'au moins N bornes à 500 m.",
                    style="font-size:0.82rem; color:#555;",
                ),
                ui.layout_columns(
                    ui.input_numeric("g1_n",    "Min. bornes (N)", 20, min=1, max=100),
                    ui.input_action_button("g1_run", "▶ Analyser",
                                           class_="btn btn-primary btn-sm"),
                    col_widths=[7, 5],
                ),
                ui.output_ui("g1_summary"),
                ui.output_table("g1_table"),
            ),

            # G2 — Épiceries
            ui.card(
                ui.card_header("② Épiceries — bornes à proximité"),
                ui.p(
                    "Un gestionnaire souhaite savoir si toutes les épiceries "
                    "de Montréal ont des bornes à 300 m.",
                    style="font-size:0.82rem; color:#555;",
                ),
                ui.input_action_button("g2_run", "▶ Analyser",
                                       class_="btn btn-primary btn-sm"),
                ui.output_ui("g2_summary"),
                ui.output_table("g2_table"),
            ),

            width=1 / 2,
        ),

        ui.br(),

        # G6 — Multi-facteurs
        ui.card(
            ui.card_header("⑥ Pourquoi cette distribution ? — Analyse multi-facteurs"),
            ui.p(
                "Est-ce lié au profil de la population ? à la proximité de zones de loisirs ? "
                "à la présence de magasins ? — Corrélation Pearson sur 6 facteurs.",
                style="font-size:0.82rem; color:#555;",
            ),
            ui.input_action_button("g6_run", "▶ Analyser les facteurs",
                                   class_="btn btn-primary btn-sm"),
            ui.output_ui("g6_interp"),
            ui.output_table("g6_table"),
        ),
    ),

    # ── TAB 3 : ÉQUITÉ SOCIO-ÉCONOMIQUE ────────────────────────────────────
    ui.nav_panel(
        "📈 Équité socio-éco",
        ui.card(
            ui.card_header(
                "Les bornes dans les quartiers résidentiels sont-elles "
                "conditionnées au profil de la population ?"
            ),
            ui.p(
                "Scatter plot : couverture en bornes (%) vs revenu médian par arrondissement. "
                "La droite de régression révèle une corrélation positive → les arrondissements "
                "à revenu élevé sont mieux desservis.",
                style="font-size:0.82rem; color:#555;",
            ),
            ui.output_plot("equity_plot", height="480px"),
        ),
        ui.br(),
        ui.card(
            ui.card_header("Profil socio-démographique par arrondissement"),
            ui.output_table("equity_table"),
        ),
    ),

    # ── TITRE APP ──────────────────────────────────────────────────────────
    title=ui.span(
        "⚡ GeoCharge Montréal",
        style="font-weight:700; letter-spacing:0.5px;",
    ),
    bg="#0d1b2e",
    inverse=True,
    footer=ui.div(
        "GMQ580 — Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke · "
        "Données : Ville de Montréal (CC-BY 4.0) · StatCan Recensement 2021",
        style="text-align:center; font-size:0.7rem; color:#999; padding:4px;",
    ),
)


# ═══════════════════════════════════════════════════════════════════════════
# SERVEUR SHINY
# ═══════════════════════════════════════════════════════════════════════════

def server(input, output, session):

    # ── CARTE ──────────────────────────────────────────────────────────────
    @render.ui
    def map_output():
        m = build_map(
            show_bornes=input.show_bornes(),
            show_arrond=input.show_arrond(),
            demo_var=input.demo_var(),
        )
        html = m._repr_html_()
        # Forcer la hauteur de l'iframe folium
        html = html.replace(
            'style="width: 100%; height: 500px; border: none"',
            'style="width:100%; height:calc(100vh - 140px); border:none;"',
        )
        return ui.HTML(html)

    # ── G1 : PARCS ─────────────────────────────────────────────────────────
    @render.ui
    @reactive.event(input.g1_run)
    def g1_summary():
        n     = input.g1_n()
        insuf = parcs_gdf[parcs_gdf["nb_bornes_500m"] < n]
        total = len(parcs_gdf)
        count = len(insuf)
        pct_ok = round(100 * (total - count) / max(total, 1), 1)
        couleur = "success" if pct_ok >= 80 else "warning" if pct_ok >= 50 else "danger"
        return ui.div(
            ui.div(
                ui.strong(f"{count}"),
                f" parcs sur {total} ont moins de {n} bornes dans un rayon de 500 m.",
                class_=f"alert alert-{couleur}",
                style="font-size:0.88rem; padding:8px 12px; margin:8px 0;",
            ),
            ui.p(
                f"✅ {pct_ok}% des parcs atteignent le seuil cible de {n} bornes à 500 m.",
                style="font-size:0.82rem; color:#555;",
            ),
        )

    @render.table
    @reactive.event(input.g1_run)
    def g1_table():
        n     = input.g1_n()
        insuf = parcs_gdf[parcs_gdf["nb_bornes_500m"] < n].copy()
        insuf = insuf.sort_values("nb_bornes_500m")[["nom", "superficie_ha", "nb_bornes_500m"]].head(25)
        insuf.columns = ["Parc", "Superficie (ha)", f"Bornes à 500 m (< {n})"]
        return insuf.reset_index(drop=True)

    # ── G2 : ÉPICERIES ─────────────────────────────────────────────────────
    @render.ui
    @reactive.event(input.g2_run)
    def g2_summary():
        sans   = epiceries_gdf[~epiceries_gdf["has_borne_300m"]]
        total  = len(epiceries_gdf)
        count  = len(sans)
        pct_ok = round(100 * (total - count) / max(total, 1), 1)
        couleur = "success" if pct_ok >= 80 else "warning" if pct_ok >= 50 else "danger"
        return ui.div(
            ui.div(
                ui.strong(f"{count}"),
                f" épiceries sur {total} n'ont aucune borne dans un rayon de 300 m.",
                class_=f"alert alert-{couleur}",
                style="font-size:0.88rem; padding:8px 12px; margin:8px 0;",
            ),
            ui.p(
                f"✅ {pct_ok}% des épiceries ont au moins une borne à 300 m.",
                style="font-size:0.82rem; color:#555;",
            ),
        )

    @render.table
    @reactive.event(input.g2_run)
    def g2_table():
        sans = epiceries_gdf[~epiceries_gdf["has_borne_300m"]][["nom", "type", "adresse"]].head(25).copy()
        sans.columns = ["Épicerie", "Type", "Adresse"]
        return sans.reset_index(drop=True)

    # ── G6 : MULTI-FACTEURS ────────────────────────────────────────────────
    @reactive.calc
    @reactive.event(input.g6_run)
    def _g6_cors():
        df   = g6_df.dropna(subset=["pct_couverture"])
        covs = df["pct_couverture"].tolist()
        cors = {}
        for var in VAR_LABELS_G6:
            if var in df.columns:
                vals = df[var].fillna(df[var].median()).tolist()
                cors[var] = pearson(vals, covs)
        return sorted(
            [{"variable": k, "r": v,
              "label": VAR_LABELS_G6[k],
              "question": QUESTIONS_G6.get(k, "")} for k, v in cors.items()],
            key=lambda x: -abs(x["r"])
        )

    @render.ui
    @reactive.event(input.g6_run)
    def g6_interp():
        cors = _g6_cors()
        if not cors:
            return ui.p("Données insuffisantes.")
        top = cors[0]
        absR = abs(top["r"])
        if absR >= 0.4:
            direction = "positive" if top["r"] > 0 else "négative"
            txt = (f"Facteur dominant : « {top['label']} » (r = {top['r']}) — "
                   f"corrélation {direction} forte. Les zones avec "
                   f"{'plus de' if top['r']>0 else 'moins de'} {top['label'].lower()} "
                   f"tendent à avoir une meilleure couverture en bornes.")
            cls = "alert alert-info"
        elif absR >= 0.2:
            txt = (f"Facteur le plus lié : « {top['label']} » (r = {top['r']}) — "
                   f"corrélation modérée. La distribution est probablement multifactorielle.")
            cls = "alert alert-warning"
        else:
            txt = ("Aucun facteur isolé n'explique clairement la distribution. "
                   "La localisation des bornes est davantage liée à des décisions historiques "
                   "ou à la disponibilité foncière qu'à un critère socio-spatial unique.")
            cls = "alert alert-secondary"
        return ui.div(txt, class_=cls, style="font-size:0.88rem; margin:8px 0;")

    @render.table
    @reactive.event(input.g6_run)
    def g6_table():
        cors = _g6_cors()
        rows = []
        for f in cors:
            absR = abs(f["r"])
            force = "Forte" if absR >= 0.4 else "Modérée" if absR >= 0.2 else "Faible"
            dir_  = "↑ positive" if f["r"] > 0.05 else ("↓ négative" if f["r"] < -0.05 else "≈ nulle")
            rows.append({
                "Facteur":       f["label"],
                "r (Pearson)":   f["r"],
                "Direction":     dir_,
                "Force":         force,
                "Question prof": f["question"],
            })
        return pd.DataFrame(rows).reset_index(drop=True)

    # ── ÉQUITÉ ─────────────────────────────────────────────────────────────
    @render.plot
    def equity_plot():
        df = arrond_gdf[["nom", "pct_couverture",
                          "revenu_median_menage", "tx_faible_revenu_pct"]].dropna()

        fig, ax = plt.subplots(figsize=(11, 6))
        fig.patch.set_facecolor("#0d1b2e")
        ax.set_facecolor("#0a0e1a")

        sc = ax.scatter(
            df["revenu_median_menage"] / 1000,
            df["pct_couverture"],
            c=df["tx_faible_revenu_pct"],
            cmap="YlOrRd_r",
            s=90, alpha=0.9,
            edgecolors="#00d4ff", linewidths=0.6,
        )

        for _, row in df.iterrows():
            ax.annotate(
                row["nom"].split("–")[0].strip(),
                (row["revenu_median_menage"] / 1000, row["pct_couverture"]),
                fontsize=5.5, color="#9ab4cc", ha="center", va="bottom",
                xytext=(0, 4), textcoords="offset points",
            )

        # Droite de régression
        xs = df["revenu_median_menage"].values
        ys = df["pct_couverture"].values
        coeffs = np.polyfit(xs, ys, 1)
        x_line = np.linspace(xs.min(), xs.max(), 100)
        ax.plot(x_line / 1000, np.polyval(coeffs, x_line),
                color="#00d4ff", linewidth=1.5, linestyle="--", alpha=0.7,
                label="Régression linéaire")

        r = pearson(xs.tolist(), ys.tolist())
        ax.set_xlabel("Revenu médian des ménages (k$)",  color="#dce8f4", fontsize=10)
        ax.set_ylabel("Couverture en bornes (%)",         color="#dce8f4", fontsize=10)
        ax.set_title(
            f"Équité socio-économique — couverture vs revenu  (r = {r})\n"
            "Couleur = taux de faible revenu (rouge = vulnérable)",
            color="#dce8f4", fontsize=11,
        )
        ax.tick_params(colors="#6a8aaa", labelsize=8)
        for sp in ax.spines.values():
            sp.set_color("#1e3a5f")
        ax.legend(fontsize=8, facecolor="#0d1b2e", labelcolor="#dce8f4",
                  framealpha=0.7)

        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label("Faible revenu (%)", color="#dce8f4", fontsize=8)
        cbar.ax.yaxis.set_tick_params(color="#6a8aaa", labelcolor="#6a8aaa")

        plt.tight_layout(pad=1.5)
        return fig

    @render.table
    def equity_table():
        df = arrond_gdf[["nom", "pct_couverture", "nb_bornes",
                          "revenu_median_menage", "tx_voiture_pct",
                          "tx_faible_revenu_pct", "densite_pop_km2"]].copy()
        df = df.sort_values("pct_couverture").rename(columns={
            "nom":                  "Arrondissement",
            "pct_couverture":       "Couverture (%)",
            "nb_bornes":            "Nb bornes",
            "revenu_median_menage": "Revenu médian ($)",
            "tx_voiture_pct":       "Motorisation (%)",
            "tx_faible_revenu_pct": "Faible revenu (%)",
            "densite_pop_km2":      "Densité (hab/km²)",
        })
        return df.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
app = App(app_ui, server)
