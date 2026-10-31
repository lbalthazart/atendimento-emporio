# Exemplo 2: Informações Institucionais e Horários de Funcionamento

## Cenário
Cliente pergunta o endereço da loja física, horários de atendimento no final de semana e formas de contato. O agente consulta o manual de políticas para obter os dados oficiais de localização em Campo Grande/MS.

---

### Diálogo

**Cliente:**
> Qual o endereço da loja física de vocês e até que horas fica aberto no sábado?

**Agente (Raciocínio Interno / Tool Calling):**
```json
{
  "tool_call": "consultar_politicas",
  "arguments": {
    "topico": "endereço localização e horário de funcionamento sábado"
  }
}
```

**Retorno da Ferramenta:**
```text
EMPRÓRIO DA MÚSICA - Dados Cadastrais e Localização:
- Razão Social: Empório da Música Instrumentos Musicais Ltda.
- CNPJ: 12.345.678/0001-90 | Fundação: 2008 (mais de 15 anos de história).
- Endereço Físico: Rua 14 de Maio, 3200 – Centro, Campo Grande - MS, CEP: 79202-333.
- Telefone / WhatsApp: (67) 3341-4444 / (67) 3321-4500 | E-mail: contato@emporiodamusica.com.br.

HORÁRIO DE FUNCIONAMENTO (Presencial e WhatsApp):
- Segunda a Sexta-feira: 09:00 às 18:00.
- Sábado: 09:00 às 13:00.
- Domingos e Feriados: Fechado.
```

**Agente (Resposta ao Cliente):**
> Opa, tudo bem? Será um prazer te receber aqui na loja! 🎶
> 
> Estamos localizados no centro de Campo Grande/MS:
> 📍 **Endereço**: Rua 14 de Maio, 3200 – Centro, Campo Grande - MS (CEP: 79202-333).
> 
> Nossos horários de atendimento são:
> - **Segunda a Sexta**: das 09:00 às 18:00
> - **Sábados**: das **09:00 às 13:00**
> - **Domingos e Feriados**: Fechado
> 
> Se precisar tirar qualquer dúvida antes de vir ou reservar um instrumento para testar no showroom, pode nos chamar por aqui ou ligar no (67) 3341-4444. Te esperamos! ✨
