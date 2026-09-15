-- ---------------------------------------------------------------------------
-- gold.dim_aeroporto — dimensao de aeroporto, servindo origem E destino.
--
-- A dimensao nasce do FATO, nao do cadastro. Copiar silver.aerodromos daria
-- 496 linhas e deixaria 218 aeroportos do fato orfaos (os estrangeiros, que a
-- ANAC nao cadastra). Uma dimensao existe para servir o fato: entao a lista de
-- chaves vem do fato, e o cadastro ENRIQUECE por LEFT JOIN.
--
-- Regra de negocio que nasce aqui: a classificacao pais_aeroporto pelo prefixo
-- ICAO. Isso nao podia estar na silver — e interpretacao, nao aritmetica.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE voebem.gold.dim_aeroporto AS
WITH aeroportos_do_fato AS (
  SELECT DISTINCT icao_origem  AS icao FROM voebem.silver.vra WHERE icao_origem  IS NOT NULL AND icao_origem  <> ''
  UNION
  SELECT DISTINCT icao_destino AS icao FROM voebem.silver.vra WHERE icao_destino IS NOT NULL AND icao_destino <> ''
),
-- defesa: se a ANAC republicar o cadastro com ICAO repetido, o join
-- multiplicaria linhas do fato sem dar erro nenhum. Hoje sao 496/496.
cadastro AS (
  SELECT icao, nome, municipio, uf_nome, municipio_servido, uf_servido_nome
  FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY icao ORDER BY nome) AS rn
    FROM voebem.silver.aerodromos
    WHERE icao IS NOT NULL AND icao <> ''
  )
  WHERE rn = 1
)
SELECT
  a.icao                                                              AS icao_aeroporto,
  -- fallback textual obrigatorio: coluna que a IA vai ler nao pode vir NULL
  COALESCE(c.nome, concat('AEROPORTO FORA DO CADASTRO ANAC (', a.icao, ')'))
                                                                      AS nome_aeroporto,
  c.municipio                                                         AS municipio_aeroporto,
  c.uf_nome                                                           AS uf_aeroporto,
  CASE WHEN a.icao RLIKE '^S[BDIJNSW]' THEN 'Brasil' ELSE 'Exterior' END
                                                                      AS pais_aeroporto,
  (c.icao IS NOT NULL)                                                AS no_cadastro_anac,
  current_timestamp()                                                 AS _processado_em
FROM aeroportos_do_fato a
LEFT JOIN cadastro c ON a.icao = c.icao
