-- P5 — Quanto atraso as companhias recuperam em voo? (>= 10.000 voos)
SELECT
  nome_companhia,
  COUNT(*)                                                                   AS voos,
  ROUND(AVG(atraso_partida_min), 2)                                          AS atraso_saida_min,
  ROUND(AVG(atraso_chegada_min), 2)                                          AS atraso_chegada_min,
  ROUND(AVG(minutos_recuperados), 2)                                         AS recuperados_medio_min
FROM voebem.gold.obt_voos
WHERE minutos_recuperados IS NOT NULL
GROUP BY 1
HAVING COUNT(*) >= 10000
ORDER BY recuperados_medio_min DESC
