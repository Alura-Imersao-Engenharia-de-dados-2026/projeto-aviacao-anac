-- ---------------------------------------------------------------------------
-- Passo 1 — marcar cada voo com o resultado dos testes de integridade.
--
-- Expectation NAO aceita subquery. E integridade referencial e, por definicao,
-- "existe na outra tabela?" — ou seja, uma subquery. A saida e resolver o join
-- AQUI, com LEFT JOIN + flag booleana, e deixar a expectation olhando so a flag.
--
-- Temporary view: e logica intermediaria do pipeline, nao dado publicado.
--
-- Repare no que NAO tem aqui: nenhuma classificacao. A versao anterior deste
-- arquivo criava escopo_origem/escopo_destino ('nacional'/'estrangeiro') pelo
-- prefixo ICAO. Isso e classificacao de negocio e o lugar dela e a gold.
-- Aqui so existe fato verificavel: o codigo esta ou nao esta no cadastro.
-- ---------------------------------------------------------------------------
CREATE TEMPORARY VIEW vra_marcado AS
WITH aerodromo AS (
  SELECT DISTINCT icao FROM voebem.silver.aerodromos
  WHERE icao IS NOT NULL AND icao <> ''
),
empresa AS (
  SELECT DISTINCT icao FROM voebem.silver.empresas
  WHERE icao IS NOT NULL AND icao <> ''
)
SELECT
  v.*,
  (ao.icao IS NOT NULL) AS origem_no_cadastro,
  (ad.icao IS NOT NULL) AS destino_no_cadastro,
  (em.icao IS NOT NULL) AS empresa_no_cadastro
FROM voebem.silver.vra v
LEFT JOIN aerodromo ao ON v.icao_origem  = ao.icao
LEFT JOIN aerodromo ad ON v.icao_destino = ad.icao
LEFT JOIN empresa   em ON v.icao_empresa = em.icao;
