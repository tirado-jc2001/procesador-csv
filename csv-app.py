import io
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Comparativa Rocky DEM - Tega Industries",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilo visual de la barra lateral
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #E6F3FA;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def leer_csv_rocky(uploaded_file, rol_variable):
  """Lee un CSV exportado por Ansys Rocky (separador ';' y coma decimal ',')
    y devuelve un DataFrame con ['TIME', rol_variable].
    """
  if uploaded_file is None:
    return None

  uploaded_file.seek(0)
  df = pd.read_csv(uploaded_file, sep=";", decimal=",")
  df.columns = [str(c).strip() for c in df.columns]

  if len(df.columns) < 2:
    raise ValueError(
        f"El archivo '{uploaded_file.name}' no tiene al menos 2 columnas."
    )

  # Columna de tiempo: prioriza 'Date [s]' o 'TIME'
  col_tiempo = None
  for col in df.columns:
    c_low = col.lower()
    if "date" in c_low or c_low.startswith("time"):
      col_tiempo = col
      break
  if col_tiempo is None:
    col_tiempo = df.columns[0]

  # Columna de variable: primera columna distinta al tiempo
  cols_valor = [c for c in df.columns if c != col_tiempo]
  col_valor = cols_valor[0]

  out = pd.DataFrame({
      "TIME": pd.to_numeric(df[col_tiempo], errors="coerce"),
      rol_variable: pd.to_numeric(df[col_valor], errors="coerce"),
  })

  out = out.dropna(subset=["TIME"]).sort_values("TIME")
  out = out.groupby("TIME", as_index=False)[rol_variable].mean()
  return out


def construir_dataframe_modelo(
    file_fuerza,
    file_energia,
    file_potencia,
    potencia_nominal_mw=0.0,
    unidad_potencia_archivo="W",
    invertir_signo_potencia=False,
):
  """Une los 3 CSV de un modelo por 'TIME' y calcula Potencia (MW) + Potencia Nominal."""
  df_f = leer_csv_rocky(file_fuerza, "Fuerza")
  df_e = leer_csv_rocky(file_energia, "Energia")
  df_p = leer_csv_rocky(file_potencia, "Potencia_raw")

  dfs = [d for d in [df_f, df_e, df_p] if d is not None]
  if not dfs:
    return None

  df_total = dfs[0]
  for d in dfs[1:]:
    df_total = pd.merge(df_total, d, on="TIME", how="outer")

  df_total = df_total.sort_values("TIME").reset_index(drop=True)

  for col in ["Fuerza", "Energia"]:
    if col not in df_total.columns:
      df_total[col] = np.nan

  if "Potencia_raw" in df_total.columns:
    factor = {"W": 1e-6, "kW": 1e-3, "MW": 1.0}[unidad_potencia_archivo]
    signo = -1.0 if invertir_signo_potencia else 1.0
    df_total["Potencia"] = (
        df_total["Potencia_raw"] * signo * factor
    ) + potencia_nominal_mw
  else:
    df_total["Potencia"] = np.nan

  return df_total[["TIME", "Fuerza", "Energia", "Potencia"]]


def recortar_a_ventana_comun(df_act, df_prop):
  """Recorta ambos DataFrames al intervalo de tiempo donde ambos tienen datos."""
  if df_act is None or df_prop is None or df_act.empty or df_prop.empty:
    return df_act, df_prop, None, None

  t_inicio = max(df_act["TIME"].min(), df_prop["TIME"].min())
  t_fin = min(df_act["TIME"].max(), df_prop["TIME"].max())

  if t_inicio > t_fin:
    return df_act, df_prop, None, None

  df_act_corte = df_act[
      (df_act["TIME"] >= t_inicio) & (df_act["TIME"] <= t_fin)
  ].copy()
  df_prop_corte = df_prop[
      (df_prop["TIME"] >= t_inicio) & (df_prop["TIME"] <= t_fin)
  ].copy()

  return (
      df_act_corte.reset_index(drop=True),
      df_prop_corte.reset_index(drop=True),
      t_inicio,
      t_fin,
  )


