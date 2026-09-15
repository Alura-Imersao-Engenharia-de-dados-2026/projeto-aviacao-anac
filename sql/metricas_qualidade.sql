-- ---------------------------------------------------------------------------
-- Metricas do contrato de dados, lidas do event log do pipeline.
--
-- O event log e uma TABELA (voebem.silver.eventos_qualidade), declarada no
-- create do pipeline. A coluna `details` e um JSON string; as metricas de
-- expectation vivem em flow_progress.data_quality.expectations.
--
-- Atencao: `databricks pipelines list-pipeline-events` na CLI v1.13.0 NAO
-- devolve o campo `details` — as metricas so aparecem lendo a tabela.
-- ---------------------------------------------------------------------------
WITH eventos AS (
  SELECT
    origin.update_id AS update_id,
    timestamp,
    from_json(
      details,
      'struct<flow_progress: struct<data_quality: struct<
         expectations: array<struct<name:string, dataset:string,
                                    passed_records:bigint, failed_records:bigint>>>>>'
    ) AS d
  FROM voebem.silver.eventos_qualidade
  WHERE event_type = 'flow_progress'
)
SELECT
  x.name                                                              AS regra,
  x.passed_records                                                    AS aprovadas,
  x.failed_records                                                    AS reprovadas,
  ROUND(100.0 * x.failed_records / (x.passed_records + x.failed_records), 2) AS pct_reprovado
FROM eventos
LATERAL VIEW explode(d.flow_progress.data_quality.expectations) t AS x
WHERE update_id = (
  SELECT origin.update_id FROM voebem.silver.eventos_qualidade
  ORDER BY timestamp DESC LIMIT 1
)
ORDER BY reprovadas DESC;
