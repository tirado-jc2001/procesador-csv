import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np # Nueva librería para calcular líneas de tendencia
import io
from google.colab import files
from matplotlib.ticker import MultipleLocator

sns.set_theme(style="whitegrid")

print("1️⃣ SUBE EL ARCHIVO DEL MODELO ACTUAL:")
uploaded_actual = files.upload()
nombre_actual = list(uploaded_actual.keys())[0]

print("\n2️⃣ SUBE EL ARCHIVO DEL MODELO PROPUESTO:")
uploaded_propuesto = files.upload()
nombre_propuesto = list(uploaded_propuesto.keys())[0]

print("\n✅ Ambos archivos cargados correctamente.")

columnas = ['Fuerza', 'Energia', 'Potencia']

# 1. Calculamos estadísticas para ambos
stats_actual = df_actual[columnas].agg(['mean', 'max', 'min', 'median'])
stats_propuesto = df_propuesto[columnas].agg(['mean', 'max', 'min', 'median'])

stats_actual.index = ['promedio', 'max', 'min', 'mediana']
stats_propuesto.index = ['promedio', 'max', 'min', 'mediana']

# 2. Función para darle tu formato visual a las tablas
def aplicar_estilo(df_stats):
    return df_stats.style.format({
        'Fuerza': '{:.1f}', 'Energia': '{:.1f}', 'Potencia': '{:.2f}'
    }).apply(lambda fila: ['background-color: #92D050; color: black' if fila.name == 'mediana' else '' for _ in fila], axis=1)\
      .set_table_styles([{'selector': 'th.col_heading', 'props': [('background-color', '#0070C0'), ('color', 'white')]}])

print("--- ESTADÍSTICAS: MODELO ACTUAL ---")
display(aplicar_estilo(stats_actual))

print("\n--- ESTADÍSTICAS: MODELO PROPUESTO ---")
display(aplicar_estilo(stats_propuesto))

# 3. Comparativa porcentual de Medianas
mediana_actual = stats_actual.loc['mediana']
mediana_propuesta = stats_propuesto.loc['mediana']
variacion_pct = ((mediana_propuesta - mediana_actual) / mediana_actual) * 100

tabla_comparativa = pd.DataFrame({
    'Mediana Actual': mediana_actual,
    'Mediana Propuesta': mediana_propuesta,
    'Variación (%)': variacion_pct
})

print("\n--- COMPARATIVA DE MEDIANAS ---")
display(tabla_comparativa.style.format({
    'Mediana Actual': '{:.2f}',
    'Mediana Propuesta': '{:.2f}',
    'Variación (%)': '{:+.2f}%'
}).set_table_styles([{'selector': 'th.col_heading', 'props': [('background-color', '#444444'), ('color', 'white')]}]))
# ==============================================================================
# CELDA 5: GRÁFICAS COMPARATIVAS CON RANGO DE TIEMPO INTERACTIVO
# ==============================================================================
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MultipleLocator
from matplotlib.lines import Line2D

sns.set_style("white")

# ==========================================
# 1. RANGO DE TIEMPO INTERACTIVO
# ==========================================
print("--- CONFIGURACIÓN DE LA GRÁFICA ---")
try:
    x_min = float(input("Ingrese el segundo de INICIO para la gráfica: "))
    x_max = float(input("Ingrese el segundo FINAL para la gráfica: "))
except ValueError:
    print("⚠️ Valor no válido. Se usará el rango por defecto de 8 a 10.")
    x_min = 8.0
    x_max = 10.0

# Se ajusta el salto en X automáticamente dependiendo de qué tan grande sea el rango
salto_x = 0.20 if (x_max - x_min) <= 3 else 0.50

color_actual = "darkgray"
color_propuesto = "#00A2E8"

