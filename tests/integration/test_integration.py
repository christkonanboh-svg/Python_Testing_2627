"""
Tests d'intégration — Requêtes HTTP complètes via Flask Test Client.

Couverture :
  - GET  /                    -> index
  - POST /showSummary         -> login par email
  - GET  /book/<comp>/<club>  -> page de réservation
  - POST /purchasePlaces      -> achat de places (happy + sad paths)
  - GET  /pointsDisplay       -> classement public
  - GET  /leaderboard         -> alias classement
  - GET  /logout              -> déconnexion
"""
import server


# ===========================================================================
# 1. Route index — GET /
# ===========================================================================
class TestIndex:
    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_form(self, client):
        response = client.get("/")
        assert b"showSummary" in response.data or b"email" in response.data

    def test_index_shows_public_link(self, client):
        """Affiche un lien vers le classement public."""
        response = client.get("/")
        assert (
            b"pointsDisplay" in response.data or
            b"classement" in response.data.lower()
        )


# ===========================================================================
# 2. Route showSummary — POST /showSummary
# ===========================================================================
class TestShowSummary:
    def test_valid_email_returns_200(self, client):
        response = client.post(
            "/showSummary", data={"email": "john@simplylift.co"}
        )
        assert response.status_code == 200

    def test_valid_email_shows_welcome_page(self, client):
        response = client.post(
            "/showSummary", data={"email": "john@simplylift.co"}
        )
        assert b"Simply Lift" in response.data

    def test_valid_email_shows_competitions(self, client):
        response = client.post(
            "/showSummary", data={"email": "john@simplylift.co"}
        )
        assert b"Spring Festival" in response.data

    def test_valid_email_shows_club_points(self, client):
        response = client.post(
            "/showSummary", data={"email": "john@simplylift.co"}
        )
        assert b"13" in response.data

    def test_unknown_email_redirects(self, client):
        response = client.post(
            "/showSummary", data={"email": "unknown@test.com"}
        )
        assert response.status_code == 302

    def test_unknown_email_redirects_to_index(self, client):
        response = client.post(
            "/showSummary",
            data={"email": "unknown@test.com"},
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_unknown_email_shows_flash_message(self, client):
        response = client.post(
            "/showSummary",
            data={"email": "unknown@test.com"},
            follow_redirects=True
        )
        assert "email" in response.data.decode("utf-8").lower()

    def test_another_valid_club(self, client):
        response = client.post(
            "/showSummary", data={"email": "admin@irontemple.com"}
        )
        assert response.status_code == 200
        assert b"Iron Temple" in response.data


# ===========================================================================
# 3. Route book — GET /book/<competition>/<club>
# ===========================================================================
class TestBook:
    def test_valid_booking_page_returns_200(self, client):
        response = client.get("/book/Spring Festival/Simply Lift")
        assert response.status_code == 200

    def test_valid_booking_page_shows_competition(self, client):
        response = client.get("/book/Spring Festival/Simply Lift")
        assert b"Spring Festival" in response.data

    def test_valid_booking_page_shows_club(self, client):
        response = client.get("/book/Spring Festival/Simply Lift")
        assert b"Simply Lift" in response.data

    def test_past_competition_redirects(self, client):
        response = client.get("/book/Past Competition/Simply Lift")
        assert response.status_code == 302

    def test_past_competition_shows_flash(self, client):
        response = client.get(
            "/book/Past Competition/Simply Lift", follow_redirects=True
        )
        data = response.data.decode("utf-8")
        assert "compétition" in data.lower() or "lieu" in data.lower()

    def test_invalid_competition_redirects(self, client):
        response = client.get("/book/InexistantComp/Simply Lift")
        assert response.status_code == 302

    def test_invalid_club_redirects(self, client):
        response = client.get("/book/Spring Festival/ClubInexistant")
        assert response.status_code == 302

    def test_invalid_competition_shows_error(self, client):
        response = client.get(
            "/book/InexistantComp/Simply Lift", follow_redirects=True
        )
        assert response.status_code == 200


# ===========================================================================
# 4. Route purchasePlaces — POST /purchasePlaces
# ===========================================================================
class TestPurchasePlaces:
    # --- Happy paths --------------------------------------------------------
    def test_valid_purchase_returns_200(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "2"
            },
        )
        assert response.status_code == 200

    def test_valid_purchase_shows_success_flash(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "2"
            },
        )
        content = response.data.decode("utf-8").lower()
        assert "succ" in content or b"Super" in response.data

    def test_valid_purchase_decreases_competition_places(self, client):
        client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "3"
            },
        )
        comp = next(
            c for c in server.competitions if c["name"] == "Spring Festival"
        )
        assert int(comp["numberOfPlaces"]) == 22

    def test_valid_purchase_decreases_club_points(self, client):
        client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "3"
            },
        )
        club = next(c for c in server.clubs if c["name"] == "Simply Lift")
        assert int(club["points"]) == 10

    def test_valid_purchase_records_booking(self, client):
        """La réservation cumulative doit être enregistrée."""
        client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "4"
            },
        )
        comp = next(
            c for c in server.competitions if c["name"] == "Spring Festival"
        )
        assert comp.get("bookings", {}).get("Simply Lift") == 4

    def test_purchase_exactly_12_places_succeeds(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "12"
            },
        )
        assert response.status_code == 200
        content = response.data.decode("utf-8").lower()
        assert b"Super" in response.data or "succ" in content

    # --- Sad paths : saisie invalide ----------------------------------------
    def test_purchase_zero_places_shows_error(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "0"
            },
        )
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "moins" in data.lower() or "place" in data.lower()

    def test_purchase_negative_places_shows_error(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "-1"
            },
        )
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "moins" in data.lower() or "place" in data.lower()

    def test_purchase_non_numeric_places_shows_error(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "abc"
            },
        )
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "valide" in data.lower() or "nombre" in data.lower()

    # --- Sad paths : règles métier ------------------------------------------
    def test_purchase_more_than_available_shows_error(self, client):
        """Fall Classic n'a que 4 places disponibles."""
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Fall Classic",
                "club": "Simply Lift",
                "places": "5"
            },
        )
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "places" in data.lower() or "disponibles" in data.lower()

    def test_purchase_more_than_12_per_transaction_shows_error(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "13"
            },
        )
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "12" in data

    def test_purchase_more_than_club_points_shows_error(self, client):
        """Iron Temple a seulement 4 points."""
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Iron Temple",
                "places": "5"
            },
        )
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "points" in data.lower()

    # --- Sad path : limite cumulative ---------------------------------------
    def test_purchase_cumulative_limit_blocked(self, client):
        """Bloqué si previous_booked + required > 12."""
        server.competitions[0]["bookings"] = {"Simply Lift": 10}

        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "5"
            },
        )
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "10" in data or "déjà réservé" in data or "2" in data

    def test_purchase_cumulative_limit_allows_remaining(self, client):
        """Permet de réserver le reste jusqu'à 12."""
        server.competitions[0]["bookings"] = {"Simply Lift": 10}

        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "2"
            },
        )
        assert response.status_code == 200
        content = response.data.decode("utf-8").lower()
        assert b"Super" in response.data or "succ" in content

    def test_purchase_cumulative_exactly_12_total_succeeds(self, client):
        server.competitions[0]["bookings"] = {"Simply Lift": 8}

        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "4"
            },
        )
        assert response.status_code == 200
        content = response.data.decode("utf-8").lower()
        assert b"Super" in response.data or "succ" in content

    # --- Sad paths : entités inconnues --------------------------------------
    def test_purchase_unknown_competition_redirects(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "CompInexistante",
                "club": "Simply Lift",
                "places": "2"
            },
        )
        assert response.status_code == 302

    def test_purchase_unknown_club_redirects(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "ClubInexistant",
                "places": "2"
            },
        )
        assert response.status_code == 302

    def test_purchase_when_competition_has_no_bookings_key(self, client):
        if "bookings" in server.competitions[0]:
            del server.competitions[0]["bookings"]
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Spring Festival",
                "club": "Simply Lift",
                "places": "1"
            },
        )
        assert response.status_code == 200
        assert server.competitions[0]["bookings"]["Simply Lift"] == 1

    def test_purchase_exact_available_places_succeeds(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Fall Classic",
                "club": "Simply Lift",
                "places": "4"
            },
        )
        assert response.status_code == 200
        content = response.data.decode("utf-8").lower()
        assert b"Super" in response.data or "succ" in content

    def test_purchase_exact_club_points_succeeds(self, client):
        response = client.post(
            "/purchasePlaces",
            data={
                "competition": "Fall Classic",
                "club": "Iron Temple",
                "places": "4"
            },
        )
        assert response.status_code == 200
        content = response.data.decode("utf-8").lower()
        assert b"Super" in response.data or "succ" in content


