# Exemplo 4: Aplicação das Políticas de Devolução e Arrependimento (CDC)

## Cenário
Cliente realizou uma compra recente pela internet e manifesta arrependimento, perguntando se tem direito à devolução e como funciona o processo. Cenário não-trivial exigindo aplicação rigorosa das políticas comerciais e do Art. 49 do CDC.

---

### Diálogo

**Cliente:**
> Recebi meu violão há 3 dias pelo correio, mas me arrependi da minha compra... Posso devolver meu pedido e receber o dinheiro de volta? Eu tenho que pagar o frete?

**Agente (Raciocínio Interno / Tool Calling):**
```json
{
  "tool_call": "consultar_politicas",
  "arguments": {
    "topico": "devolução arrependimento compras online frete reembolso cdc"
  }
}
```

**Retorno da Ferramenta:**
```text
POLÍTICA DE TROCAS E DEVOLUÇÕES (Conforme Código de Defesa do Consumidor - Lei nº 8.078/90):
1. Direito de Arrependimento (Compras Online / WhatsApp):
   - O cliente pode solicitar devolução em até 7 (SETE) DIAS CORRIDOS após receber o produto, sem necessidade de justificativa.
   - Requisitos: produto na embalagem original, sem sinais de uso, acompanhado de todos os acessórios e manuais.
   - Frete de devolução: 100% POR CONTA DA LOJA em caso de arrependimento no prazo legal.
   - Reembolso integral na mesma forma de pagamento original em até 10 dias úteis após recebimento na loja.
```

**Agente (Resposta ao Cliente):**
> Olá! Fique totalmente tranquilo(a), nós seguimos rigorosamente o Código de Defesa do Consumidor e nosso processo de devolução é bem simples e transparente! 🤝
> 
> Como você recebeu o produto há 3 dias, você está plenamente dentro do prazo legal de **7 (sete) dias corridos** para exercer o **Direito de Arrependimento**.
> 
> Veja como funciona:
> 1. **Sem Custo de Frete**: Você **não paga nada** pelo frete de devolução! A Empório da Música arca com 100% do frete reverso, gerando um código de postagem para você nos Correios ou transportadora.
> 2. **Condição do Instrumento**: O instrumento precisa estar na embalagem original, sem sinais de uso ou desgaste, acompanhado de eventuais manuais e acessórios que vieram de fábrica.
> 3. **Reembolso**: Assim que o produto chegar aqui na loja e passar pela conferência rápida, o estorno/reembolso integral é processado na mesma forma de pagamento da compra (PIX, boleto ou cartão) em até 10 dias úteis.
> 
> Você poderia me informar o **número do seu pedido** (ou o seu CPF/e-mail cadastrado)? Assim já localizo sua compra no sistema e inicio a solicitação da etiqueta de devolução para você! 📦
