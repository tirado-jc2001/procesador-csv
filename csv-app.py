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
    page_title="Comparativa de Modelos - Tega Industries",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
#  BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
  # 1. Logo de la Empresa (si subes 'logo.png' a GitHub úsalo aquí)
  try:
    st.image(
        "https://tegaindustries.hiringroom.com/data/accounts/tegaindustries/profile.jpg?version=", use_container_width=True
    )  # O cambia 'logo.png' por una URL directa si prefieres
  except Exception:
    st.title("🏢 TEGA INDUSTRIES")

  st.markdown("---")
  st.header("📂 Carga de Archivos")

  archivo_actual = st.file_uploader(
      "1️⃣ Modelo Actual (CSV)", type=["csv"], key="actual"
  )
  archivo_propuesto = st.file_uploader(
      "2️⃣ Modelo Propuesto (CSV)", type=["csv"], key="propuesto"
  )

  st.markdown("---")
  st.header("⚙️ Offsets de Potencia")
  potencia_add_actual = st.number_input(
      "Potencia a sumar ACTUAL (MW):", value=0.0, step=0.1, format="%.2f"
  )
  potencia_add_propuesto = st.number_input(
      "Potencia a sumar PROPUESTO (MW):", value=0.0, step=0.1, format="%.2f"
  )

  st.markdown("---")
  st.header("🎨 Estilo y Rango")
  col_s1, col_s2 = st.columns(2)
  with col_s1:
    x_min = st.number_input(
        "Segundo INICIO", value=8.0, step=0.1, format="%.2f"
    )
  with col_s2:
    x_max = st.number_input(
        "Segundo FINAL", value=10.0, step=0.1, format="%.2f"
    )

  color_actual = st.color_picker(
      "Color Modelo Actual", value="#A9A9A9"
  )  # Gris
  color_propuesto = st.color_picker(
      "Color Modelo Propuesto", value="#00A2E8"
  )  # Azul TEGA

  # Firma discreta al final de la barra lateral
  st.markdown("---")
  st.caption(" **Desarrollado por:** Julio Tirado")
  st.caption(" *Intern PMG Mill*")


# ==========================================
# PANTALLA PRINCIPAL
# ==========================================
st.title("🚀 Panel de Análisis y Comparación de Modelos DEM")
st.write(
    "Plataforma interactiva para la evaluación de parámetros de simulación"
    " (Fuerza, Energía y Potencia)."
)


# Función de limpieza y transformación
def limpiar_y_transformar(uploaded_file, offset_potencia):
  texto_archivo = uploaded_file.getvalue().decode("utf-8", errors="ignore")
  lineas = texto_archivo.splitlines()

  fila_encabezado = 0
  for i, linea in enumerate(lineas):
    if "TIME" in linea.upper():
      fila_encabezado = i
      break

  df = pd.read_csv(io.StringIO(texto_archivo), skiprows=fila_encabezado)
  df.columns = df.columns.str.strip()

  col_potencia = [col for col in df.columns if "Power" in col][0]
  col_energia = [col for col in df.columns if "Kinetic" in col][0]
  col_fuerza = [col for col in df.columns if "Compressive" in col][0]

  df["Potencia"] = (df[col_potencia] * -1 / 1_000_000) + offset_potencia
  df = df.rename(columns={col_energia: "Energia", col_fuerza: "Fuerza"})

  if "TIME" not in df.columns and "Time" in df.columns:
    df = df.rename(columns={"Time": "TIME"})

  return df[["TIME", "Fuerza", "Energia", "Potencia"]]


