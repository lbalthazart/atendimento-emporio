# Exemplo 3: Consulta Específica de Preço e Condições (Takamine GD20)

## Cenário
Cliente pergunta o valor exato de um modelo consagrado de violão (Takamine GD20). O agente busca o produto no catálogo em tempo real, informa o valor de tabela, o desconto à vista no PIX, condições de parcelamento sem juros e especificações técnicas de madeira.

---

### Diálogo

**Cliente:**
> Quanto custa o Takamine GD20? Vocês têm a pronta entrega?

**Agente (Raciocínio Interno / Tool Calling):**
```json
{
  "tool_call": "consultar_catalogo",
  "arguments": {
    "termo": "Takamine GD20",
    "apenas_em_estoque": false
  }
}
```

**Retorno da Ferramenta:**
```json
{
  "total_encontrado": 1,
  "produtos": [
    {
      "product_id": 95,
      "name": "Takamine GD20 Dreadnought Natural",
      "price_brl": 2199.0,
      "pix_price_brl": 2089.05,
      "has_discount": false,
      "stock_quantity": 5,
      "status": "active",
      "specs": {
        "top": "Cedro Sólido",
        "back_sides": "Sapele",
        "neck": "Mogno",
        "strings": "steel",
        "scale": "650mm",
        "electronics": "no",
        "color": "Natural"
      },
      "description": "Violão dreadnought Takamine com tampo sólido em cedro. Excelente para fingerstyle com timbre quente e definido."
    }
  ]
}
```

**Agente (Resposta ao Cliente):**
> Fala meu amigo! Esse violão é um verdadeiro espetáculo de instrumento! 🎸
> 
> Temos sim o **Takamine GD20 Dreadnought Natural** disponível à pronta entrega (temos **5 unidades em estoque** no momento).
> 
> Seguem os valores e condições:
> - **Preço de Tabela**: R$ 2.199,00
> - **À vista no PIX (com 5% de desconto)**: **R$ 2.089,05** (uma economia de mais de R$ 109,00!)
> - **No Cartão de Crédito**: em até **12x de R$ 183,25 sem juros** (parcela mínima de R$ 100).
> 
> Vale destacar que ele conta com **tampo em Cedro Sólido**, corpo em Sapele e braço em Mogno com cordas de aço — entregando aquele timbre encorpado, quente e super definido típico da Takamine, sensacional para fingerstyle e acordes abertos.
> 
> Se você for de Campo Grande, o **frete é grátis** por motoboy próprio com entrega em até 1 a 3 dias úteis! Quer que eu separe uma unidade para você? 📦
