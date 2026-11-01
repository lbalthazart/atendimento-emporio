import json
from typing import Any, Dict, List

from src.database.queries import (
    get_order_status,
    get_product_by_id,
    list_active_promotions,
    list_categories,
    search_products,
)
from src.knowledge.policies import consult_policies

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_catalogo",
            "description": "Busca instrumentos musicais no catálogo da loja por nome, categoria ou faixa de preço. Retorna dados oficiais de preço, desconto ativo e estoque disponível.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {
                        "type": "string",
                        "description": "Nome do instrumento, marca ou termo de busca (ex: 'violão', 'Yamaha', 'Takamine GD20', 'teclado', 'guitarra')."
                    },
                    "categoria": {
                        "type": "string",
                        "description": "Categoria específica (ex: 'Violões', 'Guitarras', 'Baixos', 'Baterias e Percussão', 'Teclados e Pianos', 'Ukuleles')."
                    },
                    "preco_maximo": {
                        "type": "number",
                        "description": "Preço máximo em reais (ex: 1000.00)."
                    },
                    "preco_minimo": {
                        "type": "number",
                        "description": "Preço mínimo em reais."
                    },
                    "apenas_em_estoque": {
                        "type": "boolean",
                        "description": "Se verdadeiro, filtra apenas itens com estoque > 0. Padrão: true."
                    },
                    "ordenar_por": {
                        "type": "string",
                        "enum": ["preco_asc", "preco_desc"],
                        "description": "Critério de ordenação: 'preco_desc' para buscar os instrumentos mais caros / topo de linha da loja. 'preco_asc' para os mais baratos. Padrão: 'preco_asc'."
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Quantidade máxima de produtos retornados (padrão: 6, máximo: 12)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_detalhes_produto",
            "description": "Obtém detalhes técnicos completos, especificações de madeira, acabamento e status de um instrumento específico pelo seu ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id_produto": {
                        "type": "integer",
                        "description": "ID numérico do produto no catálogo."
                    }
                },
                "required": ["id_produto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_promocoes_ativas",
            "description": "Consulta todas as ofertas especiais, queimas de estoque e promoções ativas na loja com seus respectivos percentuais de desconto e preços promocionais.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_status_pedido",
            "description": "Consulta o andamento, status de entrega, código de rastreamento e itens de uma compra realizada pelo cliente a partir do número oficial do pedido (id_pedido). Por segurança e proteção de dados (LGPD), a consulta exige obrigatoriamente o número do pedido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id_pedido": {
                        "type": "integer",
                        "description": "Número de identificação do pedido (obrigatório, ex: 8, 4, 1)."
                    },
                    "identificador_cliente": {
                        "type": "string",
                        "description": "Opcional: nome, e-mail ou telefone do titular para validação cruzada de segurança."
                    }
                },
                "required": ["id_pedido"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_politicas",
            "description": "Consulta o manual oficial de políticas e procedimentos da Empório da Música: horários de funcionamento, formas de pagamento, regras de parcelamento, desconto PIX, política de trocas e devoluções (CDC / arrependimento 7 dias), regras de frete e garantia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topico": {
                        "type": "string",
                        "description": "Assunto ou dúvida a consultar (ex: 'devolução por arrependimento', 'horário de funcionamento', 'desconto pix', 'frete campo grande', 'garantia defeito', 'acessórios')."
                    }
                },
                "required": ["topico"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "solicitar_atendimento_humano",
            "description": "Aciona o transbordo para um atendente humano da equipe quando o cliente solicitar explicitamente ou houver uma reclamação que exija intervenção manual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "motivo": {
                        "type": "string",
                        "description": "Motivo da solicitação (ex: 'pedido_do_cliente', 'reclamacao_grave', 'negociacao_especial')."
                    },
                    "resumo": {
                        "type": "string",
                        "description": "Breve resumo da solicitação para o operador humano."
                    }
                },
                "required": ["motivo", "resumo"]
            }
        }
    }
]

def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Executa a ferramenta solicitada pela LLM e retorna o resultado estruturado."""
    try:
        if name == "consultar_catalogo":
            termo = arguments.get("termo")
            categoria = arguments.get("categoria")
            max_p = arguments.get("preco_maximo")
            min_p = arguments.get("preco_minimo")
            estoque = arguments.get("apenas_em_estoque", True)

            ordem = arguments.get("ordenar_por", "preco_asc")
            sort_order = "price_desc" if ordem == "preco_desc" else "price_asc"
            limite = min(int(arguments.get("limite", 6)), 12)

            results = search_products(
                query=termo,
                category=categoria,
                max_price=max_p,
                min_price=min_p,
                in_stock_only=estoque,
                sort_by=sort_order,
                limit=limite
            )
            return {
                "total_encontrado": len(results),
                "produtos": results
            }

        elif name == "consultar_detalhes_produto":
            prod_id = int(arguments.get("id_produto", 0))
            prod = get_product_by_id(prod_id)
            if not prod:
                return {"encontrado": False, "mensagem": f"Produto com ID {prod_id} não foi encontrado."}
            return {"encontrado": True, "produto": prod}

        elif name == "consultar_promocoes_ativas":
            promos = list_active_promotions()
            return {
                "total_promocoes": len(promos),
                "promocoes": promos
            }

        elif name == "consultar_status_pedido":
            order_id = int(arguments.get("id_pedido", 0))
            ident = arguments.get("identificador_cliente")
            status = get_order_status(order_id, ident)
            return status

        elif name == "consultar_politicas":
            topico = arguments.get("topico", "")
            texto = consult_policies(topico)
            return {"resultado_politica": texto}

        elif name == "solicitar_atendimento_humano":
            motivo = arguments.get("motivo", "não informado")
            resumo = arguments.get("resumo", "Cliente solicitou atendimento com atendente humano.")
            return {
                "transbordo_acionado": True,
                "motivo": motivo,
                "resumo": resumo,
                "canais_de_contato_humano": {
                    "whatsapp_atendimento": "(67) 3321-4500",
                    "telefone_fixo": "(67) 3341-4444",
                    "endereco": "Rua 14 de Maio, 3200 – Centro, Campo Grande - MS",
                    "horarios": "Segunda a sexta das 09h às 18h, sábados das 09h às 13h"
                },
                "instrucao_para_ia": "Informe com clareza e transparência que você registrou a solicitação e forneça imediatamente os canais de contato direto com a equipe humana da loja: WhatsApp de atendimento (67) 3321-4500, telefone (67) 3341-4444 e endereço físico na Rua 14 de Maio, 3200 - Centro, Campo Grande/MS."
            }

        else:
            return {"erro": f"Ferramenta '{name}' desconhecida."}

    except Exception as e:
        return {"erro": f"Falha na execução da ferramenta {name}: {str(e)}"}
