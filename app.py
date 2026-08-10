from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_PATH = Path(__file__).parent / "data" / "Incidencias.csv"
STATUS_WEIGHTS = {"Agotado": 2, "Casi agotado": 1}
STATUS_COLORS = {"Agotado": "#C2410C", "Casi agotado": "#D97706"}
BRAND_RED = "#A6251D"
INK = "#1F2937"


st.set_page_config(
    page_title="Dashboard de Incidencias",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --brand: #A6251D;
        --brand-dark: #7F1D1D;
        --ink: #1F2937;
        --muted: #6B7280;
        --line: #E5E7EB;
        --surface: #FFFFFF;
        --soft: #F8FAFC;
    }

    .stApp {
        background: #F6F7F9;
        color: var(--ink);
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--ink);
    }

    .main .block-container {
        padding-top: 1.6rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }

    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: 0;
    }

    h1 {
        font-size: 2rem;
        line-height: 1.18;
        margin-bottom: 0.25rem;
    }

    h2 {
        font-size: 1.35rem;
        margin-top: 0.5rem;
    }

    .subtitle {
        color: var(--muted);
        font-size: 0.98rem;
        margin-bottom: 1rem;
    }

    .section-note {
        color: var(--muted);
        font-size: 0.92rem;
        margin-top: -0.4rem;
        margin-bottom: 0.8rem;
    }

    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem 1rem 0.8rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        min-height: 112px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: 0.82rem;
    }

    [data-testid="stMetricValue"] {
        color: var(--ink);
        font-size: 1.55rem;
        line-height: 1.2;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
    }

    .block-spacer {
        height: 0.7rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.55rem 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [col.strip() for col in df.columns]

    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
    df["Hora"] = pd.to_datetime(df["Hora"], format="%H:%M:%S", errors="coerce").dt.time
    df["FechaHora"] = pd.to_datetime(
        df["Fecha"].dt.strftime("%Y-%m-%d") + " " + df["Hora"].astype(str),
        errors="coerce",
    )
    df["Hora_Num"] = df["FechaHora"].dt.hour
    df["Dia"] = df["Fecha"].dt.date
    df["Dia Texto"] = df["Fecha"].dt.strftime("%d/%m/%Y")
    df["Dia_Semana"] = df["Fecha"].dt.day_name(locale=None)
    df["Existencia"] = pd.to_numeric(df["Existencia"], errors="coerce")
    df["Observaciones"] = df["Observaciones"].fillna("").astype(str).str.strip()

    if "Código" in df.columns:
        df["Código Original"] = df["Código"].astype(str)
        df["Código"] = df["Código"].replace({"6-Aug": "8/6", "5-Aug": "8/5"})
    else:
        df["Código"] = "Sin código"
        df["Código Original"] = "Sin código"

    df["Peso Criticidad"] = df["Estado"].map(STATUS_WEIGHTS).fillna(1)
    df["Bloque Horario"] = pd.cut(
        df["Hora_Num"],
        bins=[-1, 11, 14, 17, 20, 23],
        labels=["Apertura", "Mediodía", "Tarde", "Cena", "Cierre"],
    )
    return df


def format_number(value: float | int, suffix: str = "") -> str:
    if pd.isna(value):
        return "N/D"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}{suffix}"
    return f"{int(value):,}{suffix}"


def pct(value: float) -> str:
    return "N/D" if pd.isna(value) else f"{value:.1f}%"


def base_layout(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=42, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Arial", color=INK, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E5E7EB", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    orientation: str = "h",
    height: int = 420,
) -> go.Figure:
    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        title=title,
        color_discrete_map=STATUS_COLORS,
        text=x if orientation == "h" else y,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(title_font_size=17)
    if orientation == "h":
        fig.update_yaxes(categoryorder="total ascending")
    return base_layout(fig, height)


def empty_state(message: str) -> None:
    st.info(message, icon="ℹ️")


df = load_data(DATA_PATH)

st.sidebar.title("Filtros")
st.sidebar.caption("Ajusta el corte de análisis")

valid_dates = df["Fecha"].dropna()
min_date = valid_dates.min().date()
max_date = valid_dates.max().date()

date_range = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

