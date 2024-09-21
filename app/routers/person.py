from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.schemas import (
    Pagination,
    PersonRead,
    PersonCreate,
    PersonList,
    PersonFilter,
    PersonReadNatural,
    PersonReadJuridical,
    NaturalPersonDetailsRead,
    JuridicalPersonDetailsRead,
)
from app.models import Person, NaturalPersonDetails, JuridicalPersonDetails
from app.database import get_session
from sqlalchemy import or_, func

router = APIRouter(
    prefix="/persons",
    tags=["Persons"],
)


@router.post("/", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def create_person(person: PersonCreate, db: Session = Depends(get_session)):
    # Create base person
    db_person = Person(
        type=person.type,
        active=person.active,
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)

    if person.type == "natural":
        details = NaturalPersonDetails(
            person_id=db_person.id,
            curp=person.details.curp,
            rfc=person.details.rfc,
            name=person.details.name,
            first_last_name=person.details.first_last_name,
            second_last_name=person.details.second_last_name,
            date_of_birth=person.details.date_of_birth,
        )
        db.add(details)
    elif person.type == "juridical":
        details = JuridicalPersonDetails(
            person_id=db_person.id,
            rfc=person.details.rfc,
            legal_name=person.details.legal_name,
            incorporation_date=person.details.incorporation_date,
        )
        db.add(details)
    else:
        raise HTTPException(status_code=400, detail="Invalid person type")

    db.commit()
    db.refresh(db_person)

    # Assemble response
    if person.type == "natural":
        db_details = (
            db.query(NaturalPersonDetails).filter_by(person_id=db_person.id).first()
        )
        response = PersonReadNatural(
            id=db_person.id,
            type=db_person.type,
            active=db_person.active,
            created_at=db_person.created_at,
            updated_at=db_person.updated_at,
            deleted_at=db_person.deleted_at,
            details=NaturalPersonDetailsRead(
                person_id=db_details.person_id,
                curp=db_details.curp,
                rfc=db_details.rfc,
                name=db_details.name,
                first_last_name=db_details.first_last_name,
                second_last_name=db_details.second_last_name,
                date_of_birth=db_details.date_of_birth,
                created_at=db_details.created_at,
                full_name=db_details.full_name,
            ),
        )
    else:
        db_details = (
            db.query(JuridicalPersonDetails).filter_by(person_id=db_person.id).first()
        )
        response = PersonReadJuridical(
            id=db_person.id,
            type=db_person.type,
            active=db_person.active,
            created_at=db_person.created_at,
            updated_at=db_person.updated_at,
            deleted_at=db_person.deleted_at,
            details=JuridicalPersonDetailsRead(
                person_id=db_details.person_id,
                rfc=db_details.rfc,
                legal_name=db_details.legal_name,
                incorporation_date=db_details.incorporation_date,
                created_at=db_details.created_at,
            ),
        )

    return response


@router.get("/", response_model=PersonList)
def list_persons(
    filter: PersonFilter = Depends(),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_session),
):
    query = db.query(Person).filter(Person.deleted_at.is_(None))

    # Apply filters
    if filter.type:
        query = query.filter(Person.type == filter.type)
    if filter.active is not None:
        query = query.filter(Person.active == filter.active)
    if filter.name:
        # Assuming natural persons have a `name` field in `natural_person_details`
        query = query.join(NaturalPersonDetails, isouter=True).filter(
            or_(
                NaturalPersonDetails.name.ilike(f"%{filter.name}%"),
                JuridicalPersonDetails.legal_name.ilike(f"%{filter.name}%"),
            )
        )

    total = query.count()

    persons = (
        query.order_by(Person.id).offset(pagination.skip).limit(pagination.limit).all()
    )

    result = []
    for person in persons:
        if person.type == "natural":
            details = (
                db.query(NaturalPersonDetails).filter_by(person_id=person.id).first()
            )
            person_data = PersonReadNatural(
                id=person.id,
                type=person.type,
                active=person.active,
                created_at=person.created_at,
                updated_at=person.updated_at,
                deleted_at=person.deleted_at,
                details=NaturalPersonDetailsRead(
                    person_id=details.person_id,
                    curp=details.curp,
                    rfc=details.rfc,
                    name=details.name,
                    first_last_name=details.first_last_name,
                    second_last_name=details.second_last_name,
                    date_of_birth=details.date_of_birth,
                    created_at=details.created_at,
                    full_name=details.full_name,
                ),
            )
        else:
            details = (
                db.query(JuridicalPersonDetails).filter_by(person_id=person.id).first()
            )
            person_data = PersonReadJuridical(
                id=person.id,
                type=person.type,
                active=person.active,
                created_at=person.created_at,
                updated_at=person.updated_at,
                deleted_at=person.deleted_at,
                details=JuridicalPersonDetailsRead(
                    person_id=details.person_id,
                    rfc=details.rfc,
                    legal_name=details.legal_name,
                    incorporation_date=details.incorporation_date,
                    created_at=details.created_at,
                ),
            )
        result.append(person_data)

    return PersonList(total=total, items=result)


@router.delete("/{person_id}", response_model=PersonRead)
def delete_person(person_id: int, db: Session = Depends(get_session)):
    person = db.query(Person).filter_by(id=person_id, deleted_at=None).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    person.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(person)

    # Assemble response
    if person.type == "natural":
        details = db.query(NaturalPersonDetails).filter_by(person_id=person.id).first()
        response = PersonReadNatural(
            id=person.id,
            type=person.type,
            active=person.active,
            created_at=person.created_at,
            updated_at=person.updated_at,
            deleted_at=person.deleted_at,
            details=NaturalPersonDetailsRead(
                person_id=details.person_id,
                curp=details.curp,
                rfc=details.rfc,
                name=details.name,
                first_last_name=details.first_last_name,
                second_last_name=details.second_last_name,
                date_of_birth=details.date_of_birth,
                created_at=details.created_at,
                full_name=details.full_name,
            ),
        )
    else:
        details = (
            db.query(JuridicalPersonDetails).filter_by(person_id=person.id).first()
        )
        response = PersonReadJuridical(
            id=person.id,
            type=person.type,
            active=person.active,
            created_at=person.created_at,
            updated_at=person.updated_at,
            deleted_at=person.deleted_at,
            details=JuridicalPersonDetailsRead(
                person_id=details.person_id,
                rfc=details.rfc,
                legal_name=details.legal_name,
                incorporation_date=details.incorporation_date,
                created_at=details.created_at,
            ),
        )

    return response
