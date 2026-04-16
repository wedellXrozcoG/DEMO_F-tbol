import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración
st.set_page_config(page_title="FIFA Data Scout", layout="wide")


# 2. Carga y limpieza
@st.cache_data
def load_data():
    df = pd.read_csv(r"D:\DEMO\players_22.csv")

    # AGREGADAS LAS COLUMNAS:
    cols_interes = [
        "short_name", "value_eur", "overall", "potential", "pace",
        "shooting", "passing", "dribbling", "defending", "physic",
        "age", "league_name", "nationality_name", "club_name", "preferred_foot"
    ]

    # Nos aseguramos de que solo cargue lo necesario para que sea rápido
    df = df[cols_interes]
    df = df.dropna(subset=["short_name", "value_eur", "overall"])
    return df


df_raw = load_data()

# 3. Filtros Globales
st.sidebar.header("Filtros")
# Usamos sorted() para que la lista de la feria se vea ordenada alfabéticamente
leagues = st.sidebar.multiselect("Liga:", options=sorted(df_raw["league_name"].dropna().unique()))
nations = st.sidebar.multiselect("Nacionalidad:", options=sorted(df_raw["nationality_name"].dropna().unique()))

df = df_raw.copy()
if leagues:
    df = df[df["league_name"].isin(leagues)]
if nations:
    df = df[df["nationality_name"].isin(nations)]

# 4. Estructura de Pestañas
tab1, tab2, tab3 = st.tabs(["Vista General", "Perfil Jugador", "Análisis de Mercado"])

with tab1:
    st.title("Big Data en el Fútbol")
    st.markdown("### Análisis de rendimiento y mercado de jugadores año 2022")
    st.write("")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Jugadores Filtrados", f"{len(df):,}")
    with m2:
        # Añadimos un manejo de error por si el filtro deja el df vacío
        val_promedio = df['value_eur'].mean() / 1e6 if not df.empty else 0
        st.metric("Valor Promedio", f"€{val_promedio:.1f}M")
    with m3:
        pot_max = df["potential"].max() if not df.empty else 0
        st.metric("Potencial Top", pot_max)

    st.divider()

    # Creamos las dos columnas
    col_izq, col_der = st.columns(2, gap="large")

    # Distribución de Calidad
    with col_izq:
        with st.container(border=True):
            st.subheader("Distribución de Calidad")

            # Lógica del Histograma
            mean_overall = df['overall'].mean() if not df.empty else 0
            fig_hist = px.histogram(
                df, x="overall", nbins=20,
                color_discrete_sequence=['#00CC96'],
                template="plotly_white",
                labels={'overall': 'Calidad', 'count': 'Cantidad'}
            )

            fig_hist.add_vline(x=mean_overall, line_dash="dash", line_color="#FF4B4B",
                               annotation_text=f"Promedio: {mean_overall:.1f}",
                               annotation_position="top right")

            fig_hist.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                bargap=0.1,
                xaxis_title="Nivel",
                yaxis_title="Jugadores"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # Grafico Joyas Ocultas
    with col_der:
        with st.container(border=True):
            st.subheader("Joyas Ocultas")

            # Lógica de Joyas Ocultas
            df_joyas = df[(df['age'] <= 23) & (df['potential'] >= 85)]

            st.markdown(f"**{len(df_joyas)}** jóvenes promesas detectadas.")

            fig_joyas = px.scatter(
                df_joyas,
                x="age",
                y="potential",
                color="overall",
                hover_name="short_name",
                color_continuous_scale="Viridis",
                template="plotly_white"
            )

            fig_joyas.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title="Edad",
                yaxis_title="Potencial"
            )
            st.plotly_chart(fig_joyas, use_container_width=True)

    st.divider()
    st.subheader("Muestra de Datos")
    st.dataframe(df[["short_name", "overall", "potential", "value_eur", "club_name"]].head(50),
                 use_container_width=True)

