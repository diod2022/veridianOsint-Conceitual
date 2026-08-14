from pydantic import BaseModel, Field, model_validator
from typing import Optional, Union
from src.core.security import normalizar_oab

class ConsultaOABInput(BaseModel):
    oab_numero: str = Field(..., description="Número da OAB (ex: '7008', '5485', '7008/MS' ou 'OAB/MS 7008').")
    oab_estado: str = Field("", description="Sigla do Estado da OAB (ex: 'MS', 'SP', 'RJ'). Opcional se contido no número.")
    oab_tipo: str = Field("ADVOGADO", description="Tipo de inscrição OAB (padrão 'ADVOGADO').")
    max_paginas: int = Field(50, ge=1, le=100, description="Máximo de páginas a baixar (cada página = 20 processos).")
    ignore_cache: bool = Field(False, description="Se True, força nova consulta na API ignorando cache local.")

    @model_validator(mode="after")
    def extrair_oab_e_uf(self):
        num, uf = normalizar_oab(self.oab_numero, self.oab_estado)
        self.oab_numero = num
        if uf:
            self.oab_estado = uf
        return self

class ConsultaProcessoInput(BaseModel):
    numero_processo: str = Field(..., description="Número CNJ do processo (ex: '1415618-82.2026.8.12.0000').")
    dataset_code: str = Field("bdclawsuitbasicdata", description="Código do dataset desejado.")
