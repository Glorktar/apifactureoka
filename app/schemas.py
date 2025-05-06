from typing import List
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional


class ClientBase(BaseModel):
    nom: str
    email: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    code_client: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id_client: int

    class Config:
        orm_mode = True

class LigneFactureBase(BaseModel):
    nom_produit_facture: str
    quantite: int
    prix_unitaire_ht: Decimal
    taux_tva: Decimal

class LigneFactureCreate(LigneFactureBase):
    pass

class LigneFacture(LigneFactureBase):
    id_ligne: int
    montant_ht: Decimal
    montant_tva: Decimal
    montant_ttc: Decimal

    class Config:
        orm_mode = True

class FactureBase(BaseModel):
    reference: str
    date_facturation: date
    date_echeance: date
    id_client: int  
    conditions_reglement: str
    total_ht: Decimal
    total_ttc: Decimal

class FactureCreate(FactureBase):
    lignes: List[LigneFactureCreate]

class Facture(FactureBase):
    id_facture: int
    total_ht: Decimal
    total_ttc: Decimal
    lignes: List[LigneFacture] = []

    class Config:
        orm_mode = True
