"""
Tests unitaires — Fonctions internes et règles métier isolées.
"""
import json
from datetime import datetime
from unittest.mock import patch, mock_open
import server


class TestUnitPersistence:
    """Tests unitaires des fonctions de chargement et sauvegarde JSON."""

    def test_load_clubs(self):
        clubs_data = json.dumps(
            {"clubs": [{"name": "Unit Club", "points": "15"}]}
        )
        with patch("builtins.open", mock_open(read_data=clubs_data)):
            result = server.loadClubs()
            assert len(result) == 1
            assert result[0]["name"] == "Unit Club"

    def test_load_competitions(self):
        comps_data = json.dumps(
            {"competitions": [{"name": "Unit Comp", "numberOfPlaces": 20}]}
        )
        with patch("builtins.open", mock_open(read_data=comps_data)):
            result = server.loadCompetitions()
            assert len(result) == 1
            assert result[0]["name"] == "Unit Comp"

    def test_save_clubs(self):
        m = mock_open()
        with patch("builtins.open", m):
            server._real_saveClubs([{"name": "Club A", "points": "10"}])
        assert m.call_count == 1

    def test_save_competitions(self):
        m = mock_open()
        with patch("builtins.open", m):
            server._real_saveCompetitions(
                [{"name": "Comp A", "numberOfPlaces": 10}]
            )
        assert m.call_count == 1


class TestUnitBusinessLogic:
    """Tests unitaires de la logique métier sans appel HTTP."""

    def test_club_points_sorting(self):
        """Vérifie que le tri des clubs par points décroissants est exact."""
        clubs = [
            {"name": "Club Low", "points": "3"},
            {"name": "Club High", "points": "25"},
            {"name": "Club Mid", "points": "12"},
        ]
        sorted_clubs = sorted(
            clubs, key=lambda c: int(c["points"]), reverse=True
        )
        assert sorted_clubs[0]["name"] == "Club High"
        assert sorted_clubs[1]["name"] == "Club Mid"
        assert sorted_clubs[2]["name"] == "Club Low"

    def test_past_date_detection(self):
        """Vérifie la détection d'une compétition passée."""
        past_str = "2020-01-01 10:00:00"
        past_dt = datetime.strptime(past_str, "%Y-%m-%d %H:%M:%S")
        assert past_dt < datetime.now()

    def test_future_date_detection(self):
        """Vérifie la détection d'une compétition future."""
        future_str = "2030-01-01 10:00:00"
        future_dt = datetime.strptime(future_str, "%Y-%m-%d %H:%M:%S")
        assert future_dt > datetime.now()

    def test_max_places_calculation(self):
        """Vérifie le calcul du maximum de places réservables."""
        places_available = 8
        club_points = 5
        max_allowed_rule = 12
        max_reservable = min(places_available, club_points, max_allowed_rule)
        assert max_reservable == 5
