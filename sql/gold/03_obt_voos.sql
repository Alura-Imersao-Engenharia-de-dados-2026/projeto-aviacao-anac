-- ---------------------------------------------------------------------------
-- gold.obt_voos — One Big Table, desenhada para um consumidor especifico: uma IA.
--
-- Uma linha por etapa de voo, com TUDO resolvido: nome de companhia, nome de
-- aeroporto de origem e destino com municipio e UF, tipo de linha por extenso,
-- escopo, pontualidade e as metricas de atraso prontas.
--
-- Regra de ouro desta tabela: nenhuma coluna de codigo sem a coluna de
-- descricao correspondente ao lado. O LLM le nome, nao codigo ICAO.
--
-- E o unico join que ela exige de quem consome: nenhum.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE voebem.gold.obt_voos AS
SELECT
  -- ===== companhia =====
  f.icao_empresa,
  f.nome_companhia,
  f.numero_voo,

  -- ===== operacao =====
  f.codigo_di,
  f.descricao_di,
  f.codigo_tipo_linha,
  f.descricao_tipo_linha,
  f.escopo_voo,

  -- ===== origem =====
  f.icao_origem,
  o.nome_aeroporto        AS nome_aeroporto_origem,
  o.municipio_aeroporto   AS municipio_origem,
  o.uf_aeroporto          AS uf_origem,
  o.pais_aeroporto        AS pais_origem,

  -- ===== destino =====
  f.icao_destino,
  d.nome_aeroporto        AS nome_aeroporto_destino,
  d.municipio_aeroporto   AS municipio_destino,
  d.uf_aeroporto          AS uf_destino,
  d.pais_aeroporto        AS pais_destino,

  -- ===== rota, em codigo e por extenso =====
  f.rota                                                            AS rota_icao,
  concat(coalesce(o.municipio_aeroporto, f.icao_origem),  ' - ',
         coalesce(d.municipio_aeroporto, f.icao_destino))           AS rota_municipios,

  -- ===== tempo =====
  f.partida_prevista,
  f.partida_prevista_data,
  f.partida_prevista_hora,
  f.hora_partida_prevista,
  f.dia_semana,
  f.mes_referencia,
  f.partida_real,
  f.chegada_prevista,
  f.chegada_real,

  -- ===== metricas =====
  f.atraso_partida_min,
  f.atraso_chegada_min,
  f.minutos_recuperados,
  f.atraso_fora_de_faixa,
  f.partida_pontual,
  f.chegada_pontual,

  -- ===== situacao =====
  f.situacao_voo,
  f.voo_realizado,
  f.voo_cancelado,

  f._processado_em
FROM voebem.gold.fato_voos f
LEFT JOIN voebem.gold.dim_aeroporto o ON f.icao_origem  = o.icao_aeroporto
LEFT JOIN voebem.gold.dim_aeroporto d ON f.icao_destino = d.icao_aeroporto
