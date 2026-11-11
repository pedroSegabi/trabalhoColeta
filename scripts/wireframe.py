"""Gera os esboços (wireframes) das duas telas do dashboard.

Uso:  python scripts/wireframe.py
Saída: relatorios/wireframe_tela1.png, relatorios/wireframe_tela2.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SAIDA = Path(__file__).resolve().parents[1] / "relatorios"
CINZA, AZUL, AMARELO, VERDE = "#eceff1", "#dbe9f6", "#fff4cc", "#e3f1e4"


def caixa(ax, x, y, w, h, titulo, detalhe="", cor=CINZA):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.8",
                                fc=cor, ec="#607d8b", lw=1.2))
    ax.text(x + w / 2, y + h / 2 + (1.2 if detalhe else 0), titulo, ha="center", va="center",
            fontsize=11, weight="bold", wrap=True)
    if detalhe:
        ax.text(x + w / 2, y + h / 2 - 1.6, detalhe, ha="center", va="center", fontsize=8.5,
                color="#37474f", wrap=True)


def tela(nome, titulo, blocos):
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 64)
    ax.axis("off")
    ax.text(1, 62, titulo, fontsize=15, weight="bold", va="top")
    for b in blocos:
        caixa(ax, *b)
    fig.savefig(SAIDA / nome, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(f"ok: relatorios/{nome}")


def main():
    SAIDA.mkdir(exist_ok=True)
    tela("wireframe_tela1.png", "Tela 1 — Se o Guaíba chegar a X metros, quais bairros e quantas pessoas são afetados?", [
        (1, 52, 98, 6, "Nível do Guaíba:  3,0 m  ━━━━━━━●━━━━━━━━━━━━  10,0 m   (passo 0,1 m)",
         "controle deslizante — atualiza todos os elementos da tela", AZUL),
        (1, 42, 31, 7, "Pessoas afetadas (estimativa)", "ex.: 136.389 a 5,3 m"),
        (35, 42, 30, 7, "Prédios afetados", "soma do nível escolhido"),
        (68, 42, 31, 7, "Bairros atingidos", "bairros com ≥ 1 prédio afetado"),
        (1, 21, 48, 18, "% de prédios afetados por bairro", "barras horizontais, só bairros atingidos, ordenadas"),
        (52, 21, 47, 18, "Mapa dos bairros (opcional)", "malha oficial ObservaPOA, cor = % de prédios afetados"),
        (1, 6, 48, 12, "Curva: população afetada × nível do rio",
         "linha vertical em 5,35 m (recorde de maio/2024) + ponto no nível escolhido"),
        (52, 6, 47, 12, "Ranking dos bairros mais afetados", "tabela top 10: bairro, % prédios, pessoas"),
        (1, 0, 98, 3.5, "⚠ Estimativas de uma simulação — não são previsão nem contagem oficial. População distribuída "
         "igualmente entre todos os prédios (OSM). Dados corrigidos: ver relatório de limpeza.", "", AMARELO),
    ])
    tela("wireframe_tela2.png", "Tela 2 — O que a enchente real de 2024 acrescenta à simulação? (IBGE × manchas MUP e INPE/ANA)", [
        (1, 52, 98, 6, "Filtros:  [Mancha: SPGG/MUP ▾ | INPE/ANA]   [Indicador: pessoas ▾ | domicílios | escolas | saúde]"
         "   [Município: buscar…]", "o filtro atualiza os gráficos da tela", AZUL),
        (1, 42, 23, 7, "Pessoas na área afetada (RS)"),
        (26, 42, 23, 7, "Municípios atingidos"),
        (51, 42, 23, 7, "Escolas na área afetada"),
        (76, 42, 23, 7, "Unidades de saúde atingidas"),
        (1, 21, 48, 18, "Top 15 municípios pelo indicador", "barras horizontais"),
        (52, 21, 47, 18, "% da população do município na área afetada", "top 15 — municípios pequenos aparecem"),
        (1, 6, 48, 12, "Porto Alegre: simulação × observado em 2024",
         "INCT no nível da Tela 1 (5,3 m) × mancha MUP (122.663) × INPE/ANA (152.258)", VERDE),
        (52, 6, 47, 12, "Escolas e unidades de saúde atingidas", "barras empilhadas por município"),
        (1, 0, 98, 3.5, "Fontes: IBGE, Dados agregados para as áreas afetadas (ftp.ibge.gov.br/…/apoio_rs) — "
         "manchas SPGG-RS 15/05/2024 e INPE/ANA v3 19/06/2024 — data de coleta exibida aqui", "", AMARELO),
    ])


if __name__ == "__main__":
    main()
