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
      "Potencia Nominal

