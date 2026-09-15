# Databricks notebook source
# MAGIC %md
# MAGIC # Silver — espelho governado do bronze
# MAGIC
# MAGIC A regra da casa, e ela não é negociável:
# MAGIC
# MAGIC > **A silver é o espelho do bronze com governança aplicada.**
# MAGIC > Mesmo nome de tabela, mesmo grão, **mesma contagem de linhas**.
# MAGIC
# MAGIC | | permitido na silver | proibido na silver |
# MAGIC |---|---|---|
# MAGIC | tipagem | ✅ string vira `TIMESTAMP`, `INT`, `DATE` | |
# MAGIC | legibilidade | ✅ quebrar timestamp em data e hora | |
# MAGIC | metadados | ✅ `COMMENT` em toda coluna, tags na tabela | |
# MAGIC | unificação | ✅ dois cadastros do mesmo assunto, com a origem por registro | |
# MAGIC | aritmética pura | ✅ `atraso = real - previsto` | |
# MAGIC | filtro / `WHERE` de negócio | | ❌ |
# MAGIC | `GROUP BY` / agregação | | ❌ |
# MAGIC | limiar, flag, classificação | | ❌ |
# MAGIC
# MAGIC **Por quê?** Porque a silver precisa servir várias análises, e toda linha que ela
# MAGIC descarta é uma pergunta que ninguém mais vai conseguir fazer. Filtro fecha porta.
# MAGIC
# MAGIC O teste para qualquer coluna nova: *isso embute uma decisão de negócio?*
# MAGIC `atraso_partida_min = partida_real - partida_prevista` é subtração — silver.
# MAGIC `partida_pontual = atraso <= 15` embute o número **15**, que é decisão de negócio
# MAGIC e muda por cliente — gold.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. O que precisa ser consertado na tipagem
# MAGIC
# MAGIC Antes de escrever o `CAST`, medir. Duas armadilhas escondidas no bronze:

# COMMAND ----------

