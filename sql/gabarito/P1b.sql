-- P1b — as piores ROTAS domesticas por atraso de partida (>= 2.000 voos).
SELECT
  rota_municipios,
  rota_icao,
  COUNT(*)                                                                   AS voos,
  ROUND(AVG(atraso_partida_min), 2)                                          AS atraso_medio_min,
  ROUND(100.0 * try_divide(SUM(CASE WHEN partida_pontual = false THEN 1 ELSE 0 END),
                           SUM(CASE WHEN partida_pontual IS NOT NULL THEN 1 ELSE 0 END)), 2) AS pct_atrasados
FROM voebem.gold.obt_voos
WHERE escopo_voo = 'Domestico'
GROUP BY 1, 2
HAVING COUNT(*) >= 2000
ORDER BY atraso_medio_min DESC
LIMIT 10
