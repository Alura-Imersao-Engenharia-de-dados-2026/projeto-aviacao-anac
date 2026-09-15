"""Monta genie/genie_space.json a partir das queries gabarito e de genie/instrucoes.md.

Assim as example queries do Genie SAO, literalmente, o gabarito do marco-08:
se o gabarito mudar, o espaco muda junto. Rode:

    python scripts/montar_genie_space.py
"""
import io
import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TABELA = "voebem.gold.obt_voos"

PERGUNTAS = [
    ("P1",  "Quais aeroportos do Brasil concentram os maiores atrasos de partida?"),
    ("P1b", "Quais rotas domesticas tem o maior atraso medio de partida?"),
    ("P2",  "Como o atraso de partida evolui ao longo do dia?"),
    ("P3",  "Qual companhia entrega a melhor pontualidade e a menor taxa de cancelamento?"),
    ("P4",  "Voos internacionais atrasam mais que domesticos? Quanto?"),
    ("P4b", "Em quais aeroportos brasileiros a diferenca de atraso entre internacional e domestico e maior?"),
    ("P5",  "Quanto atraso as companhias recuperam em voo?"),
    ("P5b", "Em quais rotas a recuperacao em voo nao acontece?"),
]

# as 5 perguntas de negocio, como o usuario as faria
SAMPLE_QUESTIONS = [
    "Quais aeroportos e rotas concentram os maiores atrasos de partida no Brasil?",
    "Como o atraso evolui ao longo do dia?",
    "Qual companhia entrega melhor pontualidade e menor taxa de cancelamento?",
    "Voos internacionais atrasam mais que domesticos? Em quais aeroportos a diferenca e maior?",
    "Quanto atraso as companhias recuperam em voo, e em que rotas isso nao acontece?",
]


def hexid(prefixo: int, n: int) -> str:
    """32 hex chars: prefixo por lista + contador. Ordem de autoria = ordem de sort."""
    return f"{prefixo}" + f"{n:031d}"


def ler_sql(nome: str) -> list[str]:
    caminho = RAIZ / "sql" / "gabarito" / f"{nome}.sql"
    linhas = io.open(caminho, encoding="utf-8").read().splitlines(keepends=True)
    # descarta os comentarios de cabecalho: o Genie quer a query, nao o didatismo
    return [l for l in linhas if not l.lstrip().startswith("--")]


def ler_instrucoes() -> list[str]:
    texto = io.open(RAIZ / "genie" / "instrucoes.md", encoding="utf-8").read()
    corpo = texto.split("---\n", 1)[1].strip()
    return [l + "\n" for l in corpo.splitlines()]


espaco = {
    "version": 2,
    "config": {
        "sample_questions": [
            {"id": hexid(1, i), "question": [q]} for i, q in enumerate(SAMPLE_QUESTIONS, start=1)
        ]
    },
    "data_sources": {"tables": [{"identifier": TABELA}]},
    "instructions": {
        "example_question_sqls": [
            {"id": hexid(2, i), "question": [pergunta], "sql": ler_sql(nome)}
            for i, (nome, pergunta) in enumerate(PERGUNTAS, start=1)
        ],
        "text_instructions": [{"id": hexid(3, 1), "content": ler_instrucoes()}],
    },
}

destino = RAIZ / "genie" / "genie_space.json"
io.open(destino, "w", encoding="utf-8").write(json.dumps(espaco, indent=2, ensure_ascii=False) + "\n")
print(f"{destino} escrito: {len(SAMPLE_QUESTIONS)} sample questions, "
      f"{len(PERGUNTAS)} example queries, 1 bloco de instrucoes")
