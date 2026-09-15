-- P1 — Quais rotas e aeroportos concentram os maiores atrasos de partida no Brasil?
-- Recorte: aeroportos de origem no Brasil, com volume relevante (>= 5.000 voos).
SELECT
  nome_aeroporto_origem,
  municipio_origem,
  uf_origem,
  COUNT(*)                                                                   AS voos,
  ROUND(AVG(atraso_partida_min), 2)                                          AS atraso_medio_min,
  ROUND(100.0 * try_divide(SUM(CASE WHEN partida_pontual = false THEN 1 ELSE 0 END),
                           SUM(CASE WHEN partida_pontual IS NOT NULL THEN 1 ELSE 0 END)), 2) AS pct_atrasados
FROM voebem.gold.obt_voos
WHERE pais_origem = 'Brasil'
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 5000
ORDER BY pct_atrasados DESC
LIMIT 10
