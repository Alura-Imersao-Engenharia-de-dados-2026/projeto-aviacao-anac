# Teste de aceitação — Genie Agent × gabarito SQL

**Espaço:** `SEU_GENIE_SPACE_ID` — *VoeBem Analytics - Voos, atrasos e
pontualidade (ANAC)*
**Fonte única:** `voebem.gold.obt_voos` (1.014.664 linhas)
**Gabarito:** `sql/gabarito/P1..P5b.sql`, validados no marco-08.

O critério não é "a resposta parece boa". É: **o SQL que o Genie gerou devolve os mesmos
números da query que nós escrevemos à mão?**

---

## Resumo

| pergunta | rodada 1 (antes) | rodada 2 (depois das instructions) |
|---|---|---|
| P1 — aeroportos e rotas com maiores atrasos | ❌ **FAILED** — SQL inválido | ✅ idêntico ao gabarito |
| P2 — atraso ao longo do dia | ✅ idêntico ao gabarito | ✅ (não precisou de ajuste) |
| P3 — companhia com melhor pontualidade | ⚠️ divergiu — interpretou "porte" como tipo de linha | ✅ idêntico ao gabarito |
| P4 — internacional × doméstico | ⚠️ divergiu — misturou aeroporto estrangeiro no ranking | ✅ idêntico ao gabarito |
| P5 — recuperação em voo | ⚠️ parcial — respondeu companhias, ignorou rotas | ✅ + follow-up idêntico ao P5b |

**3 divergências e 1 falha na primeira rodada; 5 acertos na segunda.** Todas as correções
foram feitas nas `text_instructions` — nenhuma linha de SQL da OBT precisou mudar.

---

## P1 — "Quais rotas e aeroportos concentram os maiores atrasos de partida no Brasil?"

### Antes: FAILED

```
[PARSE_SYNTAX_ERROR] Syntax error at or near 'UNION': missing ')'. (line 1, pos 1015)
```

O agente tentou responder as **duas** dimensões da pergunta numa consulta só, colando os
dois agrupamentos com `UNION ALL` — e cada lado tinha o seu `ORDER BY ... LIMIT`:

```sql
WITH aeroportos AS (SELECT nome_aeroporto_origem, ..., NULL AS rota_municipios ...),
     rotas      AS (SELECT NULL AS nome_aeroporto_origem, ..., rota_municipios ...)
SELECT * FROM (SELECT * FROM aeroportos ORDER BY pct_atrasados DESC LIMIT 10
               UNION ALL
               SELECT * FROM rotas ORDER BY pct_atrasados DESC LIMIT 10)
ORDER BY pct_atrasados DESC
```

O diagnóstico é interessante: o SQL está **conceitualmente certo** e sintaticamente
inválido. O agente entendeu a pergunta melhor do que consegue escrevê-la.

### Correção aplicada nas instructions

```
PERGUNTA COM DUAS DIMENSOES (por exemplo "aeroportos E rotas", "companhias E rotas"):
responda UMA dimensao por vez, com uma consulta so. NUNCA junte dois agrupamentos
diferentes com UNION ou UNION ALL - isso gera SQL invalido e a resposta falha. Responda a
primeira dimensao citada e diga, no texto, que a segunda pode ser pedida na sequencia.
```

### Depois: ✅

SQL gerado **idêntico** ao `sql/gabarito/P1.sql`, incluindo `WHERE pais_origem = 'Brasil'`,
`HAVING COUNT(*) >= 5000` e o `try_divide`.

| aeroporto | voos | atraso médio | % atrasados |
|---|---:|---:|---:|
| Guarulhos | 147.968 | 13,42 | 27,10 |
| Congonhas | 95.707 | 7,19 | 19,42 |
| Viracopos | 60.382 | 10,48 | 17,67 |

Confere linha a linha com o gabarito. E a segunda dimensão, perguntada em seguida
("Quais rotas domésticas têm o maior atraso médio de partida?"), devolveu o
`sql/gabarito/P1b.sql`, também idêntico: GUARULHOS - MANAUS no topo, 21,26 min.

---

## P2 — "Como o atraso evolui ao longo do dia?"

### Antes e depois: ✅ (acertou de primeira)

SQL idêntico ao `sql/gabarito/P2.sql`. Resultado idêntico: 0,92 min às 5h, 12,72 min às
23h, 23,48 min à 0h.

E a resposta em texto é boa: *"os menores atrasos ocorrem nas primeiras horas da manhã,
enquanto os maiores são registrados no fim da noite"*. A pergunta original falava em
"quanto do atraso noturno é herdado da manhã" — o agente descreve a curva corretamente,
mas não afirma causalidade, o que é o comportamento certo: o dado mostra correlação com a
hora, não a herança de aeronave.

---

## P3 — "Qual companhia entrega melhor pontualidade e menor taxa de cancelamento, controlando por porte de operação?"

### Antes: divergiu

O agente interpretou **"porte de operação" como tipo de linha** e agrupou por
`nome_companhia, descricao_tipo_linha`:

```sql
GROUP BY nome_companhia, descricao_tipo_linha
HAVING COUNT(*) >= 10000
ORDER BY descricao_tipo_linha, pct_pontuais DESC, pct_cancelados ASC
```

A resposta não é absurda — é até útil (mostra a GOL liderando nos dois segmentos) — mas
**não é a que o gabarito responde**, e "porte" ali significa outra coisa. Divergência de
semântica, não de SQL: a query estava correta para a pergunta que ele entendeu.

### Correção aplicada

