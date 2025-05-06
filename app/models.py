from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Client(Base):
    __tablename__ = "client"

    id_client = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    code_client = Column(String, nullable=True)

    factures = relationship("Facture", back_populates="client")

class Facture(Base):
    __tablename__ = "facture"

    id_facture = Column(Integer, primary_key=True, index=True)
    reference = Column(String, nullable=False)
    date_facturation = Column(Date, nullable=False)
    date_echeance = Column(Date, nullable=False)
    id_client = Column(Integer, ForeignKey("client.id_client"), nullable=False)
    total_ht = Column(String, nullable=False)
    total_ttc = Column(String, nullable=False)
    conditions_reglement = Column(String, nullable=True)

    client = relationship("Client", back_populates="factures")
    lignes = relationship("LigneFacture", back_populates="facture", cascade="all, delete")


class LigneFacture(Base):
    __tablename__ = "ligne_facture"

    id_ligne = Column(Integer, primary_key=True)
    id_facture = Column(Integer, ForeignKey("facture.id_facture", ondelete="CASCADE"))
    nom_produit_facture = Column(String(100), nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_unitaire_ht = Column(Numeric(10, 2), nullable=False)
    taux_tva = Column(Numeric(5, 2), nullable=False)
    montant_ht = Column(Numeric(5, 2), nullable=False)
    montant_tva = Column(Numeric(5, 2), nullable=False)
    montant_ttc = Column(Numeric(5, 2), nullable=False)

    facture = relationship("Facture", back_populates="lignes")
