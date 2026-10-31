import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pypdf

from src.config import DATA_DIR

POLICY_SECTIONS: Dict[str, Dict[str, Any]] = {
    "sobre_e_endereco": {
        "title": "Sobre a Loja, Endereço e Dados Cadastrais",
        "keywords": ["endereço", "endereco", "onde fica", "localização", "localizacao", "cnpj", "telefone", "contato", "cidade", "campo grande", "sobre"],
        "content": (
            "EMPRÓRIO DA MÚSICA - Dados Cadastrais e Localização:\n"
            "- Razão Social: Empório da Música Instrumentos Musicais Ltda.\n"
            "- CNPJ: 12.345.678/0001-90 | Fundação: 2008 (mais de 15 anos de história).\n"
            "- Endereço Físico: Rua 14 de Maio, 3200 – Centro, Campo Grande - MS, CEP: 79202-333.\n"
            "- Telefone / WhatsApp: (67) 3341-4444 / (67) 3321-4500 | E-mail: contato@emporiodamusica.com.br.\n"
            "- Missão: Democratizar o acesso a instrumentos musicais de qualidade na região Centro-Oeste."
        )
    },
    "horario_funcionamento": {
        "title": "Horário de Funcionamento",
        "keywords": ["horário", "horario", "aberto", "funciona", "expediente", "sábado", "sabado", "domingo", "feriado", "atendimento"],
        "content": (
            "HORÁRIO DE FUNCIONAMENTO (Presencial e WhatsApp):\n"
            "- Segunda a Sexta-feira: 09:00 às 18:00.\n"
            "- Sábado: 09:00 às 13:00.\n"
            "- Domingos e Feriados: Fechado.\n"
            "- Datas Especiais (Black Friday, Aniversário da Loja, Natal): horários estendidos divulgados previamente nas redes sociais e WhatsApp.\n"
            "- Fora do expediente, o assistente virtual orienta sobre o retorno no próximo dia útil."
        )
    },
    "formas_pagamento": {
        "title": "Formas de Pagamento e Condições de Parcelamento",
        "keywords": ["pagamento", "pagar", "pix", "cartão", "cartao", "crédito", "credito", "débito", "debito", "parcelamento", "parcelas", "juros", "boleto", "desconto"],
        "content": (
            "FORMAS DE PAGAMENTO ACEITAS (Presencial e Online):\n"
            "1. PIX: Pagamento à vista com 5% DE DESCONTO sobre o preço de tabela (desconto não cumulativo com produtos já em promoção).\n"
            "2. Cartão de Débito: Pagamento à vista, todas as bandeiras aceitas.\n"
            "3. Cartão de Crédito: Até 12x SEM JUROS. Regras de parcelamento:\n"
            "   - Até 3x sem juros (sem parcela mínima, exceto compras abaixo de R$ 50).\n"
            "   - De 4x a 6x sem juros: parcela mínima de R$ 80,00.\n"
            "   - De 7x a 12x sem juros: parcela mínima de R$ 100,00.\n"
            "4. Boleto Bancário: Pagamento à vista, compensação em até 3 dias úteis.\n"
            "5. Combinação de Pagamentos: permitida combinação (ex.: PIX + cartão) para compras acima de R$ 2.000,00."
        )
    },
    "trocas_e_devolucoes": {
        "title": "Política de Trocas, Devoluções e Arrependimento (CDC)",
        "keywords": ["troca", "trocar", "devolução", "devolucao", "devolver", "arrependimento", "arrependi", "cancelar", "estorno", "reembolso", "defeito", "quebrado", "danificado"],
        "content": (
            "POLÍTICA DE TROCAS E DEVOLUÇÕES (Conforme Código de Defesa do Consumidor - Lei nº 8.078/90):\n"
            "1. Direito de Arrependimento (Compras Online / WhatsApp):\n"
            "   - O cliente pode solicitar devolução em até 7 (SETE) DIAS CORRIDOS após receber o produto, sem necessidade de justificativa.\n"
            "   - Requisitos: produto na embalagem original, sem sinais de uso, acompanhado de todos os acessórios e manuais.\n"
            "   - Frete de devolução: 100% POR CONTA DA LOJA em caso de arrependimento no prazo legal.\n"
            "   - Reembolso integral na mesma forma de pagamento original em até 10 dias úteis após recebimento na loja.\n"
            "2. Troca por Defeito de Fabricação:\n"
            "   - Prazo de até 30 (TRINTA) DIAS CORRIDOS diretamente com a loja. Após 30 dias, deve acionar a garantia do fabricante.\n"
            "   - Não cobre defeitos causados por mau uso, quedas, umidade excessiva ou regulagens/modificações não autorizadas.\n"
            "3. Troca por Preferência (cor, modelo, tamanho):\n"
            "   - Permitida em até 7 dias, condicionada à disponibilidade em estoque e embalagem perfeita/lacrada.\n"
            "4. ITENS NÃO ELEGÍVEIS PARA TROCA:\n"
            "   - Instrumentos personalizados ou com ajustes sob encomenda (setup, regulagem customizada).\n"
            "   - Produtos adquiridos em queima de estoque com aviso explícito de 'venda final'.\n"
            "   - Boquilhas de instrumentos de sopro (por questões sanitárias e de higiene)."
        )
    },
    "frete_e_entregas": {
        "title": "Política de Frete, Prazos de Entrega e Rastreamento",
        "keywords": ["frete", "entrega", "prazo", "enviar", "envio", "rastreio", "rastreamento", "transportadora", "correios", "sedex", "pac", "jadlog", "motoboy", "campo grande"],
        "content": (
            "POLÍTICA DE FRETE E ENTREGAS:\n"
            "1. Região Metropolitana de Campo Grande/MS:\n"
            "   - FRETE GRÁTIS para pedidos acima de R$ 500,00.\n"
            "   - Taxa fixa de R$ 35,00 para pedidos abaixo de R$ 500,00.\n"
            "   - Prazo: 1 a 3 dias úteis (entrega por motoboy próprio, com contato telefônico prévio).\n"
            "2. Outras Cidades e Estados:\n"
            "   - PAC (Correios): 5 a 12 dias úteis (com rastreamento e seguro incluso).\n"
            "   - SEDEX (Correios): 2 a 5 dias úteis (com rastreamento e seguro incluso).\n"
            "   - Jadlog (.package): 3 a 8 dias úteis (com rastreamento e seguro incluso).\n"
            "   - Instrumentos de grande porte (baterias acústicas, pianos digitais) podem exigir frete especial.\n"
            "3. Código de Rastreamento:\n"
            "   - Enviado por e-mail e WhatsApp assim que despachado. Formato padrão: BR + 9 dígitos alfanuméricos + BR (Ex: BR4K7M2X9P1BR)."
        )
    },
    "escopo_e_produtos": {
        "title": "Escopo de Produtos da Loja (O que vendemos e o que NÃO vendemos)",
        "keywords": ["acessório", "acessorio", "acessórios", "cordas", "palheta", "palhetas", "cabo", "cabos", "pedal", "pedais", "amplificador", "amplificadores", "case", "cases", "capa", "afinador"],
        "content": (
            "ESCOPO E CATÁLOGO DE PRODUTOS DA LOJA:\n"
            "- A Empório da Música comercializa EXCLUSIVAMENTE INSTRUMENTOS MUSICAIS (guitarras, baixos, violões, baterias, teclados, pianos, instrumentos de sopro, cordas orquestrais e ukuleles).\n"
            "- A LOJA NÃO COMERCIALIZA ACESSÓRIOS como cordas avulsas, palhetas, cabos, cases, capas, pedais ou amplificadores.\n"
            "- Quando o cliente solicitar tais itens, o atendente deve informar educadamente que a loja trabalha focada exclusivamente nos instrumentos e indicar lojas parceiras de acessórios."
        )
    },
    "garantia": {
        "title": "Política de Garantia",
        "keywords": ["garantia", "defeito", "fabricante", "tempo de garantia", "cobertura", "assistência", "assistencia"],
        "content": (
            "POLÍTICA DE GARANTIA:\n"
            "1. Garantia Legal (CDC): 90 (noventa) dias contra defeitos de fabricação a partir da data de recebimento.\n"
            "2. Garantia do Fabricante: Varia de 6 meses a 2 anos dependendo da marca (especificada no certificado de cada produto).\n"
            "3. O que NÃO é coberto pela garantia:\n"
            "   - Desgaste natural de peças (trastes, cordas, feltros, palhetas de sopro).\n"
            "   - Danos por mau uso, quedas ou exposição a condições climáticas extremas (umidade, calor excessivo).\n"
            "   - Modificações, regulagens ou reparos realizados por terceiros não autorizados."
        )
    },
    "privacidade_lgpd": {
        "title": "Privacidade e Proteção de Dados (LGPD)",
        "keywords": ["lgpd", "privacidade", "dados", "excluir dados", "segurança", "compartilhamento", "remover dados"],
        "content": (
            "CONFORMIDADE COM A LGPD (Lei nº 13.709/2018):\n"
            "- Dados coletados durante o atendimento (nome, telefone, e-mail) destinam-se exclusivamente à localização de pedidos e entregas.\n"
            "- Não compartilhamos dados com terceiros para fins de marketing.\n"
            "- Retenção padrão do histórico de conversa: 7 dias corridos.\n"
            "- O cliente pode solicitar a exclusão de seus dados a qualquer momento entrando em contato pelo WhatsApp ou e-mail."
        )
    }
}

