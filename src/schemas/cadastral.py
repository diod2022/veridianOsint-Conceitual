from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from src.core.security import so_digitos, normalizar_cpf, normalizar_cnpj, normalizar_telefone, normalizar_email

class CPFInput(BaseModel):
    cpf: str = Field(..., description="CPF do alvo (com ou sem máscara).")
    
    @field_validator("cpf", mode="before")
    @classmethod
    def validate_cpf(cls, v: Union[str, int]) -> str:
        digitos = so_digitos(v)
        if len(digitos) != 11:
            raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")
        return digitos

class CNPJInput(BaseModel):
    cnpj: str = Field(..., description="CNPJ da empresa (com ou sem máscara).")
    
    @field_validator("cnpj", mode="before")
    @classmethod
    def validate_cnpj(cls, v: Union[str, int]) -> str:
        digitos = so_digitos(v)
        if len(digitos) != 14:
            raise ValueError("O CNPJ deve conter exatamente 14 dígitos numéricos.")
        return digitos

class PlacaInput(BaseModel):
    placa: str = Field(..., description="Placa do veículo (padrão antigo ou Mercosul).")
    
    @field_validator("placa", mode="before")
    @classmethod
    def validate_placa(cls, v: str) -> str:
        limpo = str(v).replace("-", "").replace(" ", "").upper()
        if len(limpo) != 7:
            raise ValueError("A placa deve conter 7 caracteres alfanuméricos.")
        return limpo

class BuscaNomeInput(BaseModel):
    nome: str = Field(..., min_length=2, description="Nome completo ou parcial para busca reversa.")
    bairro: Optional[str] = Field(None, description="Filtro opcional de bairro.")
    cidade: Optional[str] = Field(None, description="Filtro opcional de cidade.")
    uf: Optional[str] = Field(None, max_length=2, description="Sigla da UF (2 letras).")

class BuscaTelefoneInput(BaseModel):
    ddd: str = Field(..., description="DDD do telefone (2 dígitos).")
    telefone: str = Field(..., description="Número de telefone (8 ou 9 dígitos).")

class BuscaEmailInput(BaseModel):
    email: str = Field(..., description="Endereço de e-mail pesquisado.")

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return normalizar_email(v)

class BuscaCEPInput(BaseModel):
    cep: str = Field(..., description="CEP com 8 dígitos numéricos.")