sucursales = st.sidebar.multiselect(
    "Sucursal",
    sorted(df["Sucursal"].dropna().unique()),
    default=sorted(df["Sucursal"].dropna().unique()),
)
estados = st.sidebar.multiselect(
    "Estado",
    sorted(df["Estado"].dropna().unique()),
    default=sorted(df["Estado"].dropna().unique()),
)
insumos = st.sidebar.multiselect(
    "Insumo",
    sorted(df["Insumo"].dropna().unique()),
    default=[],
    placeholder="Todos los insumos",
)
unidades = st.sidebar.multiselect(
    "Unidad de medida",
    sorted(df["U.M."].dropna().unique()),
    default=sorted(df["U.M."].dropna().unique()),
)
codigos = st.sidebar.multiselect(
    "Código",
    sorted(df["Código"].dropna().unique()),
    default=sorted(df["Código"].dropna().unique()),
)
hour_range = st.sidebar.slider(
    "Hora",
    min_value=0,
    max_value=23,
    value=(0, 23),
    format="%d:00",
)

filtered = df.copy()
filtered = filtered[
    (filtered["Fecha"].dt.date >= start_date)
    & (filtered["Fecha"].dt.date <= end_date)
    & (filtered["Sucursal"].isin(sucursales))
    & (filtered["Estado"].isin(estados))
    & (filtered["U.M."].isin(unidades))
    & (filtered["Código"].isin(codigos))
    & (filtered["Hora_Num"].between(hour_range[0], hour_range[1]))
]

if insumos:
    filtered = filtered[filtered["Insumo"].isin(insumos)]

page = st.sidebar.radio(
    "Página",
    [
        "Resumen ejecutivo",
        "Sucursales",
        "Insumos",
        "Tiempo",
        "Detalle y calidad",
    ],
)

st.title("Dashboard de Incidencias")
st.markdown(
    f"<div class='subtitle'>Inventario operativo | {start_date:%d/%m/%Y} - {end_date:%d/%m/%Y}</div>",
    unsafe_allow_html=True,
)

if filtered.empty:
    empty_state("No hay registros para la combinación de filtros seleccionada.")
    st.stop()

total = len(filtered)
agotado = int((filtered["Estado"] == "Agotado").sum())
casi = int((filtered["Estado"] == "Casi agotado").sum())
agotado_pct = agotado / total * 100 if total else 0
unique_items = filtered["Insumo"].nunique()
unique_branches = filtered["Sucursal"].nunique()
peak_day = filtered.groupby("Dia").size().idxmax()
peak_hour = int(filtered.groupby("Hora_Num").size().idxmax())

kpi_cols = st.columns(6)
kpi_cols[0].metric("Incidencias", format_number(total))
kpi_cols[1].metric("% Agotado", pct(agotado_pct), f"{agotado} registros")
kpi_cols[2].metric("Casi agotado", format_number(casi))
kpi_cols[3].metric("Insumos únicos", format_number(unique_items))
kpi_cols[4].metric("Sucursales", format_number(unique_branches))
kpi_cols[5].metric("Hora pico", f"{peak_hour:02d}:00")

st.markdown("<div class='block-spacer'></div>", unsafe_allow_html=True)

