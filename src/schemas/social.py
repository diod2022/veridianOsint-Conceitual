from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union

class InstagramUserInput(BaseModel):
    username: str = Field(..., description="Nome de usuário do Instagram (sem '@').")

    @field_validator("username", mode="before")
    @classmethod
    def clean_username(cls, v: str) -> str:
        return str(v).strip().replace("@", "")

class InstagramPostsInput(BaseModel):
    user_id: Union[str, int] = Field(..., description="ID numérico (pk) do usuário do Instagram.")
    page_id: Optional[str] = Field(None, description="Cursor para paginação.")
    end_cursor: Optional[str] = Field(None, description="Cursor alternativo de paginação.")

class LinkedInProfileInput(BaseModel):
    linkedin_url: str = Field(..., description="URL completa do perfil no LinkedIn.")

class LinkedInEmailInput(BaseModel):
    profile_url: str = Field(..., description="URL completa do perfil no LinkedIn.")
    skip_smtp: bool = Field(False, description="Se True, pula validação de existência SMTP.")

class TikTokProfileInput(BaseModel):
    handle: str = Field(..., description="Nome de usuário do TikTok (sem '@').")

    @field_validator("handle", mode="before")
    @classmethod
    def clean_handle(cls, v: str) -> str:
        return str(v).strip().replace("@", "")

class FacebookUIDInput(BaseModel):
    facebook_profile_uid: Union[str, int] = Field(..., description="UID do perfil do Facebook.")
