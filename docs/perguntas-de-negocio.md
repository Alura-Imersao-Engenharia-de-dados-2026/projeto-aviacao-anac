# Perguntas de negócio — VoeBem Analytics

A VoeBem Analytics é contratada por agências de viagem e seguradoras para responder:
**quais voos, companhias e rotas mais atrasam no Brasil, e por quê?**

Todo o pipeline existe para responder estas cinco perguntas. Elas são o critério de
sucesso do projeto — não "o pipeline rodou", mas "o produto de dados responde".

| id | pergunta | o que exige do modelo |
|----|----------|------------------------|
| **P1** | Quais rotas e aeroportos concentram os maiores atrasos de partida no Brasil? | atraso de partida em minutos + nome do aeroporto de origem/destino |
| **P2** | Como o atraso evolui ao longo do dia — quanto do atraso noturno é herdado da manhã? | hora prevista de partida + atraso médio por hora |
| **P3** | Qual companhia entrega melhor pontualidade e menor taxa de cancelamento, controlando por porte de operação? | nome da companhia + flag de pontualidade + situação do voo + volume de etapas |
| **P4** | Voos internacionais atrasam mais que domésticos? Quanto, e em quais aeroportos? | tipo de linha por extenso + atraso + aeroporto |
| **P5** | Quanto atraso as companhias recuperam em voo, e em que rotas isso não acontece? | minutos recuperados em voo (atraso de partida − atraso de chegada) |

## O "por quê": fator medido, não motivo declarado

A coluna `Código Justificativa` do VRA existe no schema, mas está **100% `N/A` desde
abril de 2020** — a própria ANAC documenta: *"Este campo deixou de ser exigido a partir
de abril de 2020, com a revogação da Instrução de Aviação Civil (IAC) 1504."*

Consequência de escopo, decidida antes da primeira linha de código: o projeto responde
**onde, quando e quanto** com precisão, e explica o atraso por **fatores medidos**
(hora do dia, tipo de linha, dia da semana, aeroporto, companhia) em vez do motivo
auto-declarado pela companhia. É mais próximo do que analytics de aviação faz de verdade.

## Critério de aceitação

O Genie Agent responde corretamente às 5 perguntas, com SQL correto e **nomes legíveis**
(companhias e aeroportos por nome, não por código ICAO). Cada resposta do Genie é
conferida contra uma query SQL escrita à mão (o gabarito do marco-08).
