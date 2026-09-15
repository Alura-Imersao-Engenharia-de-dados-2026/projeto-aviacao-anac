"""Envia uma pergunta ao Genie Space e imprime status, SQL gerado e resultado.

Uso:
    python scripts/perguntar_genie.py "<pergunta>"

Cada chamada abre uma conversa NOVA: as 5 perguntas do teste de aceitacao sao
independentes, e conversa compartilhada faria o Genie herdar contexto da anterior.
"""
import os
import json
import subprocess
import sys
import time

PERFIL = os.environ.get("DATABRICKS_CONFIG_PROFILE", "alura-imersao")
SPACE = os.environ.get("GENIE_SPACE_ID")
if not SPACE:
    raise SystemExit("Defina a variavel GENIE_SPACE_ID com o ID do seu espaco Genie.")


def cli(*args: str) -> dict:
    saida = subprocess.run(
        ["databricks", *args, "-p", PERFIL, "-o", "json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if saida.returncode != 0:
        raise SystemExit(f"CLI falhou: {saida.stderr[:500]}")
    return json.loads(saida.stdout or "{}")


def perguntar(pergunta: str) -> None:
    inicio = cli("genie", "start-conversation", "--no-wait", SPACE, pergunta)
    conv, msg = inicio["conversation_id"], inicio["message_id"]
    print(f"conversation_id={conv}\nmessage_id={msg}")

    for _ in range(60):
        m = cli("genie", "get-message", SPACE, conv, msg)
        estado = m.get("status")
        print(f"  status={estado}")
        if estado in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(10)

    if m.get("error"):
        print("ERRO:", json.dumps(m["error"], ensure_ascii=False)[:600])

    for a in m.get("attachments", []):
        if a.get("text"):
            print("\n--- TEXTO ---\n" + a["text"]["content"])
        if a.get("query"):
            print("\n--- SQL ---\n" + a["query"]["query"])
            print("\n--- DESCRICAO ---\n" + (a["query"].get("description") or ""))
            res = cli("genie", "get-message-attachment-query-result",
                      SPACE, conv, msg, a["attachment_id"])
            st = res.get("statement_response", {})
            cols = [c["name"] for c in st.get("manifest", {}).get("schema", {}).get("columns", [])]
            linhas = st.get("result", {}).get("data_array", []) or []
            print("\n--- RESULTADO ---")
            print(" | ".join(cols))
            for linha in linhas[:15]:
                print(" | ".join("" if v is None else str(v) for v in linha))


if __name__ == "__main__":
    perguntar(sys.argv[1])
