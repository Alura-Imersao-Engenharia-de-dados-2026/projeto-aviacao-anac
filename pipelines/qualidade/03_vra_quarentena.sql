-- ---------------------------------------------------------------------------
-- Passo 3 — quarentena como DIAGNOSTICO, nao como filtro.
--
-- A silver nao filtra. Entao esta tabela nao "tira" registro de lugar nenhum:
-- ela e um ESPELHO dos registros que reprovaram em alguma regra, com o motivo
-- ao lado, para investigacao. silver.vra continua com 100% das linhas.
--
-- Um registro pode reprovar em mais de uma regra: motivos_quarentena lista
-- todas, separadas por " | ". A lista e espelho exato das expectations do
-- passo 2 — se uma regra mudar la, muda aqui.
-- ---------------------------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW vra_quarentena
COMMENT 'Silver quarentena - espelho DIAGNOSTICO dos registros de silver.vra que
 reprovaram em alguma expectation do contrato de dados, com o motivo por registro.
 NAO e filtro: silver.vra permanece com a contagem original. A decisao de excluir
 ou nao cada categoria e de negocio e acontece na gold.'
AS
SELECT
  *,
  concat_ws(' | ',
    CASE WHEN partida_prevista IS NULL OR chegada_prevista IS NULL
         THEN 'horarios_previstos_presentes' END,
    CASE WHEN situacao_voo NOT IN ('REALIZADO', 'CANCELADO') OR situacao_voo IS NULL
         THEN 'situacao_voo_conhecida' END,
    CASE WHEN partida_prevista IS NOT NULL AND chegada_prevista IS NOT NULL
              AND chegada_prevista <= partida_prevista
         THEN 'chegada_prevista_depois_da_partida_prevista' END,
    CASE WHEN partida_real IS NOT NULL AND chegada_real IS NOT NULL
              AND chegada_real <= partida_real
         THEN 'chegada_real_depois_da_partida_real' END,
    CASE WHEN atraso_partida_min IS NOT NULL
              AND (atraso_partida_min < -120 OR atraso_partida_min > 1440)
         THEN 'atraso_partida_plausivel' END,
    CASE WHEN atraso_chegada_min IS NOT NULL
              AND (atraso_chegada_min < -120 OR atraso_chegada_min > 1440)
         THEN 'atraso_chegada_plausivel' END,
    CASE WHEN NOT empresa_no_cadastro THEN 'empresa_no_cadastro_anac' END,
    CASE WHEN NOT origem_no_cadastro THEN 'aeroporto_origem_no_cadastro_anac' END,
    CASE WHEN NOT destino_no_cadastro THEN 'aeroporto_destino_no_cadastro_anac' END
  ) AS motivos_quarentena,
  current_timestamp() AS _quarentenado_em
FROM vra_auditado
WHERE NOT (
      partida_prevista IS NOT NULL AND chegada_prevista IS NOT NULL
  AND situacao_voo IN ('REALIZADO', 'CANCELADO')
  AND (partida_prevista IS NULL OR chegada_prevista IS NULL OR chegada_prevista > partida_prevista)
  AND (partida_real IS NULL OR chegada_real IS NULL OR chegada_real > partida_real)
  AND (atraso_partida_min IS NULL OR atraso_partida_min BETWEEN -120 AND 1440)
  AND (atraso_chegada_min IS NULL OR atraso_chegada_min BETWEEN -120 AND 1440)
  AND empresa_no_cadastro
  AND origem_no_cadastro
  AND destino_no_cadastro
);
