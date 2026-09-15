-- ---------------------------------------------------------------------------
-- Passo 2 — o contrato de dados, escrito como codigo.
--
-- TODAS as expectations aqui sao "warn" (nenhuma tem ON VIOLATION). Isso e
-- arquitetura, nao preguica: a silver nao pode perder registro. As expectations
-- MEDEM a qualidade e publicam a metrica no event log; a linha continua viva.
--
-- Quem decide excluir e a gold, porque excluir e decisao de negocio.
--
-- Por que LIVE VIEW e nao TEMPORARY VIEW: CREATE TEMPORARY VIEW nao aceita
-- clausula CONSTRAINT. LIVE VIEW e a forma retida exatamente para o caso
-- "view intermediaria com expectations" — nada e materializado em UC aqui,
-- so as metricas do contrato saem para o event log.
--
-- Cuidado com NULL: numa expectation, NULL conta como REPROVADO. Por isso as
-- regras que podem receber NULL legitimamente (voo cancelado nao tem horario
-- real) escrevem o NULL como aprovado, explicitamente. Sem isso, uma regra
-- mede outra: as duas devolvem o mesmo numero e voce reporta 30 mil voos com
-- "chegada antes da partida" que nao existem.
-- ---------------------------------------------------------------------------
CREATE LIVE VIEW vra_auditado (
  -- === completude ===
  CONSTRAINT horarios_previstos_presentes
    EXPECT (partida_prevista IS NOT NULL AND chegada_prevista IS NOT NULL),

  CONSTRAINT situacao_voo_conhecida
    EXPECT (situacao_voo IN ('REALIZADO', 'CANCELADO')),

  -- === coerencia temporal (NULL aprovado explicitamente) ===
  CONSTRAINT chegada_prevista_depois_da_partida_prevista
    EXPECT (partida_prevista IS NULL OR chegada_prevista IS NULL
            OR chegada_prevista > partida_prevista),

  CONSTRAINT chegada_real_depois_da_partida_real
    EXPECT (partida_real IS NULL OR chegada_real IS NULL
            OR chegada_real > partida_real),

  -- === faixa plausivel: -2h de antecipacao a 24h de atraso ===
  CONSTRAINT atraso_partida_plausivel
    EXPECT (atraso_partida_min IS NULL
            OR atraso_partida_min BETWEEN -120 AND 1440),

  CONSTRAINT atraso_chegada_plausivel
    EXPECT (atraso_chegada_min IS NULL
            OR atraso_chegada_min BETWEEN -120 AND 1440),

  -- === integridade referencial (a flag vem do passo 1) ===
  CONSTRAINT empresa_no_cadastro_anac
    EXPECT (empresa_no_cadastro),

  CONSTRAINT aeroporto_origem_no_cadastro_anac
    EXPECT (origem_no_cadastro),

  CONSTRAINT aeroporto_destino_no_cadastro_anac
    EXPECT (destino_no_cadastro)
)
COMMENT 'Contrato de dados de silver.vra. Nove expectations, todas em modo warn:
 medem qualidade sem descartar linha. A silver segue com a contagem original.'
AS SELECT * FROM vra_marcado;
