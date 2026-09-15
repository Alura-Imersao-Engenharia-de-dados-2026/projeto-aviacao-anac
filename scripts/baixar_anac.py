"""
Baixa do portal de dados abertos da ANAC os arquivos do projeto VoeBem Analytics.

Fonte: https://sistemas.anac.gov.br/dadosabertos/  (repositorio ATUAL)
NAO usar o repositorio de www.gov.br — descontinuado, congelado em out/2024.

Uso:  python scripts/baixar_anac.py
Saida: dados/vra/*.csv, dados/referencias/*.csv e docs/fontes.md
"""
import hashlib
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone

RAIZ = pathlib.Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "dados"
VRA_BASE = "https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)"

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# janela de 12 meses: ago/2025 -> jul/2026
JANELA = [(2025, m) for m in range(8, 13)] + [(2026, m) for m in range(1, 8)]

REFERENCIAS = {
    "AerodromosPublicos.csv":
        "https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aeródromos Públicos/"
        "Lista de aeródromos públicos/AerodromosPublicos.csv",
    # ATENCAO: NAO usar .../Operador Aéreo/pda_empresas_aereas_nacionais.csv (raiz da pasta).
    # Esse arquivo esta CORROMPIDO na origem: 144 MB de exportacao aninhada e repetida,
    # com 646 empresas reais multiplicadas em ~461 mil linhas. Consulte docs/fontes.md.
    # O arquivo bom fica na SUBPASTA "Empresas Aereas Nacionais/" — 212 KB, mesmo schema
    # do arquivo de estrangeiras.
    "pda_empresas_aereas_nacionais.csv":
        "https://sistemas.anac.gov.br/dadosabertos/Operador Aéreo/"
        "Empresas Aereas Nacionais/pda_empresas_aereas_nacionais.csv",
    "pda_empresas_aereas_estrangeiros.csv":
        "https://sistemas.anac.gov.br/dadosabertos/Operador Aéreo/"
        "Empresas Aereas Estrangeiras/pda_empresas_aereas_estrangeiros.csv",
}


def url_vra(ano: int, mes: int) -> str:
    # ATENCAO: o mes no NOME DO ARQUIVO nao tem zero a esquerda (VRA_20258.csv),
    # mas o mes na PASTA tem (08 - Agosto). Errar isso da 404.
    pasta = f"{mes:02d} - {MESES[mes - 1]}"
    return f"{VRA_BASE}/{ano}/{pasta}/VRA_{ano}{mes}.csv"


def baixar(url: str, destino: pathlib.Path, pular_se_existe: bool = True) -> dict:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if pular_se_existe and destino.exists():
        conteudo = destino.read_bytes()
        return {
            "url": url, "arquivo": destino.name, "status": "cache",
            "bytes": len(conteudo),
            "sha256": hashlib.sha256(conteudo).hexdigest()[:16],
            "baixado_em": datetime.fromtimestamp(
                destino.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
    # quote com safe='/:' preserva a estrutura e escapa espacos e acentos
    url_encoded = urllib.parse.quote(url, safe="/:?=&")
    req = urllib.request.Request(url_encoded, headers={"User-Agent": "VoeBem-Analytics/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        conteudo = resp.read()
        status = resp.status
    destino.write_bytes(conteudo)
    return {
        "url": url,
        "arquivo": destino.name,
        "status": status,
        "bytes": len(conteudo),
        "sha256": hashlib.sha256(conteudo).hexdigest()[:16],
        "baixado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def main() -> None:
    registros = []
    for ano, mes in JANELA:
        url = url_vra(ano, mes)
        alvo = DESTINO / "vra" / f"VRA_{ano}{mes}.csv"
        info = baixar(url, alvo)
        info["conjunto"] = "vra"
        registros.append(info)
        print(f"[vra]  {info['arquivo']:<18} {info['status']}  {info['bytes']:>10,} bytes")

    for nome, url in REFERENCIAS.items():
        alvo = DESTINO / "referencias" / nome
        info = baixar(url, alvo)
        info["conjunto"] = "referencias"
        registros.append(info)
        print(f"[ref]  {info['arquivo']:<38} {info['status']}  {info['bytes']:>10,} bytes")

    total = sum(r["bytes"] for r in registros)
    print(f"\n{len(registros)} arquivos, {total / 1024 / 1024:.1f} MB")

    linhas = [
        "# Fontes de dados — VoeBem Analytics",
        "",
        "Gerado por `scripts/baixar_anac.py`. Portal: <https://sistemas.anac.gov.br/dadosabertos/>",
        "",
        "> **Repositório correto.** A ANAC mantém dois repositórios de VRA. O de `www.gov.br`",
        "> está **descontinuado** (congelado em out/2024, 11 colunas). Este projeto usa",
        "> exclusivamente `sistemas.anac.gov.br/dadosabertos`, para onde o link oficial",
        "> \"Arquivos (CSV)\" redireciona (HTTP 302).",
        "",
        "| conjunto | arquivo | bytes | sha256 (16) | baixado em | URL de origem |",
        "|---|---|---:|---|---|---|",
    ]
    for r in registros:
        linhas.append(
            f"| {r['conjunto']} | `{r['arquivo']}` | {r['bytes']:,} | `{r['sha256']}` | "
            f"{r['baixado_em']} | <{r['url']}> |"
        )
    linhas += [
        "",
        f"**Total:** {len(registros)} arquivos, {total / 1024 / 1024:.1f} MB.",
        "",
        "## Armadilhas do caminho",
        "",
        "- O mês no **nome do arquivo** não tem zero à esquerda (`VRA_20258.csv`), mas o mês",
        "  na **pasta** tem (`08 - Agosto`). Misturar os dois dá 404.",
        "- A URL tem espaços e acentos (`Voos e operações aéreas`) — precisa de percent-encoding.",
        "- A primeira linha do CSV **não é o cabeçalho**: é `Atualizado em: <data>`.",
        "- **`pda_empresas_aereas_nacionais.csv` tem duas cópias no portal.** A da raiz de",
        "  `Operador Aéreo/` está corrompida na origem (144 MB, exportação aninhada e",
        "  repetida). A boa está na subpasta `Empresas Aereas Nacionais/` (212 KB) e tem",
        "  exatamente o mesmo schema do arquivo de estrangeiras. Consulte as observações sobre a fonte acima.",
    ]
    (RAIZ / "docs" / "fontes.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("docs/fontes.md gerado")


if __name__ == "__main__":
    main()
