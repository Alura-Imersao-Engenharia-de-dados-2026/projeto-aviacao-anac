-- P4b — E em quais aeroportos brasileiros a diferenca internacional x domestico e maior?
SELECT
  nome_aeroporto_origem,
  municipio_origem,
  SUM(CASE WHEN escopo_voo = 'Domestico'     THEN 1 ELSE 0 END)              AS voos_domesticos,
  SUM(CASE WHEN escopo_voo = 'Internacional' THEN 1 ELSE 0 END)              AS voos_internacionais,
  ROUND(AVG(CASE WHEN escopo_voo = 'Domestico'     THEN atraso_partida_min END), 2) AS atraso_domestico,
  ROUND(AVG(CASE WHEN escopo_voo = 'Internacional' THEN atraso_partida_min END), 2) AS atraso_internacional,
  ROUND(AVG(CASE WHEN escopo_voo = 'Internacional' THEN atraso_partida_min END)
      - AVG(CASE WHEN escopo_voo = 'Domestico'     THEN atraso_partida_min END), 2) AS diferenca_min
FROM voebem.gold.obt_voos
WHERE pais_origem = 'Brasil'
GROUP BY 1, 2
HAVING SUM(CASE WHEN escopo_voo = 'Internacional' THEN 1 ELSE 0 END) >= 2000
   AND SUM(CASE WHEN escopo_voo = 'Domestico'     THEN 1 ELSE 0 END) >= 2000
ORDER BY diferenca_min DESC
LIMIT 10
