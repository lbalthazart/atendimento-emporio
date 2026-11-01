# 💬 Customer Service Interaction Examples

This folder contains transcripts and live screenshots of real interactions with the **Empório da Música** Autonomous AI Agent, captured directly from the integrated web interface via Playwright automation connected to the live FastAPI backend and OpenRouter models.

Each `.md` document presents the complete multi-turn conversation, the live browser screenshot, and the executed tool calls (*Function Calling*) against the relational SQLite database and store policy engine.

---

## 📸 Live Web Interface Demonstration

![Web Customer Service Interface](../docs/screenshots/interface_chat.png)

---

## 📑 Evaluation Scenarios

| # | Scenario & Document | Browser Screenshot | Key Tools |
|---|---|---|---|
| **01** | [**Catalog Search, Pricing & Active Promotions**](01_catalogo_precos_promocoes.md)<br>Filter guitars under R$ 1,000, price check on Takamine GD20, and automatic detection of clearance sales | ![Screenshot 01](screenshots/01_catalogo_precos_promocoes.png) | `consultar_catalogo`, `consultar_promocoes_ativas` |
| **02** | [**Store Information & CDC Return Policy**](02_loja_horarios_politica_devolucao.md)<br>Store address and hours in Campo Grande/MS + statutory 7-day remorse return with store-covered shipping | ![Screenshot 02](screenshots/02_loja_horarios_politica_devolucao.png) | `consultar_politicas` |
| **03** | [**Secure Order Tracking & LGPD Protection**](03_rastreamento_seguro_lgpd.md)<br>Rejection of unauthenticated name-only searches (anti-data leak) and verified courier tracking by Order ID (#4) | ![Screenshot 03](screenshots/03_rastreamento_seguro_lgpd.png) | `consultar_status_pedido` |
| **04** | [**Multimodal Photo Recognition, Scope & Human Handoff**](04_reconhecimento_multimodal_e_transbordo.md)<br>Gibson Les Paul identification from photo, cordial refusal of accessories, and human handoff with direct contacts | ![Screenshot 04](screenshots/04_reconhecimento_multimodal_e_transbordo.png) | OpenRouter Vision, `consultar_catalogo`, `solicitar_atendimento_humano` |

---

## 🎯 Verified Business Guarantees

1. **Automatic Promotions & Zero Numeric Hallucination**: Prices, clearance sale discounts, and cash PIX rates are strictly queried from normalized database tables.
2. **Data Protection & Privacy (LGPD)**: Customer personal data and order histories are protected against social engineering leaks; the agent mandates the formal Order ID.
3. **Focused Domain Scope & Actionable Human Handoff**: Polite refusal of out-of-scope products (accessories) and immediate provision of official store WhatsApp (`(67) 3321-4500`) and phone contacts when escalating to humans.
