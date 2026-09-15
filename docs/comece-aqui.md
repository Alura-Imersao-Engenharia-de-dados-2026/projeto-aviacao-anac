# Comece aqui — seu primeiro caminho pelo projeto

Ao terminar, você terá tabelas de voos no Databricks e conseguirá consultar os dados com SQL. Siga uma etapa por vez; confira o resultado antes de continuar.

## 1. Baixe os materiais

No repositório do GitHub, use **Code → Download ZIP**. No Windows, clique com o botão direito no ZIP e escolha **Extrair tudo**. Abra a pasta extraída: você deve encontrar `README.md`, `dados`, `notebooks` e `sql`.

Para este caminho pelo navegador, você não precisa instalar Python, Git ou a CLI no computador. Os dados já estão incluídos: 12 CSVs em `dados/vra` e três em `dados/referencias`. Não abra e salve os CSVs no Excel antes do envio, pois isso pode alterar datas e códigos.

## 2. Entre no Databricks

Use o ambiente indicado na aula. Caso precise criar uma conta de estudos, consulte a [orientação oficial de cadastro](https://docs.databricks.com/aws/en/getting-started/free-trial-vs-free-edition) e escolha **Free Edition**. Conclua o cadastro e entre no workspace, a área em que você guardará e executará o projeto.

A Free Edition oferece execução serverless, gerenciada pela plataforma, com limites de uso. Se atingir a cota, aguarde a liberação indicada no ambiente. Consulte os [limites oficiais](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

Os nomes dos menus podem variar com o idioma e a versão. Este guia foi preparado com apoio da documentação oficial; a execução completa em uma conta nova ainda precisa ser validada.

## 3. Prepare o local dos dados

No Databricks, abra **Workspace** e crie um notebook, com linguagem **SQL**, chamado `00_preparar_ambiente`. Selecione o compute **Serverless** disponível no topo.

Abra o arquivo local [00_preparar_ambiente.sql](../sql/00_preparar_ambiente.sql) em um editor de texto. Copie seu conteúdo para a primeira célula do notebook e execute pelo botão de execução da célula ou com **Shift + Enter**. Uma célula é um bloco de código executável.

O comando cria esta organização:

```text
voebem                         catálogo: organiza o projeto
├── bronze                     schema: agrupa tabelas da primeira camada
│   └── arquivos               volume: armazena os CSVs
├── silver                     schema: dados com tipos e documentação
└── gold                       schema: tabelas para análise
```

**Confira:** no menu **Catalog**, procure `voebem`, seus três schemas e o volume `arquivos` dentro de `bronze`. Atualize a listagem se necessário.

Use um ambiente dedicado aos exercícios: etapas posteriores substituem as tabelas do projeto quando executadas novamente.

## 4. Envie os CSVs para o volume

Em **Catalog**, abra `voebem → bronze → arquivos`. Use a opção de envio de arquivos ao volume (**Upload to this volume** ou equivalente). Crie ou indique a pasta de destino `vra` e envie os 12 CSVs de `dados/vra`. Repita para `referencias` com os três CSVs de `dados/referencias`.

O destino precisa ficar exatamente assim:

```text
/Volumes/voebem/bronze/arquivos/vra/VRA_20258.csv
/Volumes/voebem/bronze/arquivos/vra/…outros 11 arquivos…
/Volumes/voebem/bronze/arquivos/referencias/AerodromosPublicos.csv
/Volumes/voebem/bronze/arquivos/referencias/pda_empresas_aereas_nacionais.csv
/Volumes/voebem/bronze/arquivos/referencias/pda_empresas_aereas_estrangeiros.csv
```

Envie os arquivos para o volume; não escolha a importação que cria automaticamente uma tabela. A leitura dos CSVs será feita pelos notebooks. Veja a [documentação de arquivos em volumes](https://docs.databricks.com/aws/en/volumes/volume-files).

Em novas células do notebook SQL, execute uma consulta por vez:

```sql
LIST '/Volumes/voebem/bronze/arquivos/vra/';
```

```sql
LIST '/Volumes/voebem/bronze/arquivos/referencias/';
```

**Confira:** a primeira listagem deve ter 12 arquivos e a segunda, três. Evite criar uma pasta extra `dados` dentro de `arquivos`.

## 5. Importe os notebooks

Em **Workspace**, crie uma pasta chamada `voebem`. No menu da pasta, escolha **Import**, selecione o arquivo local e confirme. Repita para os quatro arquivos `.py` da pasta `notebooks`.

Esses arquivos têm o cabeçalho de notebook Databricks e devem abrir como células de código e texto. Consulte [como importar notebooks](https://docs.databricks.com/aws/en/notebooks/notebook-export-import).

Abra e execute, um de cada vez, nesta ordem:

| Ordem | Notebook | O que faz |
|---|---|---|
| 1 | `03_bronze_vra` | Lê os CSVs de voos e cria a tabela Bronze |
| 2 | `04_bronze_referencias` | Carrega os cadastros e códigos de referência |
| 3 | `05_silver_espelho` | Aplica tipos, cálculos e documentação |

Selecione **Serverless** no notebook e use **Run all** para executar todas as células. Aguarde terminar antes de abrir a próxima etapa. Se houver erro, pare na primeira célula que falhou e consulte a seção de ajuda abaixo.

**Confira:** no notebook SQL, execute:

```sql
SELECT 'bronze' AS camada, COUNT(*) AS linhas FROM voebem.bronze.vra
UNION ALL
SELECT 'silver' AS camada, COUNT(*) AS linhas FROM voebem.silver.vra;
```

As duas contagens devem ser maiores que zero e iguais. A Silver deste projeto preserva as linhas da Bronze. A numeração original dos arquivos foi mantida; você não precisa procurar notebooks 01 ou 02.

## 6. Configure a qualidade dos dados

Pipeline é uma sequência de transformações que o Databricks organiza pelas dependências entre os dados. Esta etapa verifica problemas e cria uma quarentena para investigação; a Silver continua preservada.

1. No **Workspace**, crie três arquivos SQL e copie para eles o conteúdo dos três arquivos de `pipelines/qualidade/`, preservando os nomes.
2. Use **New → ETL pipeline**. Nomeie como `voebem-qualidade`.
3. Escolha **Add existing assets** e associe os três arquivos SQL que você criou.
4. Defina catálogo `voebem`, schema `silver`, compute serverless e modo **Triggered**, para executar e encerrar. Se houver escolha de edição, use **Advanced**, que suporta as regras de qualidade (expectations).
5. Salve e execute a atualização do pipeline. Aguarde a conclusão e confira os resultados e mensagens na tela do pipeline.

Os três arquivos devem pertencer ao mesmo pipeline. Não execute esse SQL no editor de consultas comum. A [documentação de configuração](https://docs.databricks.com/aws/en/ldp/configure-pipeline) detalha as opções.

As métricas de qualidade podem mostrar registros reprovados: isso faz parte do exercício. Para a consulta adicional `sql/metricas_qualidade.sql`, é necessário configurar a publicação do event log em `voebem.silver.eventos_qualidade`; deixe essa configuração complementar para acompanhar com a aula.

## 7. Crie a camada de análise

Volte ao notebook SQL. Para cada arquivo abaixo, copie o conteúdo inteiro para uma célula e execute. Espere concluir antes de executar o próximo:

1. [01_dim_aeroporto.sql](../sql/gold/01_dim_aeroporto.sql)
2. [02_fato_voos.sql](../sql/gold/02_fato_voos.sql)
3. [03_obt_voos.sql](../sql/gold/03_obt_voos.sql)

Depois abra o notebook importado `09_governanca_gold` e execute suas células. Ele documenta as tabelas e colunas para facilitar seu uso.

**Confira:** no notebook SQL, execute:

```sql
SELECT COUNT(*) AS total_voos FROM voebem.gold.obt_voos;
```

```sql
SELECT * FROM voebem.gold.obt_voos LIMIT 10;
```

Você deve obter uma contagem positiva e uma amostra de até dez linhas. OBT é a tabela que reúne os dados necessários para as análises.

## 8. Responda sua primeira pergunta

Abra [P1.sql](../sql/gabarito/P1.sql), copie o conteúdo para uma nova célula SQL e execute. Compare o resultado com a pergunta descrita no arquivo. Depois explore as demais consultas de `sql/gabarito/`.

Parabéns por concluir o primeiro percurso! Você saiu dos CSVs, passou pela preparação e chegou a uma consulta de negócio. Explique com suas palavras o que o resultado mede antes de avançar.

O Genie é uma etapa complementar de perguntas em linguagem natural. Faça primeiro as consultas SQL; depois acompanhe a configuração do espaço com a aula e os materiais de `genie/`. Os scripts de terminal são opcionais e não são necessários para concluir este guia.

## Se algo der errado

| Sintoma | O que verificar |
|---|---|
| `spark is not defined` ou `dbutils is not defined` | Execute o notebook dentro do Databricks, com compute selecionado. |
| Arquivo ou caminho não encontrado | Confira os caminhos da etapa 4, incluindo nomes, pastas e os 15 CSVs. |
| Catálogo ou schema não encontrado | Execute a etapa 3 no mesmo workspace em que está rodando os notebooks. |
| `TABLE_OR_VIEW_NOT_FOUND` | Confira se a etapa anterior terminou sem erro e criou a tabela citada. |
| Permissão negada | No ambiente compartilhado, peça ao responsável acesso ao catálogo, schema, volume ou compute indicado na mensagem. |
| Erro de sintaxe em `LIVE` ou `EXPECT` | Execute os arquivos de qualidade dentro do pipeline, não em uma célula SQL comum. |
| `eventos_qualidade` não encontrada | É a configuração complementar do event log da etapa 6; acompanhe com a aula. |
| Coluna esperada não encontrada no CSV | Confira se usou os arquivos fornecidos, sem conversão pelo Excel e sem trocar por outra fonte. |
| Compute indisponível ou cota excedida | Leia a mensagem do ambiente e aguarde a liberação quando for um limite da Free Edition. |
| Resultado diferente do material | Confira período, arquivos e conclusão das etapas; os registros de aceitação originais não comprovam sua execução. |

Ao pedir ajuda, envie o nome do arquivo, a célula que falhou e o texto completo do erro, sem credenciais. Informe a última etapa concluída. Isso permite que a turma reproduza o problema.

## Checklist final

- [ ] Os 15 CSVs aparecem nos caminhos corretos.
- [ ] Os três primeiros notebooks terminaram sem erro.
- [ ] Bronze e Silver têm a mesma quantidade de voos.
- [ ] O pipeline de qualidade terminou.
- [ ] A Gold foi criada e o notebook de governança executado.
- [ ] A consulta P1 retornou um resultado que consigo explicar.

[Voltar ao README](../README.md)
