-- P5b — Em que rotas a recuperacao NAO acontece (perde tempo no ar)? (>= 2.000 voos)
SELECT
  rota_municipios,
  rota_icao,
  COUNT(*)                                                                   AS voos,
  ROUND(AVG(atraso_partida_min), 2)                                          AS atraso_saida_min,
  ROUND(AVG(atraso_chegada_min), 2)                                          AS atraso_chegada_min,
  ROUND(AVG(minutos_recuperados), 2)                                         AS recuperados_medio_min
FROM voebem.gold.obt_voos
WHERE minutos_recuperados IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(*) >= 2000
ORDER BY recuperados_medio_min ASC
LIMIT 10
