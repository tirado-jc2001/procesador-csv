def recortar_a_ventana_comun(df_act, df_prop):
  """Recorta ambos DataFrames al intervalo de tiempo donde ambos tienen datos."""
  if df_act is None or df_prop is None or df_act.empty or df_prop.empty:
    return df_act, df_prop, None, None

  t_inicio = max(df_act["TIME"].min(), df_prop["TIME"].min())
  t_fin = min(df_act["TIME"].max(), df_prop["TIME"].max())

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