# ===========================================================================
# 5. Route pointsDisplay — GET /pointsDisplay
# ===========================================================================
class TestPointsDisplay:
    def test_points_display_returns_200(self, client):
        response = client.get("/pointsDisplay")
        assert response.status_code == 200

    def test_points_display_shows_all_clubs(self, client):
        response = client.get("/pointsDisplay")
        data = response.data.decode("utf-8")
        assert "Simply Lift" in data
        assert "Iron Temple" in data
        assert "She Lifts" in data

    def test_points_display_clubs_sorted_by_points_descending(self, client):
        response = client.get("/pointsDisplay")
        data = response.data.decode("utf-8")
        pos_simply = data.find("Simply Lift")
        pos_iron = data.find("Iron Temple")
        assert pos_simply < pos_iron

    def test_leaderboard_alias_returns_200(self, client):
        response = client.get("/leaderboard")
        assert response.status_code == 200

    def test_leaderboard_same_content_as_points_display(self, client):
        r1 = client.get("/pointsDisplay")
        r2 = client.get("/leaderboard")
        assert r1.data == r2.data

    def test_points_display_accessible_without_login(self, client):
        response = client.get("/pointsDisplay")
        assert response.status_code == 200


# ===========================================================================
# 6. Route logout — GET /logout
# ===========================================================================
class TestLogout:
    def test_logout_redirects(self, client):
        response = client.get("/logout")
        assert response.status_code == 302

    def test_logout_redirects_to_index(self, client):
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"email" in response.data or b"showSummary" in response.data
