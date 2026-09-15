-- ---------------------------------------------------------------------------
-- gold.fato_voos — uma linha por etapa de voo.
--
-- E AQUI que nascem as regras de negocio que a silver nao podia ter:
--
--   1. PONTUALIDADE a 15 minutos (partida_pontual / chegada_pontual).
--      O numero 15 e decisao de cliente. Na silver ele fecharia porta;
--      aqui e uma linha de SQL que qualquer pessoa do negocio consegue ler.
--   2. ESCOPO domestico / internacional, a partir do tipo de linha.
--   3. As DECISOES SOBRE A QUARENTENA do marco-06 (documentadas abaixo).
--
-- Companhia e codigos de operacao entram como DIMENSAO DEGENERADA: codigo e
-- descricao no proprio fato, porque sao poucos atributos, nao mudam no tempo
-- e o consumidor final e um LLM — cada join a menos e um erro a menos.
--
-- ---------------------------------------------------------------------------
-- DECISOES SOBRE A QUARENTENA (213.543 registros diagnosticados no marco-06)
-- ---------------------------------------------------------------------------
-- a) AEROPORTO FORA DO CADASTRO DA ANAC (105.932) -> MANTIDO.
--    Nao e dado invalido, e aeroporto estrangeiro. Descartar mataria a
--    pergunta P4 do projeto. dim_aeroporto cobre 100% do fato.
-- b) VOO SEM HORARIO PREVISTO (30.800) -> MANTIDO.
--    O voo aconteceu e conta em "quantos voos". Sem horario previsto nao ha
--    atraso a calcular: a metrica fica NULL, e NULL ja se exclui sozinho de
--    qualquer media. Zerar seria mentir.
-- c) ATRASO FORA DA FAIXA PLAUSIVEL (778 partida / 823 chegada) -> LINHA
--    MANTIDA, METRICA ANULADA. Ha atrasos de ate 44.855 min (31 dias) e
--    antecipacoes de -43.057 (30 dias): erro de data na origem, nao operacao.
--    A linha continua contando como voo; a metrica vira NULL e a coluna
--    atraso_fora_de_faixa registra por que.
-- d) EMPRESA SEM CADASTRO (69) -> MANTIDA, com nome de fallback.
-- e) DUPLICATA EXATA (41) -> REMOVIDA. Unica exclusao de linha desta camada.
--    Duas linhas byte-identicas sao a mesma etapa publicada duas vezes;
--    conta-la duas vezes infla voos, cancelamentos e atraso ao mesmo tempo.
--    Grao esperado: 1.014.705 - 41 = 1.014.664.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE voebem.gold.fato_voos AS
WITH vra_sem_duplicata AS (
  SELECT * FROM (
    SELECT *,
      ROW_NUMBER() OVER (
        PARTITION BY icao_empresa, numero_voo, codigo_di, codigo_tipo_linha,
                     icao_origem, icao_destino, partida_prevista, partida_real,
                     chegada_prevista, chegada_real, situacao_voo
        ORDER BY _ingerido_em
      ) AS _rn
    FROM voebem.silver.vra
  )
  WHERE _rn = 1
),
empresa AS (
  SELECT icao, razao_social, origem_cadastro
  FROM (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY icao
      ORDER BY CASE WHEN situacao = 'ATIVA' THEN 0 ELSE 1 END, razao_social
    ) AS rn
    FROM voebem.silver.empresas
    WHERE icao IS NOT NULL AND icao <> ''
  )
  WHERE rn = 1
),
di AS (
  SELECT codigo, descricao FROM voebem.silver.codigos_operacao WHERE dominio = 'codigo_di'
),
tipo_linha AS (
  SELECT codigo, descricao FROM voebem.silver.codigos_operacao WHERE dominio = 'codigo_tipo_linha'
),
base AS (
  SELECT
    v.*,
    -- decisao (c): metrica fora da faixa plausivel vira NULL, linha fica
    (v.atraso_partida_min IS NOT NULL AND (v.atraso_partida_min < -120 OR v.atraso_partida_min > 1440))
      OR (v.atraso_chegada_min IS NOT NULL AND (v.atraso_chegada_min < -120 OR v.atraso_chegada_min > 1440))
                                                                    AS atraso_fora_de_faixa
  FROM vra_sem_duplicata v
)
SELECT
  -- ===== dimensao degenerada: companhia =====
  b.icao_empresa,
  COALESCE(e.razao_social, concat('COMPANHIA NAO CADASTRADA (', b.icao_empresa, ')'))
                                                                    AS nome_companhia,
  e.origem_cadastro                                                 AS cadastro_companhia,
  b.numero_voo,

  -- ===== dimensoes degeneradas: codigos de operacao =====
  b.codigo_di,
  COALESCE(d.descricao, concat('Codigo nao catalogado (', b.codigo_di, ')'))
                                                                    AS descricao_di,
  b.codigo_tipo_linha,
  COALESCE(t.descricao, concat('Codigo nao catalogado (', b.codigo_tipo_linha, ')'))
                                                                    AS descricao_tipo_linha,

  -- ===== REGRA DE NEGOCIO: escopo do voo =====
  CASE
    WHEN b.codigo_tipo_linha IN ('N', 'C') THEN 'Domestico'
    WHEN b.codigo_tipo_linha IN ('I', 'G') THEN 'Internacional'
    ELSE 'Nao classificado'
  END                                                               AS escopo_voo,

  -- ===== chaves para dim_aeroporto =====
  b.icao_origem,
  b.icao_destino,
  concat(b.icao_origem, ' - ', b.icao_destino)                      AS rota,

  -- ===== tempo =====
  b.partida_prevista,
  b.partida_prevista_data,
  b.partida_prevista_hora,
  hour(b.partida_prevista)                                          AS hora_partida_prevista,
  CASE dayofweek(b.partida_prevista_data)
    WHEN 1 THEN 'domingo'  WHEN 2 THEN 'segunda' WHEN 3 THEN 'terca'
    WHEN 4 THEN 'quarta'   WHEN 5 THEN 'quinta'  WHEN 6 THEN 'sexta'
    WHEN 7 THEN 'sabado'
  END                                                               AS dia_semana,
  date_trunc('MONTH', b.partida_prevista_data)                      AS mes_referencia,
  b.partida_real,
  b.chegada_prevista,
  b.chegada_real,

  -- ===== metricas (decisao (c) aplicada) =====
  CASE WHEN b.atraso_fora_de_faixa THEN NULL ELSE b.atraso_partida_min  END AS atraso_partida_min,
  CASE WHEN b.atraso_fora_de_faixa THEN NULL ELSE b.atraso_chegada_min  END AS atraso_chegada_min,
  CASE WHEN b.atraso_fora_de_faixa THEN NULL ELSE b.minutos_recuperados END AS minutos_recuperados,
  b.atraso_fora_de_faixa,

  -- ===== REGRA DE NEGOCIO: pontualidade a 15 minutos =====
  CASE WHEN b.atraso_fora_de_faixa OR b.atraso_partida_min IS NULL THEN NULL
       ELSE b.atraso_partida_min <= 15 END                          AS partida_pontual,
  CASE WHEN b.atraso_fora_de_faixa OR b.atraso_chegada_min IS NULL THEN NULL
       ELSE b.atraso_chegada_min <= 15 END                          AS chegada_pontual,

  -- ===== situacao =====
  b.situacao_voo,
  (b.situacao_voo = 'CANCELADO')                                    AS voo_cancelado,
  (b.situacao_voo = 'REALIZADO')                                    AS voo_realizado,

  current_timestamp()                                               AS _processado_em
FROM base b
LEFT JOIN empresa    e ON b.icao_empresa      = e.icao
LEFT JOIN di         d ON b.codigo_di         = d.codigo
LEFT JOIN tipo_linha t ON b.codigo_tipo_linha = t.codigo
