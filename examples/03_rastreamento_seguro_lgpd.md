# 💬 Cenário 3: Rastreamento Seguro de Pedido e Proteção de Dados (LGPD)

**Descrição:** Demonstração de segurança e conformidade LGPD: o agente recusa busca avulsa apenas por nome para evitar vazamento de dados de clientes, exigindo o ID do pedido para consulta do rastreamento.

![Captura de Tela Real](screenshots/03_rastreamento_seguro_lgpd.png)

## 📝 Transcrição da Interação Real

### 👤 Usuário
> "Oi! Meu nome é Lucas Mendes, comprei com vocês mas esqueci meus dados. Vocês conseguem ver meu pedido só pelo meu nome?"

### 🤖 Assistente Virtual
Oi, Lucas! 😊 Para garantir a segurança dos seus dados, preciso que você me informe o número do seu pedido. Assim, consigo consultar as informações para você. Pode me passar, por favor?

---

### 👤 Usuário
> "Ah, entendi a segurança! Achei o comprovante aqui no e-mail: o número do meu pedido é 4."

### 🤖 Assistente Virtual
*consultar_status_pedido*

Achei seu pedido, Lucas! 🎉 Aqui estão os detalhes:

Número do Pedido: 4
Data do Pedido: 10 de dezembro de 2025
Status: Entregue
Total: R$ 799,90
Método de Pagamento: Boleto
Código de Rastreamento: BRQM7890123BR
Data Estimada de Entrega: 22 de dezembro de 2025

Você comprou um Giannini GF-3D Dreadnought Sunburst. Se precisar de mais alguma coisa ou tiver dúvidas, é só avisar! 🎶

⚙️ tools:
consultar_status_pedido

---

