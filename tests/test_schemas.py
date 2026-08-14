"""
Testes automatizados para validação de Schemas Pydantic v2
"""
import pytest
from pydantic import ValidationError
from src.schemas.cadastral import CPFInput, CNPJInput, PlacaInput, BuscaTelefoneInput
from src.schemas.judicial import ConsultaOABInput
from src.schemas.social import InstagramUserInput, LinkedInProfileInput

def test_cpf_input_validation():
    inp = CPFInput(cpf="123.456.789-00")
    assert inp.cpf == "12345678900"
    
    with pytest.raises(ValidationError):
        CPFInput(cpf="123") # Menor que 11 dígitos

def test_cnpj_input_validation():
    inp = CNPJInput(cnpj="12.345.678/0001-90")
    assert inp.cnpj == "12345678000190"

def test_placa_input_validation():
    inp = PlacaInput(placa="abc-1234")
    assert inp.placa == "ABC1234"
    inp_mercosul = PlacaInput(placa="abc1d23")
    assert inp_mercosul.placa == "ABC1D23"

def test_oab_input_validation():
    inp = ConsultaOABInput(oab_numero="7008/MS")
    assert inp.oab_numero == "7008"
    assert inp.oab_estado == "MS"

def test_social_input_validation():
    ig = InstagramUserInput(username="@usuario_alvo")
    assert ig.username == "usuario_alvo"
