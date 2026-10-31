import pytest
from src.knowledge.policies import consult_policies, get_all_policy_sections

def test_get_all_policy_sections():
    sections = get_all_policy_sections()
    assert "sobre_e_endereco" in sections
    assert "horario_funcionamento" in sections
    assert "formas_pagamento" in sections
    assert "trocas_e_devolucoes" in sections
    assert "frete_e_entregas" in sections
    assert "escopo_e_produtos" in sections

def test_consult_address_and_hours():
    res = consult_policies("onde fica a loja e qual o horário de funcionamento?")
    assert "Rua 14 de Maio" in res
    assert "Campo Grande" in res
    assert "09:00" in res

def test_consult_return_and_cdc():
    res = consult_policies("me arrependi da compra, posso devolver?")
    assert "7 (SETE) DIAS CORRIDOS" in res
    assert "Arrependimento" in res
    assert "Código de Defesa do Consumidor" in res

def test_consult_out_of_scope_accessories():
    res = consult_policies("vocês vendem palhetas e cabos?")
    assert "NÃO COMERCIALIZA ACESSÓRIOS" in res
    assert "EXCLUSIVAMENTE INSTRUMENTOS MUSICAIS" in res

def test_consult_pix_discount():
    res = consult_policies("tem desconto no pix?")
    assert "5% DE DESCONTO" in res
    assert "PIX" in res
