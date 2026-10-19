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
    page_title="Comparativa de Modelos - Tega", page_icon="📊", layout="wide"
)

st.title("🚀 Analizador y Comparador de Modelos (Actual vs Propuesto)")
st.write(
    "Sube tus archivos CSV correspondientes para generar las estadísticas y"
    " gráficas comparativas en alta calidad."
)


# Función para cargar CSV de EDEM/Ansys y mapear nombres de columnas automáticamente
def cargar_y_mapear_csv(file_bytes):
  content = file_bytes.getvalue().decode("utf-8", errors="ignore").splitlines()

  # 1. Encontrar la línea del encabezado
  header_line = 0
  for i, line in enumerate(content[:60]):
    if ("TIME" in line or "Time" in line) and (
        "Compressive" in line
        or "Kinetic" in line
        or "Power" in line
        or "CF" in line
        or "Fuerza" in line
    ):
      header_line = i
      break

  file_bytes.seek(0)
  df = pd.read_csv(
      file_bytes, skiprows=header_line, sep=None, engine="python", on_bad_lines="skip"
  )
  df.columns = df.columns.str.strip()

  # 2. Mapeo inteligente de nombres de columnas
  mapping = {}
  for col in df.columns:
    col_upper = col.upper()
    if "TIME" in col_upper:
      mapping[col] = "TIME"
    elif (
        "CF" in col_upper
        or "COMPRESSIVE" in col_upper
        or "FUERZA" in col_upper
        or "FORCE" in col_upper
    ):
      mapping[col] = "Fuerza"
    elif (
        "KE" in col_upper
        or "KINETIC" in col_upper
        or "ENERGIA" in col_upper
        or "ENERGY" in col_upper
    ):
      mapping[col] = "Energia"
    elif (
        "Q01" in col_upper
        or "POWER" in col_upper
        or "POTENCIA" in col_upper
        or "GEOMETRY" in col_upper
    ):
      mapping[col] = "Potencia"

  df.rename(columns=mapping, inplace=True)
  return df


# ==========================================
# 1. SUBIDA DE ARCHIVOS EN STREAMLIT
# ==========================================
col_up1, col_up2 = st.columns(2)

with col_up1:
  st.subheader("1️⃣ Modelo Actual")
  archivo_actual = st.file_uploader(
      "Sube el CSV del Modelo Actual", type=["csv"], key="actual"
  )

with col_up2:
  st.subheader("2️⃣ Modelo Propuesto")
  archivo_propuesto = st.file_uploader(
      "Sube el CSV del Modelo Propuesto", type=["csv"], key="propuesto"
  )

