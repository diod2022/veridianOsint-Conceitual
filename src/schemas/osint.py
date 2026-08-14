from pydantic import BaseModel, Field
from typing import Optional, Union

class WhoisInput(BaseModel):
    target: str = Field(..., description="Domínio (ex: 'exemplo.com'), IP ('8.8.8.8') ou e-mail a consultar")
    ignore_raw_text: Optional[bool] = Field(True, description="Se True, omite o texto bruto desestruturado poupando tokens")
    hard_refresh: Optional[bool] = Field(False, description="Se True, ignora cache local e força nova chamada na API")

class IPInput(BaseModel):
    ip: str = Field(..., description="Endereço IPv4 ou IPv6 a consultar")

class BreachUniversalInput(BaseModel):
    query: Union[str, int] = Field(..., description="Termo de pesquisa de vazamentos (e-mail, usuário, CPF, IP, telefone)")
    tipo: Optional[str] = Field("auto", description="Tipo de dado ('auto', 'email', 'user', 'cpf', 'ip', 'phone')")

class WebDorksInput(BaseModel):
    query: str = Field(..., description="Query de busca avançada no Google (Google Dork, ex: 'filetype:pdf site:gov.br')")
    num_results: Optional[int] = Field(10, description="Quantidade de resultados a retornar", ge=1, le=50)

class WaybackInput(BaseModel):
    url: str = Field(..., description="URL do site para buscar registros históricos no Internet Archive")
