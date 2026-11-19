"""
Fixtures partagées pour tous les tests GUDLFT.
- client            : client de test Flask.
- reset_server_data : réinitialise les variables globales (clubs,
                      competitions) et mocke la persistance sur disque.
"""
import copy
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import server  # noqa: E402

CLUBS = [
    {
        "name": "Simply Lift",
        "email": "john@simplylift.co",
        "points": "13"
    },
    {
        "name": "Iron Temple",
        "email": "admin@irontemple.com",
        "points": "4"
    },
    {
        "name": "She Lifts",
        "email": "kate@shelifts.co.uk",
        "points": "12"
    },
]

COMPETITIONS = [
    {
        "name": "Spring Festival",
        "date": "2026-12-15 10:00:00",
        "numberOfPlaces": 25,
        "totalPlaces": 30,
        "category": "Haltérophilie",
        "location": "Paris Arena",
        "bookings": {},
    },
    {
        "name": "Past Competition",
        "date": "2020-01-01 10:00:00",
        "numberOfPlaces": 10,
        "totalPlaces": 20,
        "category": "Powerlifting",
        "location": "Lyon",
        "bookings": {},
    },
    {
        "name": "Fall Classic",
        "date": "2027-03-22 13:30:00",
        "numberOfPlaces": 4,
        "totalPlaces": 10,
        "category": "Powerlifting",
        "location": "Lyon",
        "bookings": {},
    },
]


@pytest.fixture
def client():
    """Client HTTP Flask configuré pour les tests."""
    server.app.config["TESTING"] = True
    server.app.config["SECRET_KEY"] = "test-secret-key"
    with server.app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_server_data(monkeypatch):
    """Réinitialise les données en mémoire et mocke l'écriture disque."""
    monkeypatch.setattr("server.clubs", copy.deepcopy(CLUBS))
    monkeypatch.setattr("server.competitions", copy.deepcopy(COMPETITIONS))
    monkeypatch.setattr("server.saveClubs", lambda data: None)
    monkeypatch.setattr("server.saveCompetitions", lambda data: None)