# ==========================================
# 2. FUNCIÓN DE GRÁFICA
# ==========================================
def graficar_comparativa_limpia(columna_y, titulo, ylabel, unidad='', color_y='darkorange', y_min=None):
    fig, ax = plt.subplots(figsize=(18, 5.5))

    # Filtramos los datos AL RANGO ELEGIDO
    df_act_filt = df_actual[(df_actual['TIME'] >= x_min) & (df_actual['TIME'] <= x_max)]
    df_prop_filt = df_propuesto[(df_propuesto['TIME'] >= x_min) & (df_propuesto['TIME'] <= x_max)]

    if df_act_filt.empty or df_prop_filt.empty:
        print(f"⚠️ No hay datos entre {x_min}s y {x_max}s para {columna_y}.")
        plt.close()
        return

    # Graficar curvas de datos reales
    sns.lineplot(data=df_act_filt, x='TIME', y=columna_y, color=color_actual, ax=ax, linewidth=1.2)
    sns.lineplot(data=df_prop_filt, x='TIME', y=columna_y, color=color_propuesto, ax=ax, linewidth=1.2)

    # Calcular y graficar Líneas de Tendencia
    z_act = np.polyfit(df_act_filt['TIME'], df_act_filt[columna_y], 1)
    p_act = np.poly1d(z_act)
    ax.plot(df_act_filt['TIME'], p_act(df_act_filt['TIME']), color=color_actual, linestyle='--', linewidth=2)

    z_prop = np.polyfit(df_prop_filt['TIME'], df_prop_filt[columna_y], 1)
    p_prop = np.poly1d(z_prop)
    ax.plot(df_prop_filt['TIME'], p_prop(df_prop_filt['TIME']), color=color_propuesto, linestyle='--', linewidth=2)

    # Insertar valores de la Mediana
    mediana_act = df_act_filt[columna_y].median()
    mediana_prop = df_prop_filt[columna_y].median()

    ax.text(0.0, 1.15, f"{mediana_act:.2f} {unidad} (ACTUAL)", transform=ax.transAxes,
            fontsize=12, fontweight='bold', color='gray')
    ax.text(0.0, 1.05, f"{mediana_prop:.2f} {unidad} (Tega)", transform=ax.transAxes,
            fontsize=12, fontweight='bold', color=color_propuesto)

    # Estética y Formato
    ax.set_xlim(x_min, x_max)
    if y_min is not None:
        ax.set_ylim(bottom=y_min)
        ax.axhline(y=y_min, color='lightskyblue', linestyle='--', linewidth=1, alpha=0.8)

    for spine in ['top', 'right', 'bottom', 'left']:
        ax.spines[spine].set_visible(False)

    ax.tick_params(axis='y', length=0)
    ax.tick_params(axis='x', rotation=90)
    ax.xaxis.set_major_locator(MultipleLocator(salto_x))
    ax.yaxis.grid(True, color='plum', linestyle='--', linewidth=0.5, alpha=0.8)

    # Títulos y Etiquetas
    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=40)
    ax.set_xlabel('Tiempo (s)', fontsize=12, fontweight='bold', color='darkorange', labelpad=10)
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold', color=color_y)

    # Leyenda Inferior
    leyenda_items = [
        Line2D([0], [0], color=color_actual, lw=1.5, label='ACTUAL'),
        Line2D([0], [0], color=color_actual, lw=1.5, linestyle='--', label='Lineal (ACTUAL)'),
        Line2D([0], [0], color=color_propuesto, lw=1.5, label='Valor propuesto (TEGA)'),
        Line2D([0], [0], color=color_propuesto, lw=1.5, linestyle='--', label='Lineal (Valor propuesto)')
    ]
    ax.legend(handles=leyenda_items, loc='upper center', bbox_to_anchor=(0.5, -0.25),
              ncol=2, frameon=False, fontsize=11)

    plt.tight_layout()
    plt.show()

# ==============================================================================
# EJECUCIÓN
# ==============================================================================
graficar_comparativa_limpia('Fuerza', 'FUERZA COMPRESIVA', 'Fuerza Compresiva (N)', unidad='N', y_min=4000)
graficar_comparativa_limpia('Energia', 'ENERGÍA CINÉTICA', 'Energía (J)', unidad='J')
graficar_comparativa_limpia('Potencia', 'POTENCIA CONSUMIDA', 'Potencia (MW)', unidad='MW')
