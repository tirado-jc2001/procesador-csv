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
    "Sube tus archivos CSV correspondientes, configura los offsets de potencia,"
    " rangos y colores para generar las estadísticas y gráficas en alta"
    " calidad."
)

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
  st.markdown("---")
  st.subheader("⚙️ Configuración de Offsets de Potencia")

  # Solicitamos los valores de MW para ambos modelos de forma interactiva en la web
  col_off1, col_off2 = st.columns(2)
  with col_off1:
    potencia_add_actual = st.number_input(
        "Ingrese la potencia (MW) a sumar para el modelo ACTUAL:",
        value=0.0,
        step=0.1,
        format="%.2f",
    )
  with col_off2:
    potencia_add_propuesto = st.number_input(
        "Ingrese la potencia (MW) a sumar para el modelo PROPUESTO:",
        value=0.0,
        step=0.1,
        format="%.2f",
    )


  # Función ultra-robusta adaptada para recibir los archivos subidos en Streamlit
  def limpiar_y_transformar(uploaded_file, offset_potencia):
    """Función ultra-robusta: Encuentra los encabezados y columnas mediante

    palabras clave, sin importar cómo el software decida nombrar la variable
    (Q01, CF, KE, etc.)
    """
    texto_archivo = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    lineas = texto_archivo.splitlines()

    # Buscar dinámicamente en qué línea está el encabezado "TIME"
    fila_encabezado = 0
    for i, linea in enumerate(lineas):
      if "TIME" in linea.upper():
        fila_encabezado = i
        break

    df = pd.read_csv(io.StringIO(texto_archivo), skiprows=fila_encabezado)
    df.columns = df.columns.str.strip()

    # Encontrar las columnas buscando palabras clave que nunca cambian
    col_potencia = [col for col in df.columns if "Power" in col][0]
    col_energia = [col for col in df.columns if "Kinetic" in col][0]
    col_fuerza = [col for col in df.columns if "Compressive" in col][0]

    # Aplicar la fórmula matemática
    df["Potencia"] = (df[col_potencia] * -1 / 1_000_000) + offset_potencia

    # Renombrar las columnas encontradas
    df = df.rename(columns={col_energia: "Energia", col_fuerza: "Fuerza"})

    # Asegurar que la columna de tiempo se llame TIME en mayúsculas
    if "TIME" not in df.columns and "Time" in df.columns:
      df = df.rename(columns={"Time": "TIME"})

    return df[["TIME", "Fuerza", "Energia", "Potencia"]]


  try:
    # Procesamos ambos archivos usando tu lógica exacta
    df_actual = limpiar_y_transformar(archivo_actual, potencia_add_actual)
    df_propuesto = limpiar_y_transformar(
        archivo_propuesto, potencia_add_propuesto
    )

    st.success(
        "✅ Datos de ambos modelos limpiados y transformados exitosamente."
        " Listos para las gráficas."
    )

    columnas_stats = ["Fuerza", "Energia", "Potencia"]

    # ==========================================
    # 2. CÁLCULO DE ESTADÍSTICAS Y TABLAS
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
    st.subheader("📈 Estadísticas y Comparativa de Modelos")

    tab1, tab2, tab3 = st.tabs(
        ["Modelo Actual", "Modelo Propuesto", "Comparativa de Medianas"]
    )

    with tab1:
      st.write("### Estadísticas: MODELO ACTUAL")
      st.dataframe(stats_actual.style.format("{:.2f}"), use_container_width=True)

    with tab2:
      st.write("### Estadísticas: MODELO PROPUESTO")
      st.dataframe(
          stats_propuesto.style.format("{:.2f}"), use_container_width=True
      )

    with tab3:
      mediana_actual = stats_actual.loc["mediana"]
      mediana_propuesta = stats_propuesto.loc["mediana"]
      variacion_pct = ((mediana_propuesta - mediana_actual) / mediana_actual) * 100

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
    # 3. CONTROLES DE RANGO DE TIEMPO Y COLORES
    # ==========================================
    st.markdown("---")
    st.subheader("⏱️ Configuración de Visualización y Gráficas")

    col_cfg1, col_cfg2, col_cfg3, col_cfg4 = st.columns(4)

    with col_cfg1:
      x_min = st.number_input(
          "Segundo INICIO", value=8.0, step=0.1, format="%.2f"
      )
    with col_cfg2:
      x_max = st.number_input(
          "Segundo FINAL", value=10.0, step=0.1, format="%.2f"
      )
    with col_cfg3:
      color_actual = st.color_picker("Color Modelo Actual", value="#A9A9A9")
    with col_cfg4:
      color_propuesto = st.color_picker(
          "Color Modelo Propuesto (Tega)", value="#00A2E8"
      )

    salto_x = 0.20 if (x_max - x_min) <= 3 else 0.50
    sns.set_style("white")


    # ==========================================
    # 4. FUNCIÓN DE GRÁFICA COMPARATIVA
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

      # Curvas de datos reales
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

      # Líneas de Tendencia
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

      # Medianas
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

      # Descarga en PNG a 300 DPI
      img_buffer = io.BytesIO()
      fig.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
      img_buffer.seek(0)

      st.download_button(
          label=f"📥 Descargar Gráfica '{titulo}' en Alta Calidad (PNG 300 DPI)",
          data=img_buffer,
          file_name=f"grafica_{columna_y.lower()}.png",
          mime="image/png",
      )
      plt.close(fig)


    # ==========================================
    # 5. RENDERIZAR LAS GRÁFICAS
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
