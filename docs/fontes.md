# Fontes de dados — VoeBem Analytics

Gerado por `scripts/baixar_anac.py`. Portal: <https://sistemas.anac.gov.br/dadosabertos/>

> **Repositório correto.** A ANAC mantém dois repositórios de VRA. O de `www.gov.br`
> está **descontinuado** (congelado em out/2024, 11 colunas). Este projeto usa
> exclusivamente `sistemas.anac.gov.br/dadosabertos`, para onde o link oficial
> "Arquivos (CSV)" redireciona (HTTP 302).

| conjunto | arquivo | bytes | sha256 (16) | baixado em | URL de origem |
|---|---|---:|---|---|---|
| vra | `VRA_20258.csv` | 12,040,470 | `9602616d997156a6` | 2026-08-31 01:43 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2025/08 - Agosto/VRA_20258.csv> |
| vra | `VRA_20259.csv` | 11,667,147 | `369986ec8065cfce` | 2026-08-31 01:43 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2025/09 - Setembro/VRA_20259.csv> |
| vra | `VRA_202510.csv` | 12,146,027 | `5901915494a4e44b` | 2026-08-31 01:43 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2025/10 - Outubro/VRA_202510.csv> |
| vra | `VRA_202511.csv` | 11,636,410 | `af2b7cee2cbcc963` | 2026-08-31 01:43 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2025/11 - Novembro/VRA_202511.csv> |
| vra | `VRA_202512.csv` | 12,528,987 | `4e38f9d150b512f8` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2025/12 - Dezembro/VRA_202512.csv> |
| vra | `VRA_20261.csv` | 13,008,603 | `c0a129a7cab311d1` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2026/01 - Janeiro/VRA_20261.csv> |
| vra | `VRA_20262.csv` | 11,280,038 | `d10e17ac6583f590` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2026/02 - Fevereiro/VRA_20262.csv> |
| vra | `VRA_20263.csv` | 12,370,457 | `90a9c707251eeabc` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2026/03 - Março/VRA_20263.csv> |
| vra | `VRA_20264.csv` | 11,402,926 | `0c467640b54bcc69` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2026/04 - Abril/VRA_20264.csv> |
| vra | `VRA_20265.csv` | 11,655,230 | `a9927560246e6206` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2026/05 - Maio/VRA_20265.csv> |
| vra | `VRA_20266.csv` | 11,496,087 | `686843d225da4f04` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2026/06 - Junho/VRA_20266.csv> |
| vra | `VRA_20267.csv` | 12,691,900 | `2cd8ceb8be13dbc7` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)/2026/07 - Julho/VRA_20267.csv> |
| referencias | `AerodromosPublicos.csv` | 101,163 | `322aa0905f44ce87` | 2026-08-31 01:44 UTC | <https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aeródromos Públicos/Lista de aeródromos públicos/AerodromosPublicos.csv> |
| referencias | `pda_empresas_aereas_nacionais.csv` | 212,216 | `15bc62fee5e0dfbc` | 2026-08-31 01:53 UTC | <https://sistemas.anac.gov.br/dadosabertos/Operador Aéreo/Empresas Aereas Nacionais/pda_empresas_aereas_nacionais.csv> |
| referencias | `pda_empresas_aereas_estrangeiros.csv` | 38,186 | `35745185b80352fe` | 2026-08-31 01:45 UTC | <https://sistemas.anac.gov.br/dadosabertos/Operador Aéreo/Empresas Aereas Estrangeiras/pda_empresas_aereas_estrangeiros.csv> |

**Total:** 15 arquivos, 137.6 MB.

## Armadilhas do caminho

- O mês no **nome do arquivo** não tem zero à esquerda (`VRA_20258.csv`), mas o mês
  na **pasta** tem (`08 - Agosto`). Misturar os dois dá 404.
- A URL tem espaços e acentos (`Voos e operações aéreas`) — precisa de percent-encoding.
- A primeira linha do CSV **não é o cabeçalho**: é `Atualizado em: <data>`.
- **`pda_empresas_aereas_nacionais.csv` tem duas cópias no portal.** A da raiz de
  `Operador Aéreo/` está corrompida na origem (144 MB, exportação aninhada e
  repetida). A boa está na subpasta `Empresas Aereas Nacionais/` (212 KB) e tem
  exatamente o mesmo schema do arquivo de estrangeiras. Consulte as observações sobre a fonte acima.