# ==========================================
#  BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
  try:
    st.image("logoTEGA.jpg", use_container_width=True)
  except Exception:
    st.title("🏢 TEGA INDUSTRIES")

  st.markdown("---")
  st.header("📂 1. Modelo Actual (3 CSV Rocky)")
  act_fuerza = st.file_uploader(
      "Fuerza Compresiva - Actual [N]", type=["csv"], key="act_f"
  )
  act_energia = st.file_uploader(
      "Energía Cinética - Actual [N·m / J]", type=["csv"], key="act_e"
  )
  act_potencia = st.file_uploader(
      "Potencia - Actual [W]", type=["csv"], key="act_p"
  )

  st.markdown("---")
  st.header("📂 2. Modelo Propuesto (3 CSV Rocky)")
  prop_fuerza = st.file_uploader(
      "Fuerza Compresiva - Propuesto [N]", type=["csv"], key="prop_f"
  )
  prop_energia = st.file_uploader(
      "Energía Cinética - Propuesto [N·m / J]", type=["csv"], key="prop_e"
  )
  prop_potencia = st.file_uploader(
      "Potencia - Propuesto [W]", type=["csv"], key="prop_p"
  )

  st.markdown("---")
  st.header("⚡ 3. Potencia Nominal y Unidades")
  pot_nom_actual = st.number_input(
      "Potencia Nominal ACTUAL (MW):",
      value=0.0,
      step=0.1,
      format="%.3f",
      help="Se suma a la potencia convertida a MW del Modelo Actual.",
  )
  pot_nom_propuesto = st.number_input(
      "Potencia Nominal PROPUESTO (MW):",
      value=0.0,
      step=0.1,
      format="%.3f",
      help="Se suma a la potencia convertida a MW del Modelo Propuesto.",
  )
  unidad_pot = st.selectbox(
      "Unidad en CSV de Potencia:", options=["W", "kW", "MW"], index=0
  )
  invertir_pot = st.checkbox(
      "Invertir signo de Potencia (-1)",
      value=False,
      help=(
          "En Rocky suele venir positiva; activa solo si necesitas cambiar el"
          " signo."
      ),
  )

  st.markdown("---")
  st.header("🎨 4. Tiempo, Recorte y Estilo")
  recortar_comun = st.checkbox(
      "Cortar ambos modelos al tiempo común",
      value=True,
      help=(
          "Limita ambos modelos hasta el último segundo donde ambos tienen"
          " datos (ej. si uno corre 25 s y otro 20 s, corta en 20 s)."
      ),
  )

  col_s1, col_s2 = st.columns(2)
  with col_s1:
    x_min = st.number_input("Segundo INICIO", value=8.0, step=0.5, format="%.2f")
  with col_s2:
    x_max = st.number_input(
        "Segundo FINAL", value=20.0, step=0.5, format="%.2f"
    )

  color_actual = st.color_picker("Color Modelo Actual", value="#A9A9A9")
  color_propuesto = st.color_picker("Color Modelo Propuesto", value="#00A2E8")

  st.markdown("---")
  st.caption("🛠️ **Desarrollado por:** Julio Tirado")
  st.caption("💡 *Simulación DEM y Análisis de Proyectos*")


# ==========================================
# PANTALLA PRINCIPAL
# ==========================================
st.title("🚀 Comparativa de Simulaciones — Ansys Rocky")
st.write(
    "Carga los 3 archivos CSV por modelo (Fuerza, Energía y Potencia) e"
    " ingresa la **Potencia Nominal (MW)** para consolidar y comparar resultados."
)

tiene_algo_actual = any(
    x is not None for x in [act_fuerza, act_energia, act_potencia]
)
tiene_algo_propuesto = any(
    x is not None for x in [prop_fuerza, prop_energia, prop_potencia]
)

