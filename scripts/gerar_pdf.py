"""Converte um relatório Markdown em PDF (Markdown -> HTML -> PDF via Chrome/Chromium headless).

Uso:  python scripts/gerar_pdf.py relatorios/limpeza_dados.md
O Chrome é procurado no PATH e no caminho padrão do macOS/Windows; defina CHROME=/caminho se necessário.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import mistune

CSS = """
body { font-family: -apple-system, Helvetica, Arial, sans-serif; font-size: 10.5pt; line-height: 1.45;
       color: #1b1b1b; max-width: 100%; margin: 0; }
h1 { font-size: 18pt; margin-bottom: 4pt; } h2 { font-size: 14pt; border-bottom: 1px solid #ccc;
padding-bottom: 2pt; margin-top: 18pt; } h3 { font-size: 12pt; } h4 { font-size: 11pt; margin-bottom: 2pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9pt; page-break-inside: avoid; }
th, td { border: 1px solid #c8c8c8; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #eef2f6; } code, pre { font-size: 8.5pt; background: #f4f4f4; }
pre { padding: 6pt; white-space: pre-wrap; } a { color: #1c5cab; }
@page { size: A4; margin: 16mm 14mm; }
"""
CANDIDATOS = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def achar_chrome():
    for c in [os.environ.get("CHROME")] + CANDIDATOS:
        if c and (shutil.which(c) or Path(c).exists()):
            return shutil.which(c) or c
    sys.exit("Chrome/Chromium não encontrado. Defina a variável CHROME com o caminho do executável.")


def main(md_path):
    md = Path(md_path)
    html, pdf = md.with_suffix(".html"), md.with_suffix(".pdf")
    corpo = mistune.create_markdown(plugins=["table"])(md.read_text(encoding="utf-8"))
    html.write_text(f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>{CSS}</style>"
                    f"</head><body>{corpo}</body></html>", encoding="utf-8")
    try:
        r = subprocess.run([achar_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={pdf.resolve()}", html.resolve().as_uri()],
                           timeout=120, capture_output=True, text=True)
    finally:
        html.unlink(missing_ok=True)
    if r.returncode != 0:  # o Chrome escreve avisos inofensivos no stderr; só mostra se falhou
        sys.exit(f"Chrome falhou (código {r.returncode}):\n{r.stderr}")
    print(f"ok: {pdf}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
