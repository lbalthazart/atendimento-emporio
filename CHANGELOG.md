# 📝 Histórico de Alterações (Changelog)

Todas as alterações notáveis deste projeto são registradas neste documento, seguindo as diretrizes do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e os padrões de [Conventional Commits](https://www.conventionalcommits.org/).

---

## [1.1.0] - 2026-10-31

### ✨ Melhorias e Resiliência (Tolerância a Falhas)
- **Expansão do Roadmap de Negócio no README**: Documentação de melhorias futuras com planejamento do Painel do Administrador (login seguro, MFA, console de chat de transbordo humano durante a pausa da IA) e Módulo de CRM integrado com visão 360° dos clientes ativos e auditoria LGPD (`docs: add admin login, human takeover chat and customer CRM to roadmap`).
- **Segurança de API, JWT & Rate Limiting**: Implementação de módulo `src/security.py` com suporte a autenticação por **Bearer JWT** e **API Key** (`X-API-Key`), proteção contra ataques de negação de serviço e abuso de créditos com limitador de taxa (60 req/min), e inclusão de cabeçalhos de segurança OWASP (`nosniff`, `SAMEORIGIN`, `strict-origin-when-cross-origin`) (`feat: implement JWT auth, rate limiting and security headers`).
- **Banner de Cookies & Modal de Privacidade LGPD**: Inclusão de banner flutuante de consentimento de cookies essenciais e armazenamento local (localStorage) no chat web, com modal detalhando a política de retenção de 7 dias e direito ao esquecimento sob a Lei 13.709/2018 (`feat: add cookie consent banner and privacy modal`).
- **Correção da Busca de Itens Mais Caros e Ordenação**: Inclusão do parâmetro `ordenar_por` (`preco_desc` e `preco_asc`) na ferramenta `consultar_catalogo` e na query SQL do SQLite, resolvendo o bug onde perguntas sobre o 'item mais caro' retornavam o ukulele mais barato em vez do Teclado Nord Synth 2 Pro (R$ 19.567) e da Gibson Les Paul (R$ 18.900) (`fix: support price ordering and fix most expensive item query bug`).
- **Alinhamento do Avatar do Atendente**: Correção do layout Flexbox para fixar o avatar do consultor no topo superior esquerdo da mensagem (`items-start`), eliminando o desalinhamento visual observado em mensagens longas (`fix: align assistant avatar to top-left of message bubble`).
- **Redesign Visual Comercial & Humanizado**: Refatoração completa da interface de chat inspirada em canais de atendimento premium (WhatsApp/Intercom), removendo badges técnicos automáticos da visão do cliente, introduzindo tipografia 'Plus Jakarta Sans', balões com horários e confirmação de leitura (`✓✓`), animação clássica de digitação com três pontinhos pulsantes e botão discreto de alternância de 'Inspecionar Tools' para avaliadores técnicos (`feat: redesign web chat with humanized retail UI and inspector mode`).
- **Envio Conjunto de Imagem + Legenda (Estilo WhatsApp)**: Implementação de pré-visualização de fotos anexadas no chat com barra de anexo e botão de remoção, permitindo que o usuário digite sua pergunta (ex: *"vocês têm dessa?"*) junto com a imagem antes do envio (`feat: add image attachment preview and combined photo+text submission`).
- **Reconhecimento Visual no Agente com Busca de Estoque**: Instrução explícita ao assistente para tratar a pré-análise de visão como instrumento visto diretamente, acionando automaticamente a ferramenta `consultar_catalogo` para verificar modelos em estoque com preços e desconto PIX (`feat: enhance multimodal vision prompt and catalog lookups for photos`).
- **Fila de Mensagens Interativa (Debounce)**: Ativação da fila inteligente de mensagens no Web Chat com janela de 2.2 segundos para agrupar frases rápidas sequenciais em um único raciocínio coerente (`feat: activate interactive message debouncing queue in web chat UI`).
- **Layout Fixo e Rolagem Suave**: Ancoragem permanente da caixa de texto no rodapé com `shrink-0` e `h-screen overflow-hidden`, garantindo que apenas a área de mensagens role para cima (`fix: dock chat input to bottom with flexbox shrink-0`).
- **Garantia de Zero Alucinação**: Remoção de qualquer chave PIX presumida, alinhando a resposta estritamente ao manual da loja (a chave/QR Code oficial é gerado na finalização da compra pelo WhatsApp oficial da equipe) (`fix: enforce zero hallucination for PIX keys`).
- **Cadeia de Contingência Multi-Modelos**: Implementação de fallbacks automáticos no OpenRouter (`openai/gpt-4o-mini` ➔ `google/gemini-2.0-flash-001` ➔ `meta-llama/llama-3.3-70b-instruct` ➔ `anthropic/claude-3.5-haiku`) caso algum provedor oscile (`fix: add multi-model fallbacks`).
- **Higienização de Mensagens (`sanitize_messages`)**: Sanitizador estrito de mensagens antes do envio à API, eliminando mensagens `tool` órfãs que causavam erro 400 em conversas de múltiplos turnos (`fix: add multi-model fallbacks, message sanitization`).
- **Renderizador de Markdown (`marked.js`)**: Integração de biblioteca para renderizar negrito, itálico, listas e badges técnicos formatados no Web Chat, eliminando a exibição de asteriscos crus na tela (`fix: improve catalog presentation formatting`).
- **Humanização do Prompt de Catálogo**: Reformulação das respostas de catálogo para exibição em uma linha fluida por instrumento, proibindo dumps mecânicos de planilhas (`fix: improve catalog presentation formatting`).

---

## [1.0.0] - 2026-10-31

### 🚀 Lançamento Inicial dos Entregáveis do Desafio
- **Setup e Governança**:
  - Inicialização do repositório Git com histórico real de progresso e rastreamento de branch `main` (`chore: initial commit`).
  - Configuração rigorosa de `.gitignore` para bloquear `.env`, bancos de dados locais, caches e manter privado o PDF de especificação (`chore: untrack challenge pdf in gitignore`).
  - Documentação completa no `README.md` com justificativas técnicas, arquitetura de retrieval, estratégia de prompt, conformidade LGPD e transparência no uso de IA (`docs: add comprehensive initial README`).
- **Camada de Dados & Relacional**:
  - Ingestão automatizada de todos os CSVs fornecidos (`products`, `categories`, `orders`, `order_items`, `customers`, `promotions`) para SQLite indexado (`feat: implement SQLite database ingestion`).
  - Funções com filtros exatos de preço, categorias, estoque e cálculo de promoções ativas sem alucinações numéricas.
- **Motor de Políticas e CDC**:
  - Extração e indexação estruturada do manual interno em PDF da loja, cobrindo direito de arrependimento (7 dias corridos sem custo de frete), garantia legal de 90 dias, horários e política de frete para Campo Grande (`feat: implement store policies parser`).
- **Memória de Sessão & LGPD**:
  - Implementação de gerenciador de memória com expurgo automático após **7 dias (TTL)** conforme a Lei Geral de Proteção de Dados (`feat: add session memory with 7-day LGPD TTL`).
  - Endpoints de exclusão imediata (Direito ao Esquecimento - Art. 18 LGPD).
  - Suporte a pausa temporária de IA para transbordo humano (`is_human_paused`).
- **Agente Autônomo com Tool Calling**:
  - Orquestrador ReAct assíncrono conectado ao OpenRouter (`feat: implement agent core with tool calling`).
  - 5 ferramentas integradas: `consultar_catalogo`, `consultar_detalhes_produto`, `consultar_status_pedido`, `consultar_politicas` e `solicitar_atendimento_humano`.
  - *System Prompt Shield* com regras inegociáveis de persona, limitação de escopo exclusivo a instrumentos e defesa ativa contra *prompt injection*.
- **API RESTful e Interface Web**:
  - Servidor FastAPI assíncrono com Swagger interativo (`/docs`) e rotas `/api/chat`, `/api/media` e `/health` (`feat: add FastAPI REST endpoints`).
  - Interface Web moderna embutida servida diretamente na raiz (`/`).
- **Containerização & Demonstração**:
  - `Dockerfile` e `docker-compose.yml` para execução rápida com 1 comando (`feat: add Docker and docker-compose configurations`).
  - 5 transcrições de conversas e cenários não-triviais salvas na pasta `examples/` (`docs: add comprehensive interaction examples`).
