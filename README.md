# 🎸 Empório da Música - Agente Inteligente de Atendimento

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Multi--Model-6366F1?style=for-the-badge)](https://openrouter.ai/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![LGPD](https://img.shields.io/badge/LGPD-Compliant_(7d_TTL)-10B981?style=for-the-badge)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

Protótipo de **Agente Autônomo de Atendimento ao Cliente** para a **Empório da Música**, tradicional loja de instrumentos musicais sediada em Campo Grande/MS desde 2008.

O agente atua no canal de atendimento auxiliando a equipe humana no esclarecimento de dúvidas recorrentes, consulta de catálogo em tempo real, verificação de pedidos, aplicação estrita de políticas comerciais (CDC, prazos, trocas e devoluções), resiliência com fila inteligente de mensagens e filtragem de pedidos fora de escopo.

---

## 📑 Sumário

- [Visão Geral & Persona](#-visão-geral--persona)
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Justificativa das Decisões Técnicas](#-justificativa-das-decisões-técnicas)
- [Mecanismos de Resiliência, Fila e Segurança](#-mecanismos-de-resiliência-fila-e-segurança)
- [Conformidade com a LGPD (Retenção de 7 Dias)](#-conformidade-com-a-lgpd-retenção-de-7-dias)
- [Como Rodar o Projeto](#-como-rodar-o-projeto)
  - [Opção 1: Via Docker (Recomendado)](#opção-1-via-docker-recomendado)
  - [Opção 2: Execução Local](#opção-2-execução-local)
- [Interface Web e Documentação da API](#-interface-web-e-documentação-da-api)
- [Integração Omnichannel (WhatsApp / Web / Redes)](#-integração-omnichannel-whatsapp--web--redes)
- [Exemplos de Interação](#-exemplos-de-interação)
- [Limitações Conhecidas & Próximos Passos](#-limitações-conhecidas--próximos-passos)
- [Uso de Assistentes de Código (Workflow de IA)](#-uso-de-assistentes-de-código-workflow-de-ia)

---

## 🎯 Visão Geral & Persona

A **Empório da Música** preza por um atendimento acolhedor, transparente e técnico:
- **Tom de Voz**: Informal, prestativo e profissional — como uma conversa amigável com alguém que realmente entende de música e instrumentos.
- **Domínio Restrito**: A loja comercializa **exclusivamente instrumentos musicais** (cordas, teclas, sopro, percussão). **Não comercializa acessórios** (palhetas, cordas avulsas, cabos, pedais, amplificadores ou cases). O agente redireciona gentilmente tais solicitações.
- **Compromisso com a Verdade**: Informações de preços, descontos, estoque e pedidos são sempre consultadas nas fontes oficiais; o agente nunca inventa dados e respeita fielmente as políticas internas e o Código de Defesa do Consumidor (CDC).

---

## 🏗 Arquitetura da Solução

O sistema adota uma abordagem modular baseada em **Function Calling / Tool Use nativo**:

```
                              ┌────────────────────────────────────────┐
                              │            Canais de Acesso            │
                              │   Web Chat Integrado | API RESTful     │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │            FastAPI Server              │
                              │   - Fila de Mensagens (Debounce)       │
                              │   - Endpoints de Texto e Multimodal    │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │          Agente Orquestrador           │
                              │      OpenRouter (ex: gpt-4o-mini)      │
                              │   + Fallbacks Automáticos de Modelos   │
                              │   + Prompt Shield (Anti-Injection)     │
                              └───────────────────┬────────────────────┘
                                                  │
                ┌─────────────────────────────────┼────────────────────────────────┐
                ▼                                 ▼                                ▼
     ┌──────────────────────┐          ┌──────────────────────┐         ┌──────────────────────┐
     │  Motor Relacional    │          │  Motor de Políticas  │         │   Gestor de Sessão   │
     │      (SQLite)        │          │    (Hybrid RAG)      │         │   (Memória & LGPD)   │
     │ - Produtos & Estoque │          │ - Manual em PDF      │         │ - TTL de 7 dias      │
     │ - Pedidos & Rastreio │          │ - Regras CDC / Troca │         │ - Transbordo Humano  │
     │ - Promoções Ativas   │          │ - Horários e Fretes  │         │ - Pausa de IA        │
     └──────────────────────┘          └──────────────────────┘         └──────────────────────┘
```

### Componentes Principais
1. **Orquestrador Central**: Implementado em Python assíncrono, gerencia o ciclo ReAct através de chamadas de função explícitas.
2. **Tools de Dados Estruturados (SQLite)**: As tabelas fornecidas (`products.csv`, `orders.csv`, `order_items.csv`, `promotions.csv`, `customers.csv`, `categories.csv`) são automaticamente indexadas em SQLite, permitindo filtros exatos de preço, categoria e disponibilidade sem alucinações numéricas.
3. **Tools de Políticas da Loja (RAG / Knowledge Retrieval)**: O arquivo `políticas_da_loja.pdf` é estruturado por tópicos normativos (Pagamento, Devolução/Arrependimento em 7 dias pelo CDC, Troca por Defeito em 30 dias, Fretes e Garantia) para recuperação precisa de regras.
4. **Fila Inteligente & Debounce**: Mensagens sequenciais enviadas pelo cliente em curto intervalo (padrão de 2.2s a 3.0s) são unificadas antes do envio à LLM, evitando respostas fragmentadas.
5. **Transbordo Humano & Pausa de IA (`pause_ia`)**: Detecção de solicitações explícitas de suporte ou reclamações complexas, gerando payloads separados para o cliente e pausando temporariamente o bot para que a equipe humana assuma.

---

## 💡 Justificativa das Decisões Técnicas

| Decisão | Escolha | Justificativa |
|---|---|---|
| **Linguagem Principal** | Python 3.12+ | Restrição técnica mandatória; ecossistema maduro para IAs, tipagem estática moderna e bibliotecas assíncronas de alta performance. |
| **Framework do Agente** | Python Nativo + Tool Calling | Optou-se por **não** usar frameworks pesados (como LangChain complexo ou CrewAI) para manter controle total sobre o loop de raciocínio, facilidade de depuração, transparência do código e performance superior. |
| **Provedor e Modelo LLM** | OpenRouter (`openai/gpt-4o-mini`) | Permite usar os melhores modelos do mercado sob **uma única chave de API**, oferecendo altíssima fidelidade a chamadas de ferramentas (*tool calling*), velocidade e suporte multimodal nativo. Não usamos modelos locais devido à latência e requisitos proibitivos de hardware. |
| **Camada de Dados** | SQLite Indexado em Memória/Disco | Dados tabulares (preço, estoque, status) devem ser exatos. Consultar CSVs via SQL estruturado elimina alucinações numéricas e garante consultas como *"violões abaixo de R$ 1000"* com 100% de precisão. |
| **Retrieval de Políticas** | Indexação Semântica / Textual | O manual de políticas possui regras contratuais e do CDC. A busca estruturada por tópicos garante que prazos (7 dias arrependimento, 30 dias defeito) sejam aplicados com fidelidade jurídica. |
| **Prompt Engineering** | *Prompt Shield* & *Few-shot System Prompt* | Delimitação estrita do papel do assistente, instruções inegociáveis de segurança contra *prompt injection* / *jailbreak*, e proibição explícita de inventar informações ausentes. |

---

## 🛡️ Mecanismos de Resiliência, Fila e Segurança

Para garantir confiabilidade de nível corporativo e uma experiência conversacional fluida, o agente incorpora padrões arquiteturais avançados:

### 1. Cadeia de Contingência e Fallback Multi-Modelos
Em ambientes de produção com APIs de LLM, oscilações externas de rede, limitações de taxa (*rate limits 429*), manutenções temporárias de provedores (*500/503*) ou inconsistências de parâmetros podem interromper o atendimento.
- **Cadeia Automática de Modelos**:
  1. **Modelo Primário**: `openai/gpt-4o-mini` (rápido, excelente aderência a JSON/Tools e ótimo custo-benefício).
  2. **Fallback 1**: `google/gemini-2.0-flash-001` (altíssima velocidade e ampla janela de contexto).
  3. **Fallback 2**: `meta-llama/llama-3.3-70b-instruct` (modelo open-source topo de linha).
  4. **Fallback 3**: `anthropic/claude-3.5-haiku` (alta aderência instrucional).
  5. **Fallback de Visão Computacional**: `openai/gpt-4o-mini` ➔ `google/gemini-2.0-flash-001`.
- **Tratamento Humanizado de Exceções**: Caso todos os modelos da cadeia falhem simultaneamente, a aplicação **nunca expõe stack traces, erros 400/500 ou JSONs técnicos para o cliente**. O sistema devolve uma mensagem acolhedora orientando o contato direto com a equipe:
  > *"No momento, nosso atendimento automático está passando por uma breve instabilidade e não foi possível processar sua mensagem. Por favor, tente novamente em instantes ou fale diretamente com nossa equipe pelo telefone ou WhatsApp (67) 3341-4444. Agradecemos a compreensão! 🎸"*

### 2. Fila Inteligente de Mensagens com Debounce
Em canais de chat (WhatsApp, web chat, Instagram), os clientes frequentemente dividem seu raciocínio em várias mensagens curtas seguidas:
> *Cliente:* "Oi"  
> *Cliente:* "Vocês têm violão de nylon?"  
> *Cliente:* "Até uns 800 reais?"  

- **Problema de arquiteturas ingênuas**: Cada mensagem dispara uma requisição individual à LLM, consumindo 3x mais tokens e gerando 3 respostas desconexas e sobrepostas que poluem o chat.
- **Solução implementada**: Fila de acumulação com janela de **debounce configurável (2.2s a 3.0s)**.
  - Cada nova frase enviada reinicia o cronômetro.
  - Ao término do intervalo, a fila consolida todas as frases em um único bloco textual.
  - O agente aciona a ferramenta `consultar_catalogo(termo='violão', preco_maximo=800)` uma única vez e gera **uma resposta completa, coesa e natural** para todos os pontos levantados.

### 3. Pausa de IA para Transbordo Humano (`pause_ia`)
Inspirado em padrões consolidados de mensageria corporativa:
- Quando o cliente solicita expressamente falar com um atendente humano (*"quero falar com uma pessoa"*, *"atendente humano"*) ou quando a ferramenta `solicitar_atendimento_humano` é acionada por reclamações complexas:
  1. A sessão recebe a flag `is_human_paused = True` com tempo de expiração configurável (padrão de 10 minutos).
  2. O agente avisa o cliente com cordialidade sobre a transferência.
  3. Enquanto pausada, a IA **não processa novas mensagens automáticas** daquela sessão. Isso permite que o operador humano da loja converse livremente com o cliente no mesmo canal sem que o bot responda por cima ou gere contradições.

### 4. Higienização de Mensagens (`sanitize_messages`) contra Erros de Schema
Provedores rigorosos de Tool Calling (como OpenAI e Anthropic via OpenRouter) exigem que mensagens com `role: "tool"` sejam obrigatoriamente precedidas por um `assistant` contendo o `tool_calls` com ID correspondente.
- Em conversas de múltiplos turnos, o fatiamento de histórico (*slicing*) pode cortar no meio de um bloco de ferramentas e deixar mensagens `tool` órfãs, causando erro HTTP 400 (`Invalid parameter: messages with role 'tool' must be a response to a preceeding message with 'tool_calls'`).
- **Solução implementada**:
  - A memória de longo prazo da conversa armazena apenas as falas dialógicas finais (`user` e `assistant`).
  - A função `sanitize_messages` varre todas as mensagens antes do envio e expurga preventivamente qualquer chamada de ferramenta incompleta ou fora de ordem.

### 5. Grounding Rigoroso e Zero Alucinação
- **Dados Numéricos**: Preços, estoque e promoções vêm exclusivamente de consultas SQL ao banco de dados estruturado derivado dos CSVs.
- **Regras Contratuais**: Prazos de devolução pelo CDC (7 dias corridos sem custo de frete), garantia de 90 dias e regras de frete vêm do manual oficial em PDF.
- **Não Invenção de Chaves ou Dados Ausentes**: Como o manual de políticas não define uma chave PIX fixa, o agente **não alucina** uma chave inventada; ele esclarece com transparência que a chave ou QR Code oficial para pagamento com os 5% de desconto é gerado pela equipe no momento do fechamento da compra pelo WhatsApp oficial da loja (`(67) 3321-4500` ou `(67) 3341-4444`).

---

## 🔒 Conformidade com a LGPD (Retenção de 7 Dias)

Em respeito à **Lei Geral de Proteção de Dados (Lei nº 13.709/2018)**:
- Todo histórico de conversa e identificador de sessão é associado a um **TTL (Time-To-Live) de 7 dias** (`604.800 segundos`).
- Após o período de 7 dias da última interação, as mensagens são automaticamente expurgadas da memória de atendimento.
- Os dados pessoais do cliente consultados durante o atendimento (telefone, e-mail) são usados exclusivamente para a finalidade legítima de localização de pedidos e atendimento.
- **Direito ao Esquecimento (Art. 18 da LGPD)**: Endpoint `DELETE /api/history/{session_id}` e botão na interface web permitem a exclusão imediata de todos os dados do cliente sob demanda.

---

## 🚀 Como Rodar o Projeto

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose **OU** Python 3.12+ instalado.
- Uma chave de API do [OpenRouter](https://openrouter.ai/) (ou OpenAI).

---

### Opção 1: Via Docker (Recomendado)

1. Clone o repositório:
```bash
git clone https://github.com/lbalthazart/atendimento-emporio.git
cd atendimento-emporio
```

2. Crie seu arquivo de ambiente `.env` a partir do exemplo:
```bash
cp .env.example .env
```
Abra o arquivo `.env` e insira sua chave:
```env
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
```

3. Suba o container da aplicação:
```bash
docker compose up --build
```

4. Acesse no navegador:
- **Interface Web de Atendimento**: [http://localhost:8000](http://localhost:8000)
- **Documentação Interativa Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Opção 2: Execução Local

1. Clone o repositório e crie o ambiente virtual:
```bash
git clone https://github.com/lbalthazart/atendimento-emporio.git
cd atendimento-emporio

python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o `.env`:
```bash
cp .env.example .env
# Preencha sua OPENROUTER_API_KEY no arquivo .env
```

4. Inicie o servidor FastAPI:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 💻 Interface Web e Documentação da API

A aplicação disponibiliza uma **interface gráfica moderna de chat** embutida diretamente no backend (sem necessidade de instalar Node.js ou ferramentas de frontend adicionais), além de endpoints REST:

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Interface Web de Chat interativo com suporte a fila inteligente |
| `POST` | `/api/chat` | Envio de mensagem de texto com histórico e suporte a debounce |
| `POST` | `/api/media` | Envio de áudio (transcrição) ou imagem (análise visual de instrumentos) |
| `GET` | `/api/history/{session_id}` | Consulta do histórico ativo da sessão (respeitando o TTL de 7 dias) |
| `DELETE` | `/api/history/{session_id}` | Exclusão imediata dos dados da conversa (Direito ao Esquecimento - LGPD) |
| `GET` | `/health` | Checagem de integridade do serviço e conexão com OpenRouter |

---

## 📱 Integração Omnichannel (WhatsApp / Web / Redes)

A arquitetura foi projetada para ser agnóstica de canal. Qualquer plataforma externa pode ser conectada consumindo a API REST:

```json
// POST /api/chat
{
  "session_id": "5567998123456",
  "message": "Vocês têm violão de nylon até R$ 800?"
}
```

**Exemplo de Resposta Estruturada**:
```json
{
  "session_id": "5567998123456",
  "reply": "Opa, tudo bem? Temos sim! Uma ótima opção é o Tagima Memphis AC-39 Nylon Natural por R$ 429,90 (temos 15 unidades em estoque). Se puder esticar um pouquinho, temos também o clássico Yamaha C40 por R$ 599,90. Lembrando que à vista no PIX você ainda garante 5% de desconto!",
  "tools_used": ["consultar_catalogo"],
  "handoff_required": false
}
```

Para integrar a bots de WhatsApp (como Evolution API, Z-API, Baileys ou n8n):
- Basta configurar o webhook de mensagem recebida para disparar uma requisição `POST /api/chat` passando o número do cliente como `session_id`.
- A fila com debounce nativo do agente agrupa automaticamente mensagens enviadas em sequência rápida.

---

## 💬 Exemplos de Interação

Conversas completas e detalhadas demonstrando o comportamento do agente encontram-se na pasta [`examples/`](examples/):

1. **[Consulta de Catálogo com Filtros](examples/01_consulta_catalogo.md)**: Cliente buscando opções de violões até R$ 1.000,00 com consulta em tempo real ao banco de estoque e preços.
2. **[Informações Institucionais e Horários](examples/02_informacoes_loja.md)**: Endereço físico em Campo Grande, canais de contato e horário de expediente.
3. **[Consulta Específica de Preço e Desconto](examples/03_preco_takamine.md)**: Busca pelo modelo Takamine GD20, detalhamento das especificações e opções de parcelamento e PIX.
4. **[Aplicação de Políticas de Devolução (CDC)](examples/04_devolucao_arrependimento.md)**: Cliente solicitando devolução por arrependimento; agente orienta sobre o prazo legal de 7 dias, condições da embalagem e frete coberto pela loja.
5. **[Tratamento de Escopo e Transbordo](examples/05_fora_escopo_e_suporte.md)**: Cliente solicitando palhetas e cabos (fora de escopo) e posterior solicitação de contato com atendente humano.

---

## ⚖ Limitações Conhecidas & Próximos Passos

Caso houvesse mais tempo de desenvolvimento, as seguintes melhorias seriam priorizadas:

1. **Reserva Automática de Estoque em Tempo Real**: Integração transacional com o ERP da loja para travar o item no carrinho durante a geração do pedido.
2. **Geração de Cobrança PIX Copia-e-Cola Dinâmica**: Integração direta com gateway bancário para gerar o QR Code e chave PIX instantaneamente no chat.
3. **Reranker Semântico para Políticas**: Adição de um modelo de re-ranking (como Cohere Rerank) para refinar a precisão em trechos altamente específicos de manuais contratuais extensos.
4. **Framework de Avaliação Contínua (LLM Evals)**: Implementação de pipeline de testes automatizados com *LLM-as-a-Judge* (ex: DeepEval ou Ragas) medindo acurácia factual, tom de voz e taxa de recusa de prompt injection a cada commit.

---

## 🤖 Uso de Assistentes de Código (Workflow de IA)

Em consonância com as orientações do desafio técnico, documentamos com total transparência o uso de assistentes de inteligência artificial durante o projeto:

- **Ferramenta Utilizada**: Google Antigravity & Claude 3.5 Sonnet / Gemini 2.0.
- **Workflow Aplicado**:
  1. **Planejamento & Engenharia de Requisitos**: Análise do PDF do desafio e dos CSVs para mapear requisitos funcionais, restrições da loja e casos de borda.
  2. **Estruturação Arquitetural**: Concepção do modelo de *Tool Calling* em Python assíncrono para desacoplar a recuperação de dados do raciocínio da LLM.
  3. **Scaffolding de Código & Testes**: Geração dos modelos Pydantic, scripts de carga de banco SQLite e implementação do servidor FastAPI.
  4. **Refinamento & Code Review**: Verificação humana de cada regra de negócio (prazos do CDC, frete grátis para Campo Grande, proibição de venda de acessórios).

O uso do assistente atuou como acelerador de produtividade na implementação do boilerplate e cobertura de testes, mantendo a direção técnica, decisões de design e validação estritamente sob comando humano.