if archivo_actual is not None and archivo_propuesto is not None:
  try:
    df_actual = cargar_y_mapear_csv(archivo_actual)
    df_propuesto = cargar_y_mapear_csv(archivo_propuesto)

    columnas_requeridas = ["TIME", "Fuerza", "Energia", "Potencia"]

    # Validar que se hayan mapeado todas las columnas correctamente
    faltantes_act = [
        c for c in columnas_requeridas if c not in df_actual.columns
    ]
    faltantes_prop = [
        c for c in columnas_requeridas if c not in df_propuesto.columns
    ]

    if faltantes_act or faltantes_prop:
      st.error(
          f"⚠️ No se pudieron identificar todas las columnas requeridas.\n\n"
          f"Columnas halladas en Actual: {list(df_actual.columns)}\n\n"
          f"Columnas halladas en Propuesto: {list(df_propuesto.columns)}"
      )
    else:
      st.success("¡Ambos archivos cargados y procesados correctamente!")

      # Convertir a numérico por seguridad
      for col in columnas_requeridas:
        df_actual[col] = pd.to_numeric(df_actual[col], errors="coerce")
        df_propuesto[col] = pd.to_numeric(df_propuesto[col], errors="coerce")

      columnas_stats = ["Fuerza", "Energia", "Potencia"]

      # ==========================================
      # 2. CÁLCULO DE ESTADÍSTICAS
      # ==========================================
      stats_actual = df_actual[columnas_stats].agg(
          ["mean", "max", "min", "median"]
      )
      stats_propuesto = df_propuesto[columnas_stats].agg(
          ["mean", "max", "min", "median"]
      )

      stats_actual.index = ["promedio", "max", "min", "mediana"]
      stats_propuesto.index = ["promedio", "max", "min", "mediana"]

      st.markdown("---")
      st.subheader("📈 Estadísticas y Comparativa")

      tab1, tab2, tab3 = st.tabs(
          ["Modelo Actual", "Modelo Propuesto", "Comparativa de Medianas"]
      )

      with tab1:
        st.write("### Estadísticas: MODELO ACTUAL")
        st.dataframe(
            stats_actual.style.format("{:.2f}"), use_container_width=True
        )

      with tab2:
        st.write("### Estadísticas: MODELO PROPUESTO")
        st.dataframe(
            stats_propuesto.style.format("{:.2f}"), use_container_width=True
        )

      with tab3:
        mediana_actual = stats_actual.loc["mediana"]
        mediana_propuesta = stats_propuesto.loc["mediana"]
        variacion_pct = (
            (mediana_propuesta - mediana_actual) / mediana_actual
        ) * 100

        tabla_comparativa = pd.DataFrame({
            "Mediana Actual": mediana_actual,
            "Mediana Propuesta": mediana_propuesta,
            "Variación (%)": variacion_pct,
        })
        st.write("### Comparativa de Medianas")
        st.dataframe(
            tabla_comparativa.style.format({
                "Mediana Actual": "{:.2f}",
                "Mediana Propuesta": "{:.2f}",
                "Variación (%)": "{:+.2f}%",
            }),
            use_container_width=True,
        )

      # ==========================================
      # 3. RANGO DE TIEMPO INTERACTIVO
      # ==========================================
      st.markdown("---")
      st.subheader("⏱️ Configuración del Rango de Tiempo para las Gráficas")

      c_min, c_max = st.columns(2)
      with c_min:
        x_min = st.number_input(
            "Segundo de INICIO", value=8.0, step=0.1, format="%.2f"
        )
      with c_max:
        x_max = st.number_input(
            "Segundo FINAL", value=10.0, step=0.1, format="%.2f"
        )

      salto_x = 0.20 if (x_max - x_min) <= 3 else 0.50
      color_actual = "darkgray"
      color_propuesto = "#00A2E8"

      sns.set_style("white")

      # ==========================================
      # 4. FUNCIÓN DE GRÁFICA
      # ==========================================
      def mostrar_grafica_comparativa(
          columna_y, titulo, ylabel, unidad="", color_y="darkorange", y_min=None
      ):
        fig, ax = plt.subplots(figsize=(16, 5))

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

        # Curvas reales
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

        # Tendencias
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
              y=y_min,
              color="lightskyblue",
              linestyle="--",
              linewidth=1,
              alpha=0.8,
          )

        for spine in ["top", "right", "bottom", "left"]:
          ax.spines[spine].set_visible(False)

        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", rotation=90)
        ax.xaxis.set_major_locator(MultipleLocator(salto_x))
        ax.yaxis.grid(
            True, color="plum", linestyle="--", linewidth=0.5, alpha=0.8
        )

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

        # Descarga a 300 DPI
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
        img_buffer.seek(0)

        st.download_button(
            label=(
                f"📥 Descargar Gráfica '{titulo}' en Alta Calidad (PNG 300 DPI)"
            ),
            data=img_buffer,
            file_name=f"grafica_{columna_y.lower()}.png",
            mime="image/png",
        )
        plt.close(fig)

      # ==========================================
      # 5. RENDERIZAR GRÁFICAS
      # ==========================================
      st.markdown("---")
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
      "👆 Por favor, sube ambos archivos CSV en la parte superior para comenzar"
      " el análisis."
  )