```
PORTE DE OPERACAO significa VOLUME DE VOOS, medido por COUNT(*). "Controlando por porte"
quer dizer aplicar o corte minimo de volume no HAVING, e nada mais. NAO interprete porte
como tipo de linha, escopo do voo ou tamanho de aeronave.
```

### Depois: ✅

SQL equivalente ao `sql/gabarito/P3.sql` (única diferença: `try_divide` também no
percentual de cancelamento, que é mais defensivo que o gabarito). Números idênticos:

| companhia | voos | % cancelados | % pontuais |
|---|---:|---:|---:|
| GOL | 259.303 | 1,13 | 86,06 |
| AZUL | 284.141 | 1,55 | 85,79 |
| AZUL CONECTA | 14.530 | **14,35** | 84,40 |
| TAP | 10.422 | 1,43 | 59,23 |

E a resposta em texto faz a leitura certa: *"a LATAM tem a menor taxa de cancelamento
(0,64%), mas pontualidade inferior à da GOL"* — exatamente o trade-off que a pergunta
pede.

---

## P4 — "Voos internacionais atrasam mais que domésticos? Quanto, e em quais aeroportos?"

### Antes: divergiu

Foi direto para o recorte por aeroporto, sem responder a comparação agregada primeiro, e
**deixou aeroporto estrangeiro entrar no ranking**:

```
AEROPORTO FORA DO CADASTRO ANAC (LPPT): 26,21 min, 54,52% atrasados
AEROPORTO FORA DO CADASTRO ANAC (SABE): 13,47 min, 23,05%
```

Não está errado — Lisboa realmente aparece no VRA como origem de voos com destino ao
Brasil. Mas a pergunta é sobre a operação brasileira, e um ranking liderado por
"AEROPORTO FORA DO CADASTRO ANAC" é ruim de ler e leva o cliente à conclusão errada.

Além disso filtrou `atraso_partida_min IS NOT NULL`, o que muda a contagem de voos
(99.664 contra 103.348 do gabarito) sem mudar a média.

### Correção aplicada

```
QUANDO A PERGUNTA CITA AEROPORTOS SEM DIZER O PAIS, considere apenas aeroportos
brasileiros: use pais_origem = 'Brasil'. Aeroporto estrangeiro aparece com o nome
AEROPORTO FORA DO CADASTRO ANAC e nao deve liderar um ranking sobre o Brasil.

COMPARACAO DOMESTICO x INTERNACIONAL: comece pelo agregado por escopo_voo, que e a
resposta direta da pergunta. So depois, se a pergunta pedir "em quais aeroportos", abra
por aeroporto de origem brasileiro.
```

### Depois: ✅

SQL idêntico ao `sql/gabarito/P4.sql`:

| escopo | voos | atraso médio | % atrasados |
|---|---:|---:|---:|
| Doméstico | 819.236 | 5,13 | 15,86 |
| Internacional | 195.428 | 19,36 | 25,37 |

E o texto agora encerra com: *"os dados apresentados são agregados por escopo de voo; para
saber em quais aeroportos isso ocorre, é necessário solicitar uma análise por aeroporto de
origem brasileiro"* — o agente passou a **dizer o que ficou de fora**, que era o
comportamento pedido na instrução.

---

## P5 — "Quanto atraso as companhias recuperam em voo, e em que rotas isso não acontece?"

### Antes: parcial

SQL **idêntico** ao `sql/gabarito/P5.sql` e resultado idêntico (TAP 9,79 min no topo,
LATAM 2,26 na base). Mas a segunda metade da pergunta — "em que rotas isso não acontece" —
foi simplesmente ignorada, sem aviso.

### Depois: ✅ na primeira dimensão, e o follow-up bate com o P5b

A resposta de companhias continua idêntica ao gabarito. Perguntando a segunda dimensão em
seguida ("Em quais rotas a recuperação em voo não acontece?"), o SQL sai idêntico ao
`sql/gabarito/P5b.sql`:

| rota | atraso saída | atraso chegada | recuperados |
|---|---:|---:|---:|
| CAMPO GRANDE - GUARULHOS | 4,37 | 8,54 | **−4,17** |
| FLORIANÓPOLIS - GUARULHOS | 8,40 | 9,46 | −1,06 |
| NAVEGANTES - GUARULHOS | 5,31 | 6,29 | −0,98 |
| GOIÂNIA - GUARULHOS | 6,31 | 6,57 | −0,26 |

E o texto explica o sinal corretamente: *"a recuperação não acontece quando o valor médio
de minutos recuperados é negativo, indicando que os voos chegam mais atrasados do que
saíram"*. Essa frase é a descrição revisada do marco-09 voltando pela boca do agente — se
o `COMMENT` estivesse com a versão errada ("positivo indica que chegou adiantado"), esta
resposta estaria errada.

**Pendência menor:** na P5 o agente não avisou que a segunda dimensão ficou de fora
(fez isso na P4, não fez aqui). A instrução está escrita; o comportamento é inconsistente
entre perguntas. Não invalida a resposta, mas vale citar em aula como limite real do
método: instruction reduz erro, não garante determinismo.

---

## O que este teste prova (e o que não prova)

**Prova:** as 5 perguntas de negócio do projeto são respondidas pelo agente com SQL
equivalente ao gabarito e números idênticos, sobre uma tabela só, sem join.

**Não prova:** que o agente vai acertar qualquer pergunta. Ele errou 3 de 5 na primeira
rodada — e os três erros foram de **semântica de negócio**, não de SQL. Foi por isso que
todas as correções couberam nas instructions.

É esse o trabalho de quem entrega um produto de dados para IA: a tabela é metade; a outra
metade é escrever, em português, o que a empresa quer dizer.
