from fastapi import APIRouter, Depends, HTTPException, Path
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

@router.post("/produits", response_model=schemas.Produit)
def create_produit(produit: schemas.ProduitCreate, db: Session = Depends(get_db)):
    db_produit = models.Produit(
        nom=produit.nom,
        description=produit.description,
        prix_unitaire_ht=produit.prix_unitaire_ht,
        id_tva=produit.id_tva
    )
    #db_produit = Produit(**produit.dict())
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

@router.get("/produits", response_model=List[schemas.Produit])
def read_produits(db: Session = Depends(get_db)):
    return db.query(models.Produit).all()

@router.put("/produits/{produit_id}", response_model=schemas.Produit)
def update_produit(produit_id: int, produit_update: schemas.ProduitUpdate, db: Session = Depends(get_db)):
    produit = db.query(models.Produit).filter(models.Produit.id == produit_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    update_data = produit_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(produit, key, value)

    db.commit()
    db.refresh(produit)
    return produit


@router.post("/tvas", response_model=schemas.Tva)
def create_tva(tva: schemas.TvaCreate, db: Session = Depends(get_db)):
    db_tva = models.Tva(
        taux=tva.taux,
        description=tva.description,
        date_debut=tva.date_debut,
        date_fin=tva.date_fin
    )
    db.add(db_tva)
    db.commit()
    db.refresh(db_tva)
    return db_tva

@router.get("/tvas", response_model=List[schemas.Tva])
def read_tvas(db: Session = Depends(get_db)):
    return db.query(models.Tva).all()


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

@router.put("/factures/{facture_id}/ligne/{id_ligne}", response_model=schemas.LigneFacture)
def update_ligne_facture(
    facture_id: int,
    id_ligne: int,
    ligne_update: schemas.LigneFactureCreate,
    db: Session = Depends(get_db)
):
    # Vérification de l'existence de la ligne
    ligne = db.query(models.LigneFacture).filter(
        models.LigneFacture.id_ligne == id_ligne,
        models.LigneFacture.id_facture == facture_id
    ).first()
    if not ligne:
        raise HTTPException(status_code=404, detail="Ligne de facture non trouvée")

    # Mise à jour de la ligne avec recalculs
    montant_ht = (ligne_update.quantite * ligne_update.prix_unitaire_ht).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    montant_tva = ((montant_ht * ligne_update.taux_tva) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    montant_ttc = (montant_ht + montant_tva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    ligne.nom_produit_facture = ligne_update.nom_produit_facture
    ligne.quantite = ligne_update.quantite
    ligne.prix_unitaire_ht = ligne_update.prix_unitaire_ht
    ligne.taux_tva = ligne_update.taux_tva
    ligne.montant_ht = montant_ht
    ligne.montant_tva = montant_tva
    ligne.montant_ttc = montant_ttc

    db.commit()

    # Récupération et recalcul des totaux de la facture
    facture = db.query(models.Facture).filter(models.Facture.id_facture == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    total_ht = Decimal("0.00")
    total_ttc = Decimal("0.00")

    for l in facture.lignes:
        total_ht += l.montant_ht
        total_ttc += l.montant_ttc

    facture.total_ht = total_ht.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    facture.total_ttc = total_ttc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    db.commit()
    db.refresh(ligne)
    return ligne


@router.post("/factures/{facture_id}/ligne", response_model=schemas.LigneFacture)
def add_ligne_to_facture(
    facture_id: int,
    ligne_data: schemas.LigneFactureCreate,
    db: Session = Depends(get_db)
):
    # Vérification que la facture existe
    facture = db.query(models.Facture).filter(models.Facture.id_facture == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    # Calculs des montants
    montant_ht = (ligne_data.quantite * ligne_data.prix_unitaire_ht).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    montant_tva = ((montant_ht * ligne_data.taux_tva) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    montant_ttc = (montant_ht + montant_tva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Création de la ligne
    nouvelle_ligne = models.LigneFacture(
        id_facture=facture_id,
        nom_produit_facture=ligne_data.nom_produit_facture,
        quantite=ligne_data.quantite,
        prix_unitaire_ht=ligne_data.prix_unitaire_ht,
        taux_tva=ligne_data.taux_tva,
        montant_ht=montant_ht,
        montant_tva=montant_tva,
        montant_ttc=montant_ttc,
    )

    db.add(nouvelle_ligne)
    db.commit()

    # Recalcul des totaux de la facture
    total_ht = Decimal("0.00")
    total_ttc = Decimal("0.00")
    for l in facture.lignes:
        total_ht += l.montant_ht
        total_ttc += l.montant_ttc

    facture.total_ht = total_ht.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    facture.total_ttc = total_ttc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    db.commit()
    db.refresh(nouvelle_ligne)
    return nouvelle_ligne

@router.delete("/factures/{facture_id}/ligne/{ligne_id}", status_code=204)
def delete_ligne_facture(
    facture_id: int,
    ligne_id: int,
    db: Session = Depends(get_db)
):
    # Vérification que la facture existe
    facture = db.query(models.Facture).filter(models.Facture.id_facture == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    # Vérification que la ligne existe et appartient à la facture
    ligne = db.query(models.LigneFacture).filter(
        models.LigneFacture.id_ligne == ligne_id,
        models.LigneFacture.id_facture == facture_id
    ).first()
    if not ligne:
        raise HTTPException(status_code=404, detail="Ligne de facture non trouvée")

    # Suppression de la ligne
    db.delete(ligne)
    db.commit()

    # Recalcul des totaux de la facture
    lignes_restantes = db.query(models.LigneFacture).filter(models.LigneFacture.id_facture == facture_id).all()
    total_ht = sum(l.montant_ht for l in lignes_restantes)
    total_ttc = sum(l.montant_ttc for l in lignes_restantes)

    facture.total_ht = Decimal(total_ht).quantize(Decimal("0.01"))
    facture.total_ttc = Decimal(total_ttc).quantize(Decimal("0.01"))
    db.commit()