if page == "Resumen ejecutivo":
    left, right = st.columns([1.15, 0.85])

    with left:
        by_date_status = (
            filtered.groupby(["Fecha", "Estado"], as_index=False)
            .size()
            .rename(columns={"size": "Incidencias"})
        )
        fig = px.line(
            by_date_status,
            x="Fecha",
            y="Incidencias",
            color="Estado",
            markers=True,
            title="Tendencia diaria por estado",
            color_discrete_map=STATUS_COLORS,
        )
        st.plotly_chart(base_layout(fig, 390), use_container_width=True)

    with right:
        by_status = filtered["Estado"].value_counts().reset_index()
        by_status.columns = ["Estado", "Incidencias"]
        fig = px.pie(
            by_status,
            names="Estado",
            values="Incidencias",
            title="Distribución por estado",
            hole=0.62,
            color="Estado",
            color_discrete_map=STATUS_COLORS,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(base_layout(fig, 390), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        branch_rank = (
            filtered.groupby("Sucursal", as_index=False)
            .size()
            .rename(columns={"size": "Incidencias"})
            .sort_values("Incidencias", ascending=False)
        )
        st.plotly_chart(
            bar_chart(
                branch_rank,
                "Incidencias",
                "Sucursal",
                "Incidencias por sucursal",
                height=430,
            ),
            use_container_width=True,
        )

    with col_b:
        item_rank = (
            filtered.groupby("Insumo", as_index=False)
            .size()
            .rename(columns={"size": "Incidencias"})
            .sort_values("Incidencias", ascending=False)
            .head(10)
        )
        st.plotly_chart(
            bar_chart(item_rank, "Incidencias", "Insumo", "Top 10 insumos", height=430),
            use_container_width=True,
        )

    heat_data = (
        filtered.groupby(["Sucursal", "Insumo"], as_index=False)
        .size()
        .rename(columns={"size": "Incidencias"})
    )
    top_heat_items = (
        heat_data.groupby("Insumo")["Incidencias"]
        .sum()
        .sort_values(ascending=False)
        .head(18)
        .index
    )
    heat_data = heat_data[heat_data["Insumo"].isin(top_heat_items)]
    matrix = heat_data.pivot(index="Sucursal", columns="Insumo", values="Incidencias").fillna(0)
    fig = px.imshow(
        matrix,
        aspect="auto",
        title="Matriz sucursal vs insumo",
        color_continuous_scale=["#FFF7ED", "#FDBA74", "#C2410C"],
        labels=dict(color="Incidencias"),
    )
    st.plotly_chart(base_layout(fig, 510), use_container_width=True)

elif page == "Sucursales":
    branch_summary = (
        filtered.assign(Agotado=(filtered["Estado"] == "Agotado").astype(int))
        .groupby("Sucursal")
        .agg(
            Incidencias=("ID Reporte", "count"),
            Agotados=("Agotado", "sum"),
            Insumos_Unicos=("Insumo", "nunique"),
            Existencia_Promedio=("Existencia", "mean"),
            Criticidad=("Peso Criticidad", "sum"),
        )
        .reset_index()
    )
    branch_summary["% Agotado"] = branch_summary["Agotados"] / branch_summary["Incidencias"] * 100

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.plotly_chart(
            bar_chart(
                branch_summary.sort_values("Criticidad", ascending=False),
                "Criticidad",
                "Sucursal",
                "Índice de criticidad por sucursal",
                height=420,
            ),
            use_container_width=True,
        )
    with col_b:
        status_branch = (
            filtered.groupby(["Sucursal", "Estado"], as_index=False)
            .size()
            .rename(columns={"size": "Incidencias"})
        )
        st.plotly_chart(
            bar_chart(
                status_branch,
                "Incidencias",
                "Sucursal",
                "Estado",
                color="Estado",
                height=420,
            ),
            use_container_width=True,
        )

    st.subheader("Resumen por sucursal")
    st.dataframe(
        branch_summary.sort_values("Criticidad", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "% Agotado": st.column_config.NumberColumn("% Agotado", format="%.1f%%"),
            "Existencia_Promedio": st.column_config.NumberColumn("Existencia promedio", format="%.1f"),
        },
    )

    selected_branch = st.selectbox("Sucursal para análisis de insumos", branch_summary["Sucursal"])
    branch_items = (
        filtered[filtered["Sucursal"] == selected_branch]
        .groupby(["Insumo", "Estado"], as_index=False)
        .size()
        .rename(columns={"size": "Incidencias"})
        .sort_values("Incidencias", ascending=False)
        .head(15)
    )
    st.plotly_chart(
        bar_chart(
            branch_items,
            "Incidencias",
            "Insumo",
            f"Top insumos en {selected_branch}",
            color="Estado",
            height=520,
        ),
        use_container_width=True,
    )

elif page == "Insumos":
    item_summary = (
        filtered.groupby("Insumo")
        .agg(
            Incidencias=("ID Reporte", "count"),
            Sucursales_Afectadas=("Sucursal", "nunique"),
            Dias_Con_Incidencia=("Dia", "nunique"),
            Existencia_Promedio=("Existencia", "mean"),
            Criticidad=("Peso Criticidad", "sum"),
        )
        .reset_index()
    )
    item_summary["Cobertura"] = item_summary["Sucursales_Afectadas"] / max(unique_branches, 1) * 100

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(
            bar_chart(
                item_summary.sort_values("Criticidad", ascending=False).head(15),
                "Criticidad",
                "Insumo",
                "Índice de criticidad por insumo",
                height=560,
            ),
            use_container_width=True,
        )
    with col_b:
        coverage = item_summary.sort_values(
            ["Sucursales_Afectadas", "Incidencias"], ascending=False
        ).head(15)
        st.plotly_chart(
            bar_chart(
                coverage,
                "Sucursales_Afectadas",
                "Insumo",
                "Sucursales afectadas por insumo",
                height=560,
            ),
            use_container_width=True,
        )

    combo = (
        filtered.groupby(["Sucursal", "Insumo"], as_index=False)
        .agg(Incidencias=("ID Reporte", "count"), Criticidad=("Peso Criticidad", "sum"))
        .sort_values(["Criticidad", "Incidencias"], ascending=False)
        .head(20)
    )
    combo["Combinación"] = combo["Sucursal"] + " | " + combo["Insumo"]
    st.plotly_chart(
        bar_chart(
            combo,
            "Criticidad",
            "Combinación",
            "Top combinaciones sucursal-insumo",
            height=620,
        ),
        use_container_width=True,
    )

    st.subheader("Resumen por insumo")
    st.dataframe(
        item_summary.sort_values("Criticidad", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Cobertura": st.column_config.NumberColumn("Cobertura", format="%.1f%%"),
            "Existencia_Promedio": st.column_config.NumberColumn("Existencia promedio", format="%.1f"),
        },
    )

elif page == "Tiempo":
    col_a, col_b = st.columns([1.1, 0.9])
    with col_a:
        by_hour = (
            filtered.groupby(["Hora_Num", "Estado"], as_index=False)
            .size()
            .rename(columns={"size": "Incidencias"})
        )
        fig = px.bar(
            by_hour,
            x="Hora_Num",
            y="Incidencias",
            color="Estado",
            title="Incidencias por hora",
            color_discrete_map=STATUS_COLORS,
        )
        fig.update_xaxes(dtick=1, title="Hora")
        st.plotly_chart(base_layout(fig, 430), use_container_width=True)

    with col_b:
        by_block = (
            filtered.groupby("Bloque Horario", observed=False)
            .size()
            .reset_index(name="Incidencias")
            .dropna()
        )
        fig = px.bar(
            by_block,
            x="Bloque Horario",
            y="Incidencias",
            title="Concentración por bloque horario",
            color_discrete_sequence=[BRAND_RED],
            text="Incidencias",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(base_layout(fig, 430), use_container_width=True)

    by_day_hour = (
        filtered.groupby(["Dia Texto", "Hora_Num"], as_index=False)
        .size()
        .rename(columns={"size": "Incidencias"})
    )
    matrix = by_day_hour.pivot(index="Dia Texto", columns="Hora_Num", values="Incidencias").fillna(0)
    fig = px.imshow(
        matrix,
        aspect="auto",
        title="Mapa de calor día vs hora",
        color_continuous_scale=["#F8FAFC", "#FDBA74", "#C2410C"],
        labels=dict(color="Incidencias"),
    )
    st.plotly_chart(base_layout(fig, 430), use_container_width=True)

    top_hours = filtered.groupby("Hora_Num").size().sort_values(ascending=False).head(3).sum()
    concentration = top_hours / total * 100
    st.metric("Concentración en las 3 horas más críticas", pct(concentration))

elif page == "Detalle y calidad":
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Registros con observación", format_number((filtered["Observaciones"] != "").sum()))
    col_b.metric("Existencia promedio", format_number(filtered["Existencia"].mean()))
    col_c.metric("Existencia mínima", format_number(filtered["Existencia"].min()))
    col_d.metric("Existencia máxima", format_number(filtered["Existencia"].max()))

    duplicated_semantic = filtered.duplicated(
        subset=["Fecha", "Sucursal", "Insumo", "Existencia", "Código", "Estado"],
        keep=False,
    )
    quality = pd.DataFrame(
        {
            "Validación": [
                "Fechas no válidas",
                "Horas no válidas",
                "Existencias no numéricas",
                "Registros posiblemente duplicados",
                "Observaciones vacías",
            ],
            "Registros": [
                int(filtered["Fecha"].isna().sum()),
                int(filtered["Hora"].isna().sum()),
                int(filtered["Existencia"].isna().sum()),
                int(duplicated_semantic.sum()),
                int((filtered["Observaciones"] == "").sum()),
            ],
        }
    )

    left, right = st.columns([0.75, 1.25])
    with left:
        st.subheader("Calidad de datos")
        st.dataframe(quality, use_container_width=True, hide_index=True)
    with right:
        observations = filtered[filtered["Observaciones"] != ""][
            ["Fecha", "Hora", "Sucursal", "Insumo", "Estado", "Observaciones"]
        ].sort_values(["Fecha", "Hora"])
        st.subheader("Observaciones capturadas")
        if observations.empty:
            empty_state("No hay observaciones para el corte seleccionado.")
        else:
            st.dataframe(observations, use_container_width=True, hide_index=True)

    st.subheader("Detalle filtrado")
    detail_cols = [
        "ID Reporte",
        "Fecha",
        "Hora",
        "Sucursal",
        "Insumo",
        "U.M.",
        "Existencia",
        "Código",
        "Estado",
        "Observaciones",
    ]
    st.dataframe(
        filtered[detail_cols].sort_values(["Fecha", "Hora", "Sucursal"]),
        use_container_width=True,
        hide_index=True,
        height=520,
    )

    csv = filtered[detail_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar CSV filtrado",
        data=csv,
        file_name="incidencias_filtradas.csv",
        mime="text/csv",
        use_container_width=True,
    )
