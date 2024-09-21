import pytest
from datetime import datetime
from sqlalchemy import text
from fastapi import status
from fastapi.testclient import TestClient
from app.database import engine, get_session
from app.main import app

from app.models import Person, NaturalPersonDetails, JuridicalPersonDetails
from app.routers.person import create_person

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    yield
    with engine.begin() as connection:
        connection.execute(text('TRUNCATE person CASCADE'))


@pytest.fixture
def natural_person_data():
    return {
        "type": "natural",
        "active": True,
        "details": {
            "curp": "CURP12345678901234",
            "rfc": "RFC123456789",
            "name": "John",
            "first_last_name": "Doe",
            "second_last_name": "Smith",
            "date_of_birth": "1990-01-01",
            "full_name": "JOHN DOE SMITH", # this is generated in the DB
        },
    }


@pytest.fixture
def juridical_person_data():
    return {
        "type": "juridical",
        "active": True,
        "details": {
            "rfc": "RFC987654321",
            "legal_name": "Acme Corporation",
            "incorporation_date": "2000-05-15",
        },
    }


def create_person(person_data: dict):
    response = client.post("/persons", json=person_data)
    response.raise_for_status()
    return response.json()


def test_create_natural_person(natural_person_data):
    response = client.post("/persons", json=natural_person_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["type"] == natural_person_data["type"]
    assert data["active"] == natural_person_data["active"]
    assert data["details"]["curp"] == natural_person_data["details"]["curp"]
    assert data["details"]["rfc"] == natural_person_data["details"]["rfc"]
    assert data["details"]["name"] == natural_person_data["details"]["name"]
    assert (
        data["details"]["first_last_name"]
        == natural_person_data["details"]["first_last_name"]
    )
    assert (
        data["details"]["second_last_name"]
        == natural_person_data["details"]["second_last_name"]
    )
    assert (
        data["details"]["date_of_birth"]
        == natural_person_data["details"]["date_of_birth"]
    )
    assert data["details"]["full_name"] == natural_person_data["details"]["full_name"]


def test_create_juridical_person(juridical_person_data):
    response = client.post("/persons", json=juridical_person_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["type"] == juridical_person_data["type"]
    assert data["active"] == juridical_person_data["active"]
    assert data["details"]["rfc"] == juridical_person_data["details"]["rfc"]
    assert (
        data["details"]["legal_name"] == juridical_person_data["details"]["legal_name"]
    )
    assert (
        data["details"]["incorporation_date"]
        == juridical_person_data["details"]["incorporation_date"]
    )


def test_get_persons_empty():
    response = client.get("/persons")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_get_persons_with_data(natural_person_data, juridical_person_data):
    # Create natural person
    create_person(natural_person_data)

    # Create juridical person
    create_person(juridical_person_data)

    response = client.get("/persons")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Verify the first person
    person1 = data["items"][0]
    assert person1["type"] in ["natural", "juridical"]
    assert person1["active"] is True
    assert "details" in person1

    # Further assertions can be added based on ordering


def test_get_persons_pagination(natural_person_data):
    # Create 15 natural persons
    for i in range(15):
        person_data = natural_person_data.copy()
        person_data["details"]["name"] = f"Person {i}"
        person_data["details"]["curp"] = f"CURPXXXXXXXXXXXX{i:02d}"
        create_person(person_data)

    # Request first page
    response = client.get("/persons?skip=0&limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 10

    # Request second page
    response = client.get("/persons?skip=10&limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 5


def test_get_persons_filter_type(
    natural_person_data, juridical_person_data
):
    # Create one natural and one juridical person
    create_person(natural_person_data)
    create_person(juridical_person_data)

    # Filter by type=natural
    response = client.get("/persons?type=natural")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == "natural"

    # Filter by type=juridical
    response = client.get("/persons?type=juridical")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == "juridical"


def test_get_persons_filter_active(
    natural_person_data, juridical_person_data
):
    # Create active and inactive persons
    natural_active = natural_person_data.copy()
    natural_active["active"] = True
    create_person(natural_active)

    juridical_inactive = juridical_person_data.copy()
    juridical_inactive["active"] = False
    create_person(juridical_inactive)

    # Filter active=True
    response = client.get("/persons?active=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["active"] is True

    # Filter active=False
    response = client.get("/persons?active=false")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["active"] is False


def test_get_persons_filter_name(
    natural_person_data, juridical_person_data
):
    # Create persons with specific names
    natural_person1 = natural_person_data.copy()
    natural_person1["details"]["name"] = "Alice"
    natural_person1["details"]["full_name"] = "Alice Wonderland"
    create_person(natural_person1)

    juridical_person1 = juridical_person_data.copy()
    juridical_person1["details"]["legal_name"] = "Wonderland LLC"
    create_person(juridical_person1)

    # Search for 'Alice'
    response = client.get("/persons?name=Alice")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert "Alice" in data["items"][0]["details"]["name"]

    # Search for 'Wonderland'
    response = client.get("/persons?name=Wonderland")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 2  # Both natural and juridical have 'Wonderland'


def test_delete_person_natural(natural_person_data):
    # Create a natural person
    person = create_person(natural_person_data)

    # Delete the person
    response = client.delete(f"/persons/{person['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == person['id']
    assert data["deleted_at"] is not None

    # Verify the person is marked as deleted
    db = next(get_session())
    try:
        deleted_person = db.query(Person).filter_by(id=person['id']).first()
        assert deleted_person.deleted_at is not None
    finally:
        db.close()

    # Attempt to delete again
    response = client.delete(f"/persons/{person['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_person_juridical(juridical_person_data):
    # Create a juridical person
    person = create_person(juridical_person_data)

    # Delete the person
    response = client.delete(f"/persons/{person['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == person['id']
    assert data["deleted_at"] is not None

    # Verify the person is marked as deleted
    db = next(get_session())
    try:
        deleted_person = db.query(Person).filter_by(id=person['id']).first()
        assert deleted_person.deleted_at is not None
    finally:
        db.close()

    # Attempt to delete again
    response = client.delete(f"/persons/{person['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_person_not_found():
    # Attempt to delete a non-existing person
    response = client.delete("/persons/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Person not found"
