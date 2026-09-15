-- P3 — Companhia: pontualidade x cancelamento, controlando por porte (>= 10.000 voos).
SELECT
  nome_companhia,
  COUNT(*)                                                                   AS voos,
  ROUND(100.0 * SUM(CASE WHEN voo_cancelado THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_cancelados,
  ROUND(100.0 * try_divide(SUM(CASE WHEN partida_pontual = true THEN 1 ELSE 0 END),
                           SUM(CASE WHEN partida_pontual IS NOT NULL THEN 1 ELSE 0 END)), 2) AS pct_pontuais,
  ROUND(AVG(atraso_partida_min), 2)                                          AS atraso_medio_min
FROM voebem.gold.obt_voos
GROUP BY 1
HAVING COUNT(*) >= 10000
ORDER BY pct_pontuais DESC
