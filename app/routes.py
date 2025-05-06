from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine
from typing import List
from decimal import Decimal, ROUND_HALF_UP


models.Base.metadata.create_all(bind=engine)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/clients", response_model=schemas.Client)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(
        nom=client.nom,
        email=client.email,
        adresse=client.adresse,
        telephone=client.telephone,
        code_client=client.code_client
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.get("/clients", response_model=List[schemas.Client])
def read_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()


@router.post("/factures", response_model=schemas.Facture)
def create_facture(facture: schemas.FactureCreate, db: Session = Depends(get_db)):

    client = db.query(models.Client).filter(models.Client.id_client == facture.id_client).first()
    if not client:
        raise HTTPException(status_code=404, detail="id Client non trouvé")


    total_ht = Decimal("0.00")
    total_ttc = Decimal("0.00")
    lignes_db = []

    for ligne in facture.lignes:
        montant_ht = (ligne.quantite * ligne.prix_unitaire_ht).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        montant_tva = ((montant_ht * ligne.taux_tva) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        montant_ttc = (montant_ht + montant_tva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_ht += montant_ht
        total_ttc += montant_ttc

        db_ligne = models.LigneFacture(
            nom_produit_facture=ligne.nom_produit_facture,
            quantite=ligne.quantite,
            prix_unitaire_ht=ligne.prix_unitaire_ht,
            taux_tva=ligne.taux_tva,
            montant_ht=montant_ht,
            montant_tva=montant_tva,
            montant_ttc=montant_ttc
        )
        lignes_db.append(db_ligne)

    db_facture = models.Facture(
        reference=facture.reference,
        date_facturation=facture.date_facturation,
        date_echeance=facture.date_echeance,
        id_client=facture.id_client,
        conditions_reglement=facture.conditions_reglement,
        total_ht=total_ht.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        total_ttc=total_ttc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        lignes=lignes_db
    )

    db.add(db_facture)
    db.commit()
    db.refresh(db_facture)
    return db_facture


@router.get("/factures", response_model=List[schemas.Facture])
def read_factures(db: Session = Depends(get_db)):
    return db.query(models.Facture).all()


@router.get("/factures/{facture_id}", response_model=schemas.Facture)
def read_facture(facture_id: int, db: Session = Depends(get_db)):
    facture = db.query(models.Facture).filter(models.Facture.id_facture == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return facture