display(spark.sql("""
    SELECT
      COUNT(*)                                                        AS linhas,
      SUM(CASE WHEN partida_real     IS NULL THEN 1 ELSE 0 END)       AS partida_real_null_de_verdade,
      SUM(CASE WHEN partida_real     = 'null' THEN 1 ELSE 0 END)      AS partida_real_string_null,
      SUM(CASE WHEN partida_prevista = 'null' THEN 1 ELSE 0 END)      AS partida_prevista_string_null,
      SUM(CASE WHEN partida_prevista LIKE '%.%' THEN 1 ELSE 0 END)    AS com_fracao_de_segundo
    FROM voebem.bronze.vra
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC **Armadilha 1 — a ausência veio como a string `'null'`.** Quatro caracteres de texto.
# MAGIC `WHERE partida_real IS NULL` devolve **zero** numa tabela onde 29 mil voos não têm
# MAGIC horário real. Correção: `nullif(coluna, 'null')` **antes** do cast.
# MAGIC
# MAGIC **Armadilha 2 — dois formatos de timestamp no mesmo arquivo.** A maioria vem
# MAGIC `2026-01-27 19:45:00`, mas ~80 mil linhas vêm com fração de segundo de 9 casas.
# MAGIC Um `to_timestamp(col, 'yyyy-MM-dd HH:mm:ss')` fixo devolveria NULL para 8% da base,
# MAGIC em silêncio. O `try_cast(... AS TIMESTAMP)` aceita os dois formatos, e o `try_`
# MAGIC garante que um formato novo vire NULL em vez de derrubar o job.
# MAGIC
# MAGIC Note que isso é **tipagem**, não limpeza de negócio: `'null'` é a forma como a fonte
# MAGIC escreve "ausente". Traduzir isso para `NULL` é dizer a mesma coisa no tipo certo.
# MAGIC Nenhuma linha sai.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. `silver.vra` — o espelho
# MAGIC
# MAGIC Repare no que **não** existe nesta query: nenhum `WHERE`, nenhum `GROUP BY`,
# MAGIC nenhum `DISTINCT`, nenhum `JOIN`. É um `SELECT` de projeção sobre o bronze inteiro.
# MAGIC
# MAGIC E repare nas três colunas do fim: `atraso_partida_min`, `atraso_chegada_min` e
# MAGIC `minutos_recuperados`. São subtrações entre colunas da própria linha. Não têm
# MAGIC limiar, não classificam nada, não escondem número mágico — e, principalmente,
# MAGIC não impedem análise nenhuma. Por isso podem morar aqui.

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE voebem.silver.vra AS
WITH tipado AS (
  SELECT
    icao_empresa,
    numero_voo,
    codigo_di,
    codigo_tipo_linha,
    icao_origem,
    icao_destino,
    try_cast(nullif(partida_prevista, 'null') AS TIMESTAMP) AS partida_prevista,
    try_cast(nullif(partida_real,     'null') AS TIMESTAMP) AS partida_real,
    try_cast(nullif(chegada_prevista, 'null') AS TIMESTAMP) AS chegada_prevista,
    try_cast(nullif(chegada_real,     'null') AS TIMESTAMP) AS chegada_real,
    situacao_voo,
    nullif(codigo_justificativa, 'N/A')                     AS codigo_justificativa,
    _arquivo_origem,
    _ingerido_em
  FROM voebem.bronze.vra
)
SELECT
  icao_empresa,
  numero_voo,
  codigo_di,
  codigo_tipo_linha,
  icao_origem,
  icao_destino,

  partida_prevista,
  CAST(partida_prevista AS DATE)                     AS partida_prevista_data,
  date_format(partida_prevista, 'HH:mm')             AS partida_prevista_hora,

  partida_real,
  CAST(partida_real AS DATE)                         AS partida_real_data,
  date_format(partida_real, 'HH:mm')                 AS partida_real_hora,

  chegada_prevista,
  CAST(chegada_prevista AS DATE)                     AS chegada_prevista_data,
  date_format(chegada_prevista, 'HH:mm')             AS chegada_prevista_hora,

  chegada_real,
  CAST(chegada_real AS DATE)                         AS chegada_real_data,
  date_format(chegada_real, 'HH:mm')                 AS chegada_real_hora,

  situacao_voo,
  codigo_justificativa,

  -- aritmetica pura: subtracao de colunas da propria linha, sem limiar e sem decisao
  CAST(timestampdiff(MINUTE, partida_prevista, partida_real) AS INT) AS atraso_partida_min,
  CAST(timestampdiff(MINUTE, chegada_prevista, chegada_real) AS INT) AS atraso_chegada_min,
  CAST(timestampdiff(MINUTE, partida_prevista, partida_real)
     - timestampdiff(MINUTE, chegada_prevista, chegada_real) AS INT) AS minutos_recuperados,

  _arquivo_origem,
  _ingerido_em,
  current_timestamp()                                AS _transformado_em
FROM tipado
""")

print("silver.vra criada")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. A prova que importa: mesma contagem
# MAGIC
# MAGIC Este é o critério objetivo do marco. Se a diferença não for **zero**, a silver
# MAGIC não é espelho — é recorte, e alguém em algum momento vai fazer uma pergunta que
# MAGIC ela não consegue mais responder.

# COMMAND ----------

display(spark.sql("""
    SELECT
      (SELECT COUNT(*) FROM voebem.bronze.vra) AS bronze_vra,
      (SELECT COUNT(*) FROM voebem.silver.vra) AS silver_vra,
      (SELECT COUNT(*) FROM voebem.bronze.vra)
        - (SELECT COUNT(*) FROM voebem.silver.vra) AS diferenca
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC E a tipagem funcionou? Contagem de conversões bem-sucedidas por coluna:

# COMMAND ----------

display(spark.sql("""
    SELECT
      COUNT(partida_prevista)     AS partida_prevista_ok,
      COUNT(partida_real)         AS partida_real_ok,
      COUNT(chegada_prevista)     AS chegada_prevista_ok,
      COUNT(chegada_real)         AS chegada_real_ok,
      COUNT(atraso_partida_min)   AS atraso_partida_ok,
      COUNT(minutos_recuperados)  AS minutos_recuperados_ok
    FROM voebem.silver.vra
"""))

# COMMAND ----------

display(spark.sql("""
    SELECT icao_empresa, numero_voo, icao_origem, icao_destino,
           partida_prevista, partida_prevista_data, partida_prevista_hora,
           atraso_partida_min, atraso_chegada_min, minutos_recuperados, situacao_voo
    FROM voebem.silver.vra
    ORDER BY partida_prevista
    LIMIT 5
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. `silver.empresas` — o caso clássico dos dois sistemas
# MAGIC
# MAGIC Aqui a silver faz a única coisa que muda a forma da tabela: **unifica dois cadastros
# MAGIC do mesmo assunto**. `bronze.empresas_nacionais` e `bronze.empresas_estrangeiras` são
# MAGIC dois processos administrativos da ANAC descrevendo a mesma entidade de negócio —
# MAGIC "empresa aérea que opera no Brasil".
# MAGIC
# MAGIC Isso é permitido porque **não perde informação**: a contagem da silver é a soma exata
# MAGIC das duas, e `origem_cadastro` guarda por registro de onde ele veio. Quem quiser
# MAGIC voltar a olhar só as estrangeiras, consegue. Nada fecha.
# MAGIC
# MAGIC O que seria proibido: um `WHERE situacao = 'ATIVA'` aqui. Empresa que encerrou
# MAGIC operação continua tendo voado no período — filtrar apagaria o histórico dela.

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE voebem.silver.empresas AS
SELECT
  icao,
  sigla_iata,
  razao_social,
  servico,
  cidade,
  uf,
  situacao,
  'nacional'      AS origem_cadastro,
  _arquivo_origem,
  _ingerido_em,
  current_timestamp() AS _transformado_em
FROM voebem.bronze.empresas_nacionais
UNION ALL
SELECT
  icao,
  sigla_iata,
  razao_social,
  servico,
  cidade,
  uf,
  situacao,
  'estrangeira'   AS origem_cadastro,
  _arquivo_origem,
  _ingerido_em,
  current_timestamp() AS _transformado_em
FROM voebem.bronze.empresas_estrangeiras
""")

display(spark.sql("""
    SELECT
      (SELECT COUNT(*) FROM voebem.bronze.empresas_nacionais)    AS bronze_nacionais,
      (SELECT COUNT(*) FROM voebem.bronze.empresas_estrangeiras) AS bronze_estrangeiras,
      (SELECT COUNT(*) FROM voebem.bronze.empresas_nacionais)
        + (SELECT COUNT(*) FROM voebem.bronze.empresas_estrangeiras) AS soma_esperada,
      (SELECT COUNT(*) FROM voebem.silver.empresas)              AS silver_empresas
"""))

# COMMAND ----------

display(spark.sql("""
    SELECT origem_cadastro,
           COUNT(*) AS linhas,
           COUNT(CASE WHEN icao IS NOT NULL AND icao <> '' THEN 1 END) AS com_icao
    FROM voebem.silver.empresas
    GROUP BY origem_cadastro
    ORDER BY origem_cadastro
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC > Este `GROUP BY` é **conferência**, não construção. A tabela já está escrita; o
# MAGIC > agrupamento aqui só serve para eu olhar o resultado. A proibição vale para o que
# MAGIC > é **materializado** na silver.
# MAGIC
# MAGIC Só 20 das 729 empresas nacionais têm código ICAO — o cadastro é dominado por aviação
# MAGIC agrícola, táxi aéreo e aeroclube, que não têm código de três letras. Quem voa linha
# MAGIC regular tem. Isso volta no marco-07, quando o join com o VRA for medido.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. `silver.aerodromos` e `silver.codigos_operacao` — espelhos
# MAGIC
# MAGIC Uma tabela de referência para cada uma do bronze, tipada e documentada. Duas coisas
# MAGIC valem comentário:
# MAGIC
# MAGIC - `altitude` vem como `"193,0"` — vírgula decimal. Vira `DOUBLE` com um `replace`.
# MAGIC - a coluna que o cabeçalho chama de `UF` contém `"Acre"`, `"São Paulo"`: é o **nome
# MAGIC   da unidade federativa por extenso**, não a sigla. Quem escrever `WHERE uf = 'SP'`
# MAGIC   recebe zero linhas e vai achar que o dado sumiu. O nome da coluna passa a dizer a
# MAGIC   verdade (`uf_nome`) e o `COMMENT` avisa. Renomear e documentar é governança;
# MAGIC   inventar a sigla seria transformação de negócio.

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE voebem.silver.aerodromos AS
SELECT
  icao,
  ciad,
  nome,
  municipio,
  uf                                            AS uf_nome,
  municipio_servido,
  uf_servido                                    AS uf_servido_nome,
  latitude                                      AS latitude_dms,
  longitude                                     AS longitude_dms,
  try_cast(replace(altitude, ',', '.') AS DOUBLE) AS altitude_m,
  situacao,
  _ingerido_em,
  current_timestamp()                           AS _transformado_em
FROM voebem.bronze.aerodromos
""")

spark.sql("""
CREATE OR REPLACE TABLE voebem.silver.codigos_operacao AS
SELECT
  dominio,
  codigo,
  descricao,
  current_timestamp() AS _transformado_em
FROM voebem.bronze.codigos_operacao
""")

display(spark.sql("""
    SELECT 'aerodromos' AS tabela,
           (SELECT COUNT(*) FROM voebem.bronze.aerodromos) AS bronze,
           (SELECT COUNT(*) FROM voebem.silver.aerodromos) AS silver
    UNION ALL
    SELECT 'codigos_operacao',
           (SELECT COUNT(*) FROM voebem.bronze.codigos_operacao),
           (SELECT COUNT(*) FROM voebem.silver.codigos_operacao)
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Metadados gerenciados
# MAGIC
# MAGIC Documentação não é enfeite: o consumidor final deste pipeline é um **LLM**, e o
# MAGIC `COMMENT` é literalmente o que ele lê para decidir qual coluna usar. Coluna sem
# MAGIC comentário é coluna que a IA vai usar errado.
# MAGIC
# MAGIC O comentário descreve **significado de negócio**, não tipo de dado. "TIMESTAMP da
# MAGIC partida" não ajuda ninguém; "horário em que a aeronave efetivamente saiu do solo"
# MAGIC ajuda.

# COMMAND ----------

COMENTARIOS_VRA = {
    "icao_empresa":            "Codigo ICAO de tres letras da empresa aerea que operou a etapa. Chave para silver.empresas.",
    "numero_voo":              "Numero do voo divulgado pela companhia. Identificador comercial, nao numerico: pode ter zero a esquerda e se repete entre datas.",
    "codigo_di":               "Codigo de autorizacao (DI) da etapa: distingue etapa regular, extra, de retorno, charter. Descricao em silver.codigos_operacao (dominio codigo_di).",
    "codigo_tipo_linha":       "Codigo do tipo de linha: N e C domesticas, I e G internacionais. Descricao em silver.codigos_operacao (dominio codigo_tipo_linha).",
    "icao_origem":             "Codigo ICAO do aerodromo de onde a etapa partiu. Chave para silver.aerodromos - aeroportos estrangeiros nao constam no cadastro da ANAC.",
    "icao_destino":            "Codigo ICAO do aerodromo onde a etapa pousou. Mesma observacao de cobertura da origem.",
    "partida_prevista":        "Horario de partida programado pela companhia, na hora local do aeroporto de origem.",
    "partida_prevista_data":   "Data da partida programada, separada para facilitar analise por dia.",
    "partida_prevista_hora":   "Hora e minuto da partida programada (HH:mm), separada para analise por faixa horaria.",
    "partida_real":            "Horario em que a aeronave efetivamente saiu. Nulo em voo cancelado, que nao chegou a partir.",
    "partida_real_data":       "Data da partida efetiva.",
    "partida_real_hora":       "Hora e minuto da partida efetiva (HH:mm).",
    "chegada_prevista":        "Horario de chegada programado, na hora local do aeroporto de destino.",
    "chegada_prevista_data":   "Data da chegada programada.",
    "chegada_prevista_hora":   "Hora e minuto da chegada programada (HH:mm).",
    "chegada_real":            "Horario em que a aeronave efetivamente pousou. Nulo em voo cancelado.",
    "chegada_real_data":       "Data da chegada efetiva.",
    "chegada_real_hora":       "Hora e minuto da chegada efetiva (HH:mm).",
    "situacao_voo":            "Situacao informada pela companhia: REALIZADO quando a etapa aconteceu, CANCELADO quando nao.",
    "codigo_justificativa":    "Motivo declarado do atraso. Deixou de ser exigido pela ANAC em abril de 2020 com a revogacao da IAC 1504: vem vazio em toda a janela deste projeto.",
    "atraso_partida_min":      "Minutos entre a partida programada e a partida efetiva. Positivo e atraso, negativo e antecipacao. Aritmetica pura: nao aplica limiar de pontualidade.",
    "atraso_chegada_min":      "Minutos entre a chegada programada e a chegada efetiva. Positivo e atraso, negativo e antecipacao.",
    "minutos_recuperados":     "Minutos que a etapa recuperou em voo: atraso de partida menos atraso de chegada. Positivo significa que chegou menos atrasada do que saiu.",
    "_arquivo_origem":         "Auditoria: nome do arquivo CSV mensal da ANAC de onde a linha veio.",
    "_ingerido_em":            "Auditoria: momento em que a linha entrou no bronze.",
    "_transformado_em":        "Auditoria: momento em que a silver foi reconstruida a partir do bronze.",
}

for coluna, comentario in COMENTARIOS_VRA.items():
    spark.sql(f"ALTER TABLE voebem.silver.vra ALTER COLUMN {coluna} COMMENT '{comentario}'")

print(f"{len(COMENTARIOS_VRA)} colunas comentadas em silver.vra")

# COMMAND ----------

COMENTARIOS_EMPRESAS = {
    "icao":            "Codigo ICAO de tres letras da empresa. Vazio para operadores sem codigo (aviacao agricola, taxi aereo, aeroclube).",
    "sigla_iata":      "Sigla de duas letras da empresa no padrao IATA, como publicada pela ANAC.",
    "razao_social":    "Razao social da empresa aerea. E o nome que aparece para quem consome o produto final.",
    "servico":         "Tipo de servico autorizado pela ANAC: transporte regular, nao regular, aeroagricola, taxi aereo.",
    "cidade":          "Municipio da sede ou do representante legal no Brasil.",
    "uf":              "Sigla da unidade federativa da sede.",
    "situacao":        "Situacao do registro na ANAC: ATIVA ou nao. Registro inativo permanece na tabela porque a empresa pode ter voado no periodo analisado.",
    "origem_cadastro": "De qual dos dois cadastros da ANAC este registro veio: nacional ou estrangeira. E a coluna que preserva a fronteira entre as duas fontes depois da uniao.",
    "_arquivo_origem": "Auditoria: arquivo CSV de origem.",
    "_ingerido_em":    "Auditoria: momento da ingestao no bronze.",
    "_transformado_em":"Auditoria: momento da construcao da silver.",
}

COMENTARIOS_AERODROMOS = {
    "icao":              "Codigo ICAO (OACI) do aerodromo. Chave de ligacao com origem e destino do VRA.",
    "ciad":              "Codigo de identificacao do aerodromo no cadastro da ANAC.",
    "nome":              "Nome do aerodromo como publicado pela ANAC.",
    "municipio":         "Municipio onde o aerodromo esta fisicamente localizado.",
    "uf_nome":           "Nome da unidade federativa POR EXTENSO (Acre, Sao Paulo), nao a sigla: e assim que a ANAC publica.",
    "municipio_servido": "Municipio principal atendido pelo aerodromo, que pode ser diferente do municipio onde ele fica.",
    "uf_servido_nome":   "Nome por extenso da UF do municipio servido.",
    "latitude_dms":      "Latitude em graus, minutos e segundos, como publicada pela ANAC.",
    "longitude_dms":     "Longitude em graus, minutos e segundos, como publicada pela ANAC.",
    "altitude_m":        "Altitude do aerodromo em metros. Na origem vem com virgula decimal.",
    "situacao":          "Situacao do aerodromo no cadastro da ANAC.",
    "_ingerido_em":      "Auditoria: momento da ingestao no bronze.",
    "_transformado_em":  "Auditoria: momento da construcao da silver.",
}

COMENTARIOS_CODIGOS = {
    "dominio":          "A qual coluna do VRA este codigo pertence: codigo_di ou codigo_tipo_linha.",
    "codigo":           "O codigo como aparece no VRA.",
    "descricao":        "Descricao oficial do codigo, curada da pagina de descricao de variaveis da ANAC.",
    "_transformado_em": "Auditoria: momento da construcao da silver.",
}

for tabela, mapa in [
    ("voebem.silver.empresas",         COMENTARIOS_EMPRESAS),
    ("voebem.silver.aerodromos",       COMENTARIOS_AERODROMOS),
    ("voebem.silver.codigos_operacao", COMENTARIOS_CODIGOS),
]:
    for coluna, comentario in mapa.items():
        spark.sql(f"ALTER TABLE {tabela} ALTER COLUMN {coluna} COMMENT '{comentario}'")
    print(f"{len(mapa)} colunas comentadas em {tabela}")

# COMMAND ----------

# MAGIC %md
# MAGIC Comentário de tabela e **tags**. Tag é metadado de busca e de política: é como alguém
# MAGIC que nunca viu este projeto encontra "todas as tabelas da camada silver" ou "tudo que
# MAGIC é do domínio aviação" sem precisar perguntar para a gente.

# COMMAND ----------

TABELAS = {
    "voebem.silver.vra": (
        "Silver - espelho governado de bronze.vra. Mesmo grao (uma linha por etapa de voo) e "
        "MESMA contagem de linhas do bronze: sem filtro, sem agregacao e sem regra de negocio. "
        "Traz tipagem, data e hora separadas e as tres metricas de aritmetica pura de atraso. "
        "Pontualidade, escopo e exclusoes ficam na gold.",
        {"camada": "silver", "dominio": "aviacao", "fonte": "ANAC-VRA", "grao": "etapa_de_voo"},
    ),
    "voebem.silver.empresas": (
        "Silver - cadastro unificado de empresas aereas: uniao dos dois cadastros do bronze "
        "(nacionais e estrangeiras) com a coluna origem_cadastro preservando a fonte de cada registro. "
        "Contagem igual a soma exata das duas tabelas de origem.",
        {"camada": "silver", "dominio": "aviacao", "fonte": "ANAC-Operador-Aereo", "grao": "empresa"},
    ),
    "voebem.silver.aerodromos": (
        "Silver - espelho governado do cadastro de aerodromos publicos da ANAC. Cobre apenas "
        "aerodromos brasileiros: aeroportos estrangeiros do VRA nao constam aqui, e isso e "
        "propriedade da fonte, nao defeito.",
        {"camada": "silver", "dominio": "aviacao", "fonte": "ANAC-Aerodromos", "grao": "aerodromo"},
    ),
    "voebem.silver.codigos_operacao": (
        "Silver - espelho da seed table de codigos de operacao (DI e tipo de linha) com as "
        "descricoes oficiais da ANAC.",
        {"camada": "silver", "dominio": "aviacao", "fonte": "ANAC-seed", "grao": "codigo"},
    ),
}

for tabela, (comentario, tags) in TABELAS.items():
    spark.sql(f"COMMENT ON TABLE {tabela} IS '{comentario}'")
    pares = ", ".join(f"'{k}' = '{v}'" for k, v in tags.items())
    spark.sql(f"ALTER TABLE {tabela} SET TAGS ({pares})")
    print(f"{tabela}: comentario + {len(tags)} tags")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Auditoria da governança: 100% das colunas comentadas?
# MAGIC
# MAGIC "Documentei tudo" é afirmação, não fato. O `information_schema` responde de verdade:

# COMMAND ----------

display(spark.sql("""
    SELECT table_name,
           COUNT(*)                                                          AS colunas,
           SUM(CASE WHEN comment IS NULL OR comment = '' THEN 1 ELSE 0 END)  AS sem_comentario,
           ROUND(100.0 * SUM(CASE WHEN comment IS NOT NULL AND comment <> '' THEN 1 ELSE 0 END)
                 / COUNT(*), 1)                                              AS pct_documentado
    FROM voebem.information_schema.columns
    WHERE table_schema = 'silver'
    GROUP BY table_name
    ORDER BY table_name
"""))

# COMMAND ----------

display(spark.sql("""
    SELECT table_name, tag_name, tag_value
    FROM voebem.information_schema.table_tags
    WHERE schema_name = 'silver'
    ORDER BY table_name, tag_name
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Fechamento do marco
# MAGIC
# MAGIC A silver tem quatro tabelas, todas espelho do bronze, todas documentadas, e a `vra`
# MAGIC com exatamente a mesma contagem de linhas da origem.
# MAGIC
# MAGIC O que **não** está aqui, de propósito: `partida_pontual`, `escopo`, qualquer
# MAGIC agregação. O limiar de 15 minutos é uma decisão do cliente — outra seguradora pode
# MAGIC trabalhar com 30. Se ele estivesse cravado na silver, atender esse outro cliente
# MAGIC significaria reprocessar a camada inteira. Na gold, é uma linha de SQL.

# COMMAND ----------

display(spark.sql("SHOW TABLES IN voebem.silver"))
