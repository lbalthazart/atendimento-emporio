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

Abaixo detalham-se as justificativas aprofundadas para cada um dos eixos arquiteturais solicitados no desafio:

| Eixo Arquitetural | Escolha | Justificativa Sintética |
|---|---|---|
| **1. Framework** | FastAPI (Python 3.12) + ReAct Nativo | Alto throughput assíncrono, documentação OpenAPI automática, zero acoplamento com bibliotecas inchadas (LangChain/CrewAI) e controle total do ciclo de vida das mensagens. |
| **2. Abordagem** | ReAct com *Function Calling* Estrito | Separação rígida entre cognição (LLM) e dados factuais (SQL/Regras). Elimina alucinações de preço, estoque e prazos legais do CDC. |
| **3. Modelo e Provedor** | OpenRouter (`gpt-4o-mini` + Multi-Fallback) | Chave unificada para múltiplos provedores (OpenAI, Google, Meta, Anthropic), latência sub-segundo, baixo custo e mitigação de lock-in ou rate limits. |
| **4. Interface Híbrida** | Web Chat Integrado + API RESTful | Permite avaliação imediata no navegador (sem dependências de Node.js/npm) e integração plug-and-play com bots de WhatsApp (Evolution API, Z-API, n8n). |
| **5. Persistência & LGPD** | Memória em Sessão com TTL de 7 Dias | Conformidade estrita com a LGPD (Lei 13.709/2018); expurgo automático de conversas após 7 dias e endpoint de exclusão sob demanda. |
| **6. Tratamento de Dados** | SQLite Indexado + Parser de Políticas | Consultas SQL de milissegundo a partir dos CSVs brutos e recuperação por seções normativas do manual em PDF. |

---

### 1. Framework: FastAPI + Python Nativo vs. LangChain / CrewAI
- **Por que FastAPI?**
  - **Alta Performance Assíncrona**: Suporte nativo a `async/await` com ASGI (`uvicorn`), essencial para lidar com requisições I/O-bound (chamadas de rede para APIs de IA, streams e webhooks de mensageria).
  - **Validação com Pydantic v2**: Contratos de entrada e saída rigorosamente tipados, garantindo que payloads de chat ou transbordo humano sejam validados em nível de schema antes de atingir o agente.
  - **Documentação Automática**: Geração em tempo real de especificações OpenAPI e Swagger UI interativo (`/docs`).
- **Por que Python Nativo em vez de LangChain ou CrewAI?**
  - Frameworks de agente de alto nível frequentemente introduzem camadas desnecessárias de abstração (*black boxes*), prompts internos opacos, dependências pesadas e quebras de contrato entre versões menores.
  - Implementar o orquestrador ReAct de forma nativa permitiu:
    - Controle milimétrico sobre a higienização de mensagens (`sanitize_messages`) evitando erros 400 de *orphan tool calls*.
    - Depuração facilitada e transparente através de logs estruturados.
    - Menor pegada de memória do container Docker e inicialização ultrarrápida (sub-segundo).

### 2. Abordagem: ReAct com Function Calling Nativo vs. RAG Ingênuo
- **O Risco do RAG Ingênuo de Texto Puro**:
  - Injetar catálogos inteiros em texto plano no contexto da LLM causa alucinações numéricas graves (preços inventados, modelos trocados, promoções vencidas) e estouro da janela de contexto.
- **A Solução Adotada (ReAct + Tool Calling)**:
  - O agente atua como um **orquestrador cognitivo**: ele interpreta a intenção do cliente, extrai parâmetros (ex: termo de busca, teto de preço, categoria) e delega a busca a funções Python determinísticas (`consultar_catalogo`, `consultar_detalhes_produto`, `consultar_status_pedido`, `consultar_politicas`).
  - O modelo apenas sintetiza em linguagem natural a resposta factual retornada pela ferramenta, garantindo **fidelidade matemática e comercial absoluta**.

### 3. Modelo e Provedor: OpenRouter com Fallbacks Automáticos
- **Por que OpenRouter?**
  - Provedores diretos únicos criam dependência de fornecedor (*vendor lock-in*). Caso a OpenAI ou Anthropic sofram instabilidade temporária, o atendimento da loja é interrompido.
  - O OpenRouter unifica OpenAI, Google, Anthropic e Meta sob um mesmo endpoint compatível com o padrão OpenAI, permitindo roteamento inteligente e contingência instantânea.