def get_all_policy_sections() -> Dict[str, Dict[str, Any]]:
    """Retorna todas as seções de políticas registradas."""
    return POLICY_SECTIONS

def consult_policies(topic_or_query: str) -> str:
    """
    Busca nas políticas internas da loja as regras pertinentes à dúvida do cliente.
    Retorna o trecho normativo correspondente para orientar a resposta da IA.
    """
    if not topic_or_query:
        # Retorna resumo das principais diretrizes
        return "\n\n".join([sec["content"] for sec in POLICY_SECTIONS.values() if sec in ("sobre_e_endereco", "horario_funcionamento", "formas_pagamento", "trocas_e_devolucoes")])

    query_norm = topic_or_query.lower()
    matches: List[tuple[int, str]] = []

    for key, data in POLICY_SECTIONS.items():
        score = 0
        # Checagem por título e chave
        if key in query_norm or any(w in query_norm for w in data["title"].lower().split()):
            score += 3

        # Checagem por palavras-chave mapeadas
        for kw in data["keywords"]:
            if kw in query_norm:
                score += 2

        # Checagem no conteúdo
        for term in query_norm.split():
            if len(term) > 3 and term in data["content"].lower():
                score += 1

        if score > 0:
            matches.append((score, data["content"]))

    if not matches:
        # Se nenhuma seção específica pontuar alto, retorna as mais comuns (pagamento, trocas, horários)
        return (
            "POLÍTICAS GERAIS DA EMPÓRIO DA MÚSICA:\n"
            + POLICY_SECTIONS["horario_funcionamento"]["content"] + "\n\n"
            + POLICY_SECTIONS["formas_pagamento"]["content"] + "\n\n"
            + POLICY_SECTIONS["trocas_e_devolucoes"]["content"]
        )

    # Ordena pelo maior score e combina as seções mais relevantes
    matches.sort(key=lambda x: x[0], reverse=True)
    selected_texts = [content for _, content in matches[:2]]
    return "\n\n".join(selected_texts)
