# 📝 Histórico de Alterações (Changelog)

Todas as alterações notáveis deste projeto são registradas neste documento, seguindo as diretrizes do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e os padrões de [Conventional Commits](https://www.conventionalcommits.org/).

---

## [1.1.0] - 2026-10-31

### ✨ Melhorias e Resiliência (Tolerância a Falhas)
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