- **Por que `openai/gpt-4o-mini` como Modelo Primário?**
  - Excelente custo-benefício (fração do custo de modelos frontier como GPT-4o ou Claude 3.5 Sonnet).
  - Fidelidade superior na geração de chamadas de função JSON (*tool calling*).
  - Latência de primeiro token (TTFT) extremamente baixa, crucial para chats síncronos.
- **Por que não Modelos Locais (Ollama / vLLM)?**
  - Modelos locais de 70B+ parâmetros exigem instâncias com GPUs caras (A10G/A100) com custo fixo elevado para uma loja regional, enquanto modelos menores (ex: 7B/8B) apresentam falhas frequentes ao invocar ferramentas estruturadas com múltiplos argumentos. O OpenRouter combina custo sob demanda com performance topo de linha.

### 4. Interface de Interação Híbrida: Web Chat Embutido + API REST
- **Acesso Imediato via Web Chat (`GET /`)**:
  - A aplicação entrega uma interface moderna em HTML5, Tailwind CSS e `marked.js` servida diretamente pelo FastAPI. Isso elimina a necessidade de instalar Node.js, npm ou rodar múltiplos terminais durante a avaliação ou demonstração para clientes.
  - A interface conta com fila de digitação com indicador visual de debounce e layout ancorado sem quebra de scroll.
- **API REST Omnichannel (`POST /api/chat`, `POST /api/media`)**:
  - A mesma lógica que alimenta a web atende qualquer plataforma externa de mensageria (WhatsApp via Evolution API / Z-API / Baileys, Instagram Direct, Telegram ou fluxos n8n). Basta enviar um JSON contendo `session_id` e `message`.

### 5. Persistência do Histórico e Conformidade LGPD
- **Memória de Sessão com TTL de 7 Dias**:
  - Em conformidade com a **Lei Geral de Proteção de Dados (Lei nº 13.709/2018)**, dados conversacionais e dados pessoais consultados para pedidos (e-mail, telefone) não devem residir indefinidamente no sistema.
  - A classe `SessionStore` implementa purga automática de qualquer sessão cuja última mensagem tenha ocorrido há mais de **604.800 segundos (7 dias)**.
- **Direito ao Esquecimento (Art. 18 LGPD)**:
  - Disponibilizado o endpoint `DELETE /api/history/{session_id}` e um botão visual de 'Limpar Conversa' no chat para exclusão definitiva imediata sob requisição do titular.
- **Arquitetura Desacoplada**:
  - O armazenamento reside em memória com interface desacoplada, pronta para substituição transparente por Redis ou Memcached em clusters distribuídos de alta escala.

### 6. Tratamento e Ingestão de Dados: CSVs em SQLite + Parser de PDF
- **Ingestão Estruturada dos CSVs**:
  - Durante a inicialização da aplicação, os 6 arquivos CSV fornecidos (`products.csv`, `categories.csv`, `orders.csv`, `order_items.csv`, `promotions.csv`, `customers.csv`) são automaticamente sanitizados, convertidos para tipos fortes (floats de preço, inteiros de estoque, datas ISO) e carregados em um banco SQLite indexado.
  - Índices dedicados em `products(category_id)`, `products(price)`, `products(stock)` e `orders(order_id)` garantem consultas instantâneas e sem overhead de I/O em disco.
- **Parser Segmentado de Políticas**:
  - O arquivo `políticas_da_loja.pdf` é processado na inicialização e particionado em seções normativas canônicas (Arrependimento CDC de 7 dias, Defeito de 30 dias, Garantia legal de 90 dias, Fretes e Horários). Dessa forma, a ferramenta `consultar_politicas` recupera o parágrafo exato aplicável à dúvida jurídica do cliente sem ruídos de formatação.
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
- **Dados Numéricos**: Preços, estoque e promoções vêm exclusivamente de consultas SQL ao banco de dados estruturado derivado dos CSVs. Suporte a ordenação de preço (`preco_desc` e `preco_asc`) garantindo que perguntas sobre o produto mais caro tragam o topo da linha (Teclado Nord Synth 2 Pro e Gibson Les Paul) e não instrumentos baratos.
- **Regras Contratuais**: Prazos de devolução pelo CDC (7 dias corridos sem custo de frete), garantia de 90 dias e regras de frete vêm do manual oficial em PDF.
- **Não Invenção de Chaves ou Dados Ausentes**: Como o manual de políticas não define uma chave PIX fixa, o agente **não alucina** uma chave inventada; ele esclarece com transparência que a chave ou QR Code oficial para pagamento com os 5% de desconto é gerado pela equipe no momento do fechamento da compra pelo WhatsApp oficial da loja (`(67) 3321-4500` ou `(67) 3341-4444`).

