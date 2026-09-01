import json
from datetime import datetime

def format_ai_dossier(products_list):
    """Formata os dados minerados em um relatório estruturado para o Agente de IA."""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    dossier = f"""# 📊 DOSSIÊ DE MINERAÇÃO TIKTOK SHOP BRASIL
**Data de Extração:** {timestamp}
**Nicho Principal:** Moda Feminina e Achadinhos para Casa
**Formato de Produção:** Vídeos com Influencer de IA (POV Silencioso + Música Viral + Headline)

---

## 🎯 INSTRUÇÃO PARA O AGENTE ANALISADOR DE PRODUTOS:
Atue como um Especialista em Viralização e Conversão no TikTok Shop Brasil.
Analise a lista de produtos minerados abaixo e execute:
1. **Definir o Produto Vencedor (Top 1)** com maior potencial de venda imediata e facilidade de geração visual em IA.
2. **Criar 5 Headlines de Alta Conversão** no formato POV / Curiosidade adaptadas para o público brasileiro.
3. **Descrever o Prompt Visual da Influencer de IA** (Cenário, expressão e como o produto deve ser exibido na mão ou no ambiente).

---

## 📦 PRODUTOS MINERADOS:

"""
    for p in products_list:
        dossier += f"""### [{p['id']}] {p['titulo_bruto']}
* **Categoria:** {p['categoria']}
* **Formato Sugerido:** {p['formato']}
* **Dados / Métricas:** {p['detalhes']}
* **Link de Referência:** {p['video_url'] or 'Visualizado no Viralyze'}
---
"""

    return dossier

def save_local_report(dossier_text, filename="relatorio_mineracao.md"):
    """Salva o dossiê em arquivo local para envio ao Drive ou cópia direta."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(dossier_text)
    return filename
  