if tiene_algo_actual and tiene_algo_propuesto:
  try:
    df_actual = construir_dataframe_modelo(
        act_fuerza,
        act_energia,
        act_potencia,
        potencia_nominal_mw=pot_nom_actual,
        unidad_potencia_archivo=unidad_pot,
        invertir_signo_potencia=invertir_pot,
    )
    df_propuesto = construir_dataframe_modelo(
        prop_fuerza,
        prop_energia,
        prop_potencia,
        potencia_nominal_mw=pot_nom_propuesto,
        unidad_potencia_archivo=unidad_pot,
        invertir_signo_potencia=invertir_pot,
    )

    if recortar_comun:
      df_actual, df_propuesto, t_ini_c, t_fin_c = recortar_a_ventana_comun(
          df_actual, df_propuesto
      )
      if t_ini_c is not None and t_fin_c is not None:
        st.info(
            "✂️ **Recorte a ventana común activo:** Ambos modelos se comparan"
            f" desde **{t_ini_c:.2f} s** hasta **{t_fin_c:.2f} s**."
        )

    columnas_stats = ["Fuerza", "Energia", "Potencia"]

    st.markdown("### 📊 Resumen Ejecutivo (Medianas)")
    m_act = df_actual[columnas_stats].median(skipna=True)
    m_prop = df_propuesto[columnas_stats].median(skipna=True)
    v_pct = ((m_prop - m_act) / m_act.replace(0, np.nan)) * 100

    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric(
        "Fuerza Compresiva",
        f"{m_prop['Fuerza']:.2f} N"
        if pd.notna(m_prop["Fuerza"])
        else "Sin dato",
        f"{v_pct['Fuerza']:+.2f}%" if pd.notna(v_pct["Fuerza"]) else None,
    )
    c_m2.metric(
        "Energía Cinética",
        f"{m_prop['Energia']:.2f} N·m"
        if pd.notna(m_prop["Energia"])
        else "Sin dato",
        f"{v_pct['Energia']:+.2f}%" if pd.notna(v_pct["Energia"]) else None,
    )
    c_m3.metric(
        "Potencia Total (Sim + Nominal)",
        f"{m_prop['Potencia']:.2f} MW"
        if pd.notna(m_prop["Potencia"])
        else "Sin dato",
        f"{v_pct['Potencia']:+.2f}%" if pd.notna(v_pct["Potencia"]) else None,
    )

    st.markdown("---")
    st.subheader("📈 Estadísticas Detalladas")
    stats_actual = df_actual[columnas_stats].agg(["mean", "max", "min", "median"])
    stats_propuesto = df_propuesto[columnas_stats].agg(
        ["mean", "max", "min", "median"]
    )
    stats_actual.index = ["promedio", "max", "min", "mediana"]
    stats_propuesto.index = ["promedio", "max", "min", "mediana"]

    tab1, tab2, tab3 = st.tabs(
        ["Modelo Actual", "Modelo Propuesto", "Comparativa de Medianas"]
    )

    with tab1:
      st.dataframe(stats_actual.style.format("{:.2f}"), use_container_width=True)
    with tab2:
      st.dataframe(
          stats_propuesto.style.format("{:.2f}"), use_container_width=True
      )
    with tab3:
      tabla_comparativa = pd.DataFrame({
          "Mediana Actual": m_act,
          "Mediana Propuesta": m_prop,
          "Variación (%)": v_pct,
      })
      st.dataframe(
          tabla_comparativa.style.format({
              "Mediana Actual": "{:.2f}",
              "Mediana Propuesta": "{:.2f}",
              "Variación (%)": "{:+.2f}%",
          }),
          use_container_width=True,
      )

    st.markdown("---")
    st.subheader("📉 Gráficas Comparativas")

    salto_x = 0.50 if (x_max - x_min) <= 5 else 1.0
    sns.set_style("white")

    def mostrar_grafica_comparativa(
        columna_y, titulo, ylabel, unidad="", color_y="darkorange"
    ):
      df_act_filt = df_actual[
          (df_actual["TIME"] >= x_min) & (df_actual["TIME"] <= x_max)
      ].dropna(subset=["TIME", columna_y])
      df_prop_filt = df_propuesto[
          (df_propuesto["TIME"] >= x_min) & (df_propuesto["TIME"] <= x_max)
      ].dropna(subset=["TIME", columna_y])

      if df_act_filt.empty or df_prop_filt.empty:
        st.warning(
            f"⚠️ Falta cargar o no hay datos de '{columna_y}' en ambos modelos"
            f" entre {x_min}s y {x_max}s."
        )
        return

      fig, ax = plt.subplots(figsize=(16, 4.8))

      sns.lineplot(
          data=df_act_filt,
          x="TIME",
          y=columna_y,
          color=color_actual,
          ax=ax,
          linewidth=1.3,
      )
      sns.lineplot(
          data=df_prop_filt,
          x="TIME",
          y=columna_y,
          color=color_propuesto,
          ax=ax,
          linewidth=1.3,
      )

      z_act = np.polyfit(df_act_filt["TIME"], df_act_filt[columna_y], 1)
      ax.plot(
          df_act_filt["TIME"],
          np.poly1d(z_act)(df_act_filt["TIME"]),
          color=color_actual,
          linestyle="--",
          linewidth=2,
      )

      z_prop = np.polyfit(df_prop_filt["TIME"], df_prop_filt[columna_y], 1)
      ax.plot(
          df_prop_filt["TIME"],
          np.poly1d(z_prop)(df_prop_filt["TIME"]),
          color=color_propuesto,
          linestyle="--",
          linewidth=2,
      )

      mediana_act = df_act_filt[columna_y].median()
      mediana_prop = df_prop_filt[columna_y].median()

      ax.text(
          0.0,
          1.15,
          f"{mediana_act:.2f} {unidad} (ACTUAL)",
          transform=ax.transAxes,
          fontsize=12,
          fontweight="bold",
          color="gray",
      )
      ax.text(
          0.0,
          1.05,
          f"{mediana_prop:.2f} {unidad} (PROPUESTO)",
          transform=ax.transAxes,
          fontsize=12,
          fontweight="bold",
          color=color_propuesto,
      )

      ax.set_xlim(x_min, x_max)

      for spine in ["top", "right", "bottom", "left"]:
        ax.spines[spine].set_visible(False)

      ax.tick_params(axis="y", length=0)
      ax.tick_params(axis="x", rotation=90)
      ax.xaxis.set_major_locator(MultipleLocator(salto_x))
      ax.yaxis.grid(True, color="plum", linestyle="--", linewidth=0.5, alpha=0.8)

      ax.set_title(titulo, fontsize=16, fontweight="bold", pad=40)
      ax.set_xlabel(
          "Tiempo (s)",
          fontsize=12,
          fontweight="bold",
          color="darkorange",
          labelpad=10,
      )
      ax.set_ylabel(ylabel, fontsize=12, fontweight="bold", color=color_y)

      leyenda_items = [
          Line2D([0], [0], color=color_actual, lw=1.5, label="ACTUAL"),
          Line2D(
              [0],
              [0],
              color=color_actual,
              lw=1.5,
              linestyle="--",
              label="Lineal (ACTUAL)",
          ),
          Line2D([0], [0], color=color_propuesto, lw=1.5, label="PROPUESTO"),
          Line2D(
              [0],
              [0],
              color=color_propuesto,
              lw=1.5,
              linestyle="--",
              label="Lineal (PROPUESTO)",
          ),
      ]
      ax.legend(
          handles=leyenda_items,
          loc="upper center",
          bbox_to_anchor=(0.5, -0.25),
          ncol=2,
          frameon=False,
          fontsize=11,
      )

      plt.tight_layout()
      st.pyplot(fig)

      img_buffer = io.BytesIO()
      fig.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
      img_buffer.seek(0)

      st.download_button(
          label=f"📥 Descargar Gráfica '{titulo}' (PNG 300 DPI)",
          data=img_buffer,
          file_name=f"grafica_{columna_y.lower()}.png",
          mime="image/png",
      )
      plt.close(fig)

    mostrar_grafica_comparativa(
        "Fuerza", "FUERZA COMPRESIVA", "Fuerza Compresiva (N)", unidad="N"
    )
    st.markdown("---")
    mostrar_grafica_comparativa(
        "Energia", "ENERGÍA CINÉTICA", "Energía (N·m)", unidad="N·m"
    )
    st.markdown("---")
    mostrar_grafica_comparativa(
        "Potencia",
        "POTENCIA TOTAL (SIMULACIÓN + NOMINAL)",
        "Potencia (MW)",
        unidad="MW",
    )

  except Exception as e:
    st.error(f"Error al procesar los archivos: {e}")

else:
  st.info(
      "👈 Sube al menos un archivo del **Modelo Actual** y uno del **Modelo"
      " Propuesto** en la barra lateral para comenzar."
  )

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.85em;'>"
    "Desarrollado por Julio Tirado — Tega Industries ©"
    "</div>",
    unsafe_allow_html=True,
)