### 6. Autenticação de API: Bearer JWT & API Key
Para proteger o backend contra acessos não autorizados, consumo indevido de créditos de IA e scraping de catálogo, a API disponibiliza uma camada de segurança robusta implementada em `src/security.py`:

- **Arquitetura de Segurança Híbrida**:
  - **Atendimento Web Público**: Clientes navegando no site da loja não precisam de cadastro ou senha para consultar instrumentos, garantindo zero fricção na experiência de compra.
  - **Canais Externos & Backend-to-Backend (WhatsApp / CRM / Webhooks)**: Integrações com bots de mensageria (Evolution API, Z-API, Baileys, n8n) e rotas administrativas são protegidas por **Tokens Bearer JWT** (RFC 7519, algoritmo HMAC-SHA256) ou chave direta via cabeçalho `X-API-Key`.
- **Emissão Dinâmica de Tokens JWT (`POST /api/auth/token`)**:
  Permite emitir credenciais com tempo de vida controlado (`JWT_EXPIRATION_HOURS=24`):
  ```bash
  # 1. Solicitar token JWT para o bot do WhatsApp:
  curl -X POST "http://localhost:8000/api/auth/token" \
       -H "Content-Type: application/json" \
       -d '{"client_id": "bot_whatsapp_vendas", "secret_key": "sua-chave-secreta"}'
  
  # Resposta:
  # {"access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer", "expires_in_hours": 24}
  ```
- **Consumo da API com o Token JWT**:
  ```bash
  # 2. Enviar mensagem autenticada:
  curl -X POST "http://localhost:8000/api/chat" \
       -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
       -H "Content-Type: application/json" \
       -d '{"session_id": "5567998123456", "message": "Qual o violão mais vendido?"}'
  ```
- **Ambiente Flexível de Avaliação**:
  - Se a variável `API_SECRET_KEY` estiver vazia no `.env` (padrão de desenvolvimento), a API opera em modo aberto facilitando testes locais e auditorias de código sem necessidade de configurar chaves adicionais.
  - Ao preencher `API_SECRET_KEY=uma-chave-forte`, todas as rotas protegidas passam a exigir automaticamente o token Bearer ou o header `X-API-Key: sua-chave`.

### 7. Blindagem OWASP, Rate Limiting & Política de Cookies (LGPD)
- **Cabeçalhos de Segurança HTTP (Middleware OWASP)**:
  Todas as respostas da aplicação incluem cabeçalhos de defesa ativa:
  - `X-Content-Type-Options: nosniff`: Impede ataques de interpretação forçada de tipo MIME.
  - `X-Frame-Options: SAMEORIGIN`: Protege o chat web contra ataques de clickjacking.
  - `X-XSS-Protection: 1; mode=block`: Bloqueia tentativas de injeção de script refletido.
  - `Referrer-Policy: strict-origin-when-cross-origin`: Resguarda dados de rota em navegações externas.
- **Proteção Anti-DDoS e Rate Limiting**:
  - Algoritmo de janela deslizante (*sliding window*) em memória que monitora o volume de requisições por IP ou sessão.
  - Limite configurável via `RATE_LIMIT_PER_MINUTE` (padrão de 60 requisições/minuto). Caso ultrapassado, o serviço devolve status `HTTP 429 Too Many Requests` com mensagem orientativa, resguardando os custos com a LLM.
- **Política de Cookies e Armazenamento Local (LGPD)**:
  - **Banner Flutuante de Consentimento**: O chat web exibe aviso transparente informando que o armazenamento local (`localStorage`) é utilizado **estritamente para manter a sessão conversacional ativa e preferências de navegação**.
  - **Sem Rastreamento de Terceiros**: A aplicação não utiliza cookies de publicidade, pixel de rastreamento ou compartilhamento de dados analíticos com terceiros.
  - **Modal de Transparência**: O usuário pode clicar em "Ver Detalhes" para consultar as garantias dos Artigos 15, 16 e 18 da LGPD (retenção máxima de 7 dias e direito ao esquecimento imediato).
  - **Endpoint Público de Auditoria**: `GET /api/security/policies` retorna o manifesto JSON completo de conformidade para auditoria externa.

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
| `POST` | `/api/auth/token` | Emissão de token JWT assinado para integrações seguras (WhatsApp / CRM) |
| `GET` | `/api/security/policies` | Declaração pública de conformidade LGPD, rate limiting e política de cookies |
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
