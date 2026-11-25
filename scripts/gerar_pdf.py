"""Converte um relatório Markdown em PDF (Markdown -> HTML -> PDF via Chrome/Chromium headless).

Uso:  python scripts/gerar_pdf.py relatorios/limpeza_dados.md
O Chrome é procurado no PATH e no caminho padrão do macOS/Windows; defina CHROME=/caminho se necessário.

O que vem antes do primeiro "---" do Markdown vira a capa. Imagens sozinhas num parágrafo viram
"Figura N", com o texto alternativo como título.
"""
import html as h
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import mistune

CSS = """
@page { size: A4; margin: 25mm 20mm 22mm 25mm; @bottom-right { content: counter(page); font: 9pt Arial, sans-serif; } }
@page :first { @bottom-right { content: none; } }
body { margin: 0; font: 10.5pt/1.5 Arial, Helvetica, sans-serif; color: #111; text-align: justify; hyphens: auto; }
h1, h2, h3, h4 { line-height: 1.25; text-align: left; break-after: avoid; }
h2 { font-size: 13pt; margin: 22pt 0 8pt; } h3 { font-size: 11pt; margin: 14pt 0 6pt; } h4 { font-size: 10.5pt; }
p { margin: 0 0 8pt; orphans: 3; widows: 3; } ul, ol { margin: 0 0 8pt; padding-left: 18pt; } li { margin-bottom: 3pt; }
a { color: #1a4f8b; }
code { font: 9pt Menlo, Consolas, monospace; }
pre { font-size: 9pt; white-space: pre-wrap; border: 0.5pt solid #999; padding: 6pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 12pt; font-size: 9pt; line-height: 1.35; text-align: left; }
thead { display: table-header-group; } tr { break-inside: avoid; }
th, td { border: 0.5pt solid #888; padding: 3pt 5pt; vertical-align: top; } th { background: #eee; }
blockquote { margin: 8pt 0; padding: 4pt 10pt; border-left: 2pt solid #888; font-style: italic; }
blockquote p { margin: 0; }
figure { margin: 10pt 0 14pt; break-inside: avoid; text-align: center; }
figcaption { font-size: 9.5pt; margin-bottom: 4pt; text-align: center; }
figure img { max-width: 100%; max-height: 95mm; border: 0.5pt solid #999; }
.capa { height: 246mm; display: flex; flex-direction: column; text-align: center; break-after: page; }
.capa h1 { font-size: 18pt; margin: 70mm 0 10pt; }
.capa .sub { font-size: 12pt; }
.capa .meta { margin-top: auto; font-size: 10.5pt; } .capa .meta p { margin: 0 0 5pt; }
"""


def capa(md_capa, converter):
    """Título e subtítulo no meio da página; disciplina, equipe e data embaixo."""
    blocos = [b for b in converter(md_capa).strip().split("\n") if b.strip()]
    titulo, sub, meta = blocos[0], blocos[1:2], blocos[2:]
    sub = "".join(sub).replace("<p>", '<p class="sub">', 1)
    return f'<section class="capa">{titulo}{sub}<div class="meta">{"".join(meta)}</div></section>'


def corpo(md_corpo, converter):
    n = 0

    def figura(m):
        nonlocal n
        n += 1
        return f'<figure><figcaption>Figura {n} – {m[2]}</figcaption><img src="{m[1]}" alt="{m[2]}"></figure>'

    return re.sub(r'<p><img src="([^"]+)" alt="([^"]*)" ?/?></p>', figura, converter(md_corpo))


def main(md_path):
    md = Path(md_path)
    html, pdf = md.with_suffix(".html"), md.with_suffix(".pdf")
    converter = mistune.create_markdown(plugins=["table"])
    md_capa, _, md_corpo = md.read_text(encoding="utf-8").partition("\n---\n")
    titulo = re.search(r"^# (.+)$", md_capa, re.M)[1]
    html.write_text(f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>{h.escape(titulo)}</title>"
                    f"<style>{CSS}</style></head><body>{capa(md_capa, converter)}{corpo(md_corpo, converter)}"
                    f"</body></html>", encoding="utf-8")
    try:
        r = subprocess.run([achar_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={pdf.resolve()}", html.resolve().as_uri()],
                           timeout=120, capture_output=True, text=True)
    finally:
        html.unlink(missing_ok=True)
    if r.returncode != 0:  # o Chrome escreve avisos inofensivos no stderr; só mostra se falhou
        sys.exit(f"Chrome falhou (código {r.returncode}):\n{r.stderr}")
    print(f"ok: {pdf}")


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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