if archivo_actual is not None and archivo_propuesto is not None:
  try:
    df_actual = limpiar_y_transformar(archivo_actual, potencia_add_actual)
    df_propuesto = limpiar_y_transformar(
        archivo_propuesto, potencia_add_propuesto
    )

    columnas_stats = ["Fuerza", "Energia", "Potencia"]

    # Tarjetas Métricas Rápidas (Resumen Visual)
    st.markdown("### 📊 Resumen Ejecutivo (Medianas)")
    m_act = df_actual[columnas_stats].median()
    m_prop = df_propuesto[columnas_stats].median()
    v_pct = ((m_prop - m_act) / m_act) * 100

    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Fuerza Compresiva", f"{m_prop['Fuerza']:.1f} N", f"{v_pct['Fuerza']:+.2f}%")
    c_m2.metric("Energía Cinética", f"{m_prop['Energia']:.1f} J", f"{v_pct['Energia']:+.2f}%")
    c_m3.metric("Potencia Consumida", f"{m_prop['Potencia']:.2f} MW", f"{v_pct['Potencia']:+.2f}%")

    st.markdown("---")

    # Tablas Estadísticas Organizadas
    st.subheader("📈 Estadísticas Detalladas")
    stats_actual = df_actual[columnas_stats].agg(
        ["mean", "max", "min", "median"]
    )
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

    # Gráficas
    st.markdown("---")
    st.subheader("📉 Gráficas Comparativas de Desempeño")

    salto_x = 0.20 if (x_max - x_min) <= 3 else 0.50
    sns.set_style("white")

    def mostrar_grafica_comparativa(
        columna_y, titulo, ylabel, unidad="", color_y="darkorange", y_min=None
    ):
      fig, ax = plt.subplots(figsize=(16, 4.8))

      df_act_filt = df_actual[
          (df_actual["TIME"] >= x_min) & (df_actual["TIME"] <= x_max)
      ].dropna(subset=["TIME", columna_y])
      df_prop_filt = df_propuesto[
          (df_propuesto["TIME"] >= x_min) & (df_propuesto["TIME"] <= x_max)
      ].dropna(subset=["TIME", columna_y])

      if df_act_filt.empty or df_prop_filt.empty:
        st.warning(
            f"⚠️ No hay datos suficientes entre {x_min}s y {x_max}s para"
            f" {columna_y}."
        )
        plt.close(fig)
        return

      sns.lineplot(
          data=df_act_filt,
          x="TIME",
          y=columna_y,
          color=color_actual,
          ax=ax,
          linewidth=1.2,
      )
      sns.lineplot(
          data=df_prop_filt,
          x="TIME",
          y=columna_y,
          color=color_propuesto,
          ax=ax,
          linewidth=1.2,
      )

      z_act = np.polyfit(df_act_filt["TIME"], df_act_filt[columna_y], 1)
      p_act = np.poly1d(z_act)
      ax.plot(
          df_act_filt["TIME"],
          p_act(df_act_filt["TIME"]),
          color=color_actual,
          linestyle="--",
          linewidth=2,
      )

      z_prop = np.polyfit(df_prop_filt["TIME"], df_prop_filt[columna_y], 1)
      p_prop = np.poly1d(z_prop)
      ax.plot(
          df_prop_filt["TIME"],
          p_prop(df_prop_filt["TIME"]),
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
          f"{mediana_prop:.2f} {unidad} (Tega)",
          transform=ax.transAxes,
          fontsize=12,
          fontweight="bold",
          color=color_propuesto,
      )

      ax.set_xlim(x_min, x_max)
      if y_min is not None:
        ax.set_ylim(bottom=y_min)
        ax.axhline(
            y=y_min, color="lightskyblue", linestyle="--", linewidth=1, alpha=0.8
        )

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
          Line2D(
              [0],
              [0],
              color=color_propuesto,
              lw=1.5,
              label="Valor propuesto (TEGA)",
          ),
          Line2D(
              [0],
              [0],
              color=color_propuesto,
              lw=1.5,
              linestyle="--",
              label="Lineal (Valor propuesto)",
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
        "Fuerza",
        "FUERZA COMPRESIVA",
        "Fuerza Compresiva (N)",
        unidad="N",
        y_min=4000,
    )
    st.markdown("---")
    mostrar_grafica_comparativa(
        "Energia", "ENERGÍA CINÉTICA", "Energía (J)", unidad="J"
    )
    st.markdown("---")
    mostrar_grafica_comparativa(
        "Potencia", "POTENCIA CONSUMIDA", "Potencia (MW)", unidad="MW"
    )

  except Exception as e:
    st.error(f"Error al procesar los archivos: {e}")

else:
  st.info(
      "👈 Por favor, sube ambos archivos CSV en la barra lateral para iniciar"
      " el análisis."
  )

# Pie de página sutil en la pantalla principal
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.85em;'>"
    "Desarrollado por Julio Tirado — Tega Industries ©"
    "</div>",
    unsafe_allow_html=True,
)
