# Exemplo 1: Consulta sobre o Catálogo de Produtos com Filtros

## Cenário
Cliente buscando opções de violões com cordas de nylon ou aço custando até R$ 1.000,00. O agente deve identificar a intenção, acionar a ferramenta de catálogo com os parâmetros adequados e apresentar as opções com clareza, preços, estoque e opções de pagamento.

---

### Diálogo

**Cliente:**
> Olá! Vocês têm opções de violões disponíveis custando até R$ 1.000?

**Agente (Raciocínio Interno / Tool Calling):**
```json
{
  "tool_call": "consultar_catalogo",
  "arguments": {
    "termo": "violão",
    "preco_maximo": 1000.0,
    "apenas_em_estoque": true
  }
}
```

**Retorno da Ferramenta:**
```json
{
  "total_encontrado": 3,
  "produtos": [
    {
      "product_id": 83,
      "name": "Tagima Memphis AC-39 Nylon Natural",
      "price_brl": 429.9,
      "pix_price_brl": 408.41,
      "category_name": "Violões",
      "stock_quantity": 15,
      "specs": {
        "top": "Linden",
        "strings": "nylon",
        "electronics": "no",
        "color": "Natural"
      }
    },
    {
      "product_id": 81,
      "name": "Yamaha C40 Nylon Natural",
      "price_brl": 599.9,
      "pix_price_brl": 569.91,
      "category_name": "Violões",
      "stock_quantity": 12,
      "specs": {
        "top": "Spruce",
        "strings": "nylon",
        "electronics": "no",
        "color": "Natural"
      }
    },
    {
      "product_id": 82,
      "name": "Yamaha C70 Nylon Natural",
      "price_brl": 849.0,
      "pix_price_brl": 806.55,
      "category_name": "Violões",
      "stock_quantity": 8,
      "specs": {
        "top": "Spruce Sólido",
        "strings": "nylon",
        "electronics": "no",
        "color": "Natural"
      }
    }
  ]
}
```

**Agente (Resposta ao Cliente):**
> Olá! Tudo bem? Seja muito bem-vindo à Empório da Música! 🎸
> 
> Temos ótimas opções de violões em estoque custando até R$ 1.000,00, todos ideais para estudo e excelente sonoridade:
> 
> 1. **Tagima Memphis AC-39 Nylon Natural**: R$ 429,90 (ou **R$ 408,41 no PIX** com 5% de desconto). Um violão leve e confortável com cordas de nylon, perfeito para iniciantes. Temos 15 unidades em estoque!
> 2. **Yamaha C40 Nylon Natural**: R$ 599,90 (ou **R$ 569,91 no PIX**). O clássico mais recomendado por professores de música no mundo todo, com tampo em Spruce. Temos 12 unidades.
> 3. **Yamaha C70 Nylon Natural**: R$ 849,00 (ou **R$ 806,55 no PIX**). Nível intermediário com tampo em Spruce sólido e acabamento superior. Temos 8 unidades.
> 
> Lembrando que além do desconto de 5% no PIX à vista, parcelamos em até **12x sem juros no cartão de crédito**!
> 
> Gostaria de saber mais detalhes de algum deles ou prefere cordas de aço? 🎶