with tab2:
    st.subheader("Scouting y Comparación Directa")

    # Selección de jugadores en dos columnas
    c_sel1, c_sel2 = st.columns(2)

    with c_sel1:
        p1_name = st.selectbox("Selecciona Jugador 1:", df["short_name"].unique(), key="p1")
        p1_data = df[df["short_name"] == p1_name].iloc[0]

    with c_sel2:
        # Añadimos una opción de "Ninguno" para que la comparación sea opcional
        opciones_p2 = ["Ninguno"] + list(df["short_name"].unique())
        p2_name = st.selectbox("Comparar con (Opcional):", opciones_p2, key="p2")

    st.divider()

    # Layout: Info a la izquierda, Radar a la derecha
    col_info, col_radar = st.columns([1, 2])

    with col_info:
        # Info Jugador 1
        st.write(f"### {p1_name}")
        st.caption(f"Club: {p1_data['club_name']}")
        st.metric("Overall", p1_data['overall'])

        if p2_name != "Ninguno":
            p2_data = df[df["short_name"] == p2_name].iloc[0]
            st.divider()
            # Info Jugador 2
            st.write(f"### {p2_name}")
            st.caption(f"Club: {p2_data['club_name']}")
            st.metric("Overall", p2_data['overall'], delta=int(p2_data['overall'] - p1_data['overall']))

    with col_radar:
        categories = ['Ritmo', 'Tiro', 'Pase', 'Regate', 'Defensa', 'Físico']

        fig = go.Figure()

        # Trazado del Jugador 1 (Verde)
        fig.add_trace(go.Scatterpolar(
            r=[p1_data['pace'], p1_data['shooting'], p1_data['passing'],
               p1_data['dribbling'], p1_data['defending'], p1_data['physic']],
            theta=categories,
            fill='toself',
            name=p1_name,
            line_color='#00CC96'
        ))

        # Trazado del Jugador 2 (Si existe) en color Naranja/Rojo
        if p2_name != "Ninguno":
            fig.add_trace(go.Scatterpolar(
                r=[p2_data['pace'], p2_data['shooting'], p2_data['passing'],
                   p2_data['dribbling'], p2_data['defending'], p2_data['physic']],
                theta=categories,
                fill='toself',
                name=p2_name,
                line_color='#FF4B4B'
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="lightgray"),
                angularaxis=dict(gridcolor="lightgray")
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("📈 Relación Valor vs Potencial")
    if not df.empty:
        fig_scatter = px.scatter(
            df.head(500), x="value_eur", y="overall", size="potential", color="age",
            hover_name="short_name", color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.write("Selecciona filtros para ver el análisis de mercado.")

    st.subheader("Arquitectura Financiera del Fútbol Mundial")
    st.markdown(
        "Explora la distribución del valor de mercado por Liga y Club. *Haz clic en una liga para profundizar en sus equipos.*")

    # 1. Preparación de datos limpia
    # Filtramos las ligas top y eliminamos posibles nulos en nombres
    top_n_ligas = 6
    filtro_ligas = df.groupby('league_name')['value_eur'].sum().nlargest(top_n_ligas).index
    df_tree = df[df['league_name'].isin(filtro_ligas)].copy()

    # Redondeamos el valor para que el hover no tenga demasiados decimales
    df_tree['valor_millones'] = df_tree['value_eur'] / 1e6

    # 2. Creación del Treemap Profesional
    fig_tree = px.treemap(
        df_tree,
        path=[px.Constant("Mercado Global"), 'league_name', 'club_name'],
        values='value_eur',
        color='overall',
        color_continuous_scale='GnBu',  # Escala azul-verde, más sobria y elegante
        range_color=[70, 85],  # Enfocamos el color en el rango de jugadores élite
        hover_data={'value_eur': ':,.0f', 'overall': ':.1f'}
    )

    # 3. Refinado de Estilo (Look & Feel)
    fig_tree.update_traces(
        textinfo="label+value",
        texttemplate="<b>%{label}</b><br>€%{value:,.2s}",  # Formato tipo 1.2B o 500M
        hovertemplate="<b>%{label}</b><br>Valor: €%{value:,.0f}<br>Media: %{color:.1f}",
        marker=dict(pad=dict(t=30, l=5, r=5, b=5)),  # Añade aire entre cuadros
        selector=dict(type='treemap')
    )

    fig_tree.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        height=650,  # Más alto para que se aprecien los clubes pequeños
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_colorbar=dict(
            title="Calidad (AVG)",
            thicknessmode="pixels", thickness=15,
            lenmode="pixels", len=300,
            yanchor="top", y=1,
            ticks="outside"
        )
    )

    # Mostrar con un contenedor con borde para estilo
    with st.container(border=True):
        st.plotly_chart(fig_tree, use_container_width=True)