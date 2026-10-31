# Exemplo 5: Tratamento de Itens Fora de Escopo e Transbordo para Atendente Humano

## Cenário
1. Cliente pergunta sobre compra de acessórios (cordas avulsas, palhetas e cabos), os quais a Empório da Música **não comercializa**.
2. O agente orienta com cortesia que a loja é focada exclusivamente em instrumentos musicais.
3. Em seguida, o cliente solicita falar com um atendente humano para tirar uma dúvida sobre uma troca personalizada.
4. O agente aciona a ferramenta de transbordo (`solicitar_atendimento_humano`), pausando a IA e alertando a equipe de suporte.

---

### Diálogo

**Cliente (Mensagem 1):**
> Boa tarde! Vocês vendem encordoamento D'Addario calibre 0.10, um cabo P10 de 5 metros e um pacote de palhetas?

**Agente (Raciocínio Interno / Tool Calling):**
```json
{
  "tool_call": "consultar_politicas",
  "arguments": {
    "topico": "acessórios cordas cabos palhetas escopo"
  }
}
```

**Retorno da Ferramenta:**
```text
ESCOPO E CATÁLOGO DE PRODUTOS DA LOJA:
- A Empório da Música comercializa EXCLUSIVAMENTE INSTRUMENTOS MUSICAIS (guitarras, baixos, violões, baterias, teclados, sopros, cordas orquestrais e ukuleles).
- A LOJA NÃO COMERCIALIZA ACESSÓRIOS como cordas avulsas, palhetas, cabos, cases, capas, pedais ou amplificadores.
- Informar educadamente que a loja trabalha focada exclusivamente nos instrumentos e indicar lojas parceiras.
```

**Agente (Resposta 1 ao Cliente):**
> Boa tarde! Tudo bem? 🎶
> 
> Aqui na Empório da Música nosso foco é 100% especializado na venda de **instrumentos musicais** (como guitarras, baixos, violões, teclados, sopros e percussão). Por essa razão, **não comercializamos acessórios** como cordas avulsas, palhetas, cabos, pedais ou amplificadores.
> 
> Para esses itens, recomendamos lojas parceiras aqui de Campo Grande especializadas em acessórios e luthieria.
> 
> Caso precise de um novo instrumento ou queira conhecer nossos modelos de guitarras e violões, estou à disposição! 🎸

---

**Cliente (Mensagem 2):**
> Entendi. Mas eu fiz uma compra de um contrabaixo semana passada e gostaria de pedir uma regulagem especial antes de vocês despacharem. Gostaria de falar com um atendente humano da equipe, por favor.

**Agente (Raciocínio Interno / Tool Calling):**
```json
{
  "tool_call": "solicitar_atendimento_humano",
  "arguments": {
    "motivo": "pedido_do_cliente",
    "resumo": "Cliente comprou contrabaixo e solicita contato com operador humano para verificar regulagem especial antes do envio."
  }
}
```

**Retorno da Ferramenta:**
```json
{
  "transbordo_acionado": true,
  "motivo": "pedido_do_cliente",
  "resumo": "Cliente comprou contrabaixo e solicita contato com operador humano para verificar regulagem especial antes do envio.",
  "instrucao_para_ia": "Informe ao cliente com cordialidade que a solicitação foi encaminhada para um atendente da equipe humana e que responderemos em breve no horário comercial."
}
```

**Agente (Resposta 2 ao Cliente):**
> Perfeito! Já registrei o seu pedido de contato e encaminhei a sua solicitação diretamente para a nossa equipe de atendimento humano aqui da loja. 🤝
> 
> Um dos nossos consultores vai assumir este chat em breve para verificar os detalhes da regulagem do seu contrabaixo antes do despacho.
> 
> Se preferir adiantar, você pode enviar por aqui o **número do seu pedido** e as especificações de altura de cordas/afinação que gostaria. Muito obrigado pela paciência! ✨
