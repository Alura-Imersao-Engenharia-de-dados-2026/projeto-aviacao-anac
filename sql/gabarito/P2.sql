-- P2 — Como o atraso evolui ao longo do dia (efeito cascata).
SELECT
  hora_partida_prevista                                                      AS hora,
  COUNT(*)                                                                   AS voos,
  ROUND(AVG(atraso_partida_min), 2)                                          AS atraso_medio_min,
  ROUND(100.0 * try_divide(SUM(CASE WHEN partida_pontual = false THEN 1 ELSE 0 END),
                           SUM(CASE WHEN partida_pontual IS NOT NULL THEN 1 ELSE 0 END)), 2) AS pct_atrasados
FROM voebem.gold.obt_voos
WHERE hora_partida_prevista IS NOT NULL
GROUP BY 1
ORDER BY 1
