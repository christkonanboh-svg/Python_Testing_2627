"""
Locust — Tests de performance GUDLFT
=====================================
Simule deux types d'utilisateurs :
  - SecretaryUser  : secrétaire de club (login, réservation, dashboard)
  - PublicUser     : visiteur anonyme qui consulte le classement

Lancer (serveur Flask démarré sur http://localhost:5000) :
    locust -f locustfile.py --headless -u 10 -r 2 --run-time 60s \\
           --host http://localhost:5000 --html reports/locust_report.html

Avec l'interface Web :
    locust -f locustfile.py --host http://localhost:5000
    Ouvrir http://localhost:8089
"""
from locust import HttpUser, task, between, events
import random


SECRETARY_ACCOUNTS = [
    {"email": "john@simplylift.co",     "club": "Simply Lift"},
    {"email": "admin@irontemple.com",   "club": "Iron Temple"},
    {"email": "kate@shelifts.co.uk",    "club": "She Lifts"},
]

COMPETITION_NAMES = [
    "Spring Festival",
    "Fall Classic",
    "Winter Open Championship",
]


class SecretaryUser(HttpUser):
    """
    Simule un secrétaire de club qui :
      1. Navigue sur l'index
      2. Se connecte par email
      3. Consulte la page de réservation
      4. Réserve des places
      5. Consulte le classement
      6. Se déconnecte
    """
    weight = 3
    wait_time = between(1, 3)

    def on_start(self):
        account = random.choice(SECRETARY_ACCOUNTS)
        self.email = account["email"]
        self.club = account["club"]

    @task(5)
    def view_index(self):
        self.client.get("/", name="GET /")

    @task(4)
    def login(self):
        self.client.post(
            "/showSummary",
            data={"email": self.email},
            name="POST /showSummary",
        )

    @task(2)
    def view_booking_page(self):
        competition = random.choice(COMPETITION_NAMES)
        self.client.get(
            f"/book/{competition}/{self.club}",
            name="GET /book/<comp>/<club>",
        )

    @task(1)
    def purchase_places(self):
        competition = random.choice(COMPETITION_NAMES)
        places = random.randint(1, 3)
        self.client.post(
            "/purchasePlaces",
            data={
                "club": self.club,
                "competition": competition,
                "places": str(places),
            },
            name="POST /purchasePlaces",
        )

    @task(2)
    def view_leaderboard(self):
        self.client.get("/pointsDisplay", name="GET /pointsDisplay")

    @task(1)
    def logout(self):
        self.client.get("/logout", name="GET /logout")


class PublicUser(HttpUser):
    """
    Simule un visiteur anonyme qui consulte uniquement
    l'accueil et le classement.
    """
    weight = 1
    wait_time = between(2, 5)

    @task(2)
    def view_index(self):
        self.client.get("/", name="GET / (public)")

    @task(3)
    def view_leaderboard(self):
        self.client.get("/pointsDisplay", name="GET /pointsDisplay (public)")


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    stats = environment.runner.stats
    print("\n" + "=" * 60)
    print("GUDLFT — Résumé des performances Locust")
    print("=" * 60)
    for name, entry in stats.entries.items():
        print(
            f"[{entry.method}] {entry.name:40s} "
            f"| Requêtes: {entry.num_requests:5d} "
            f"| Échecs: {entry.num_failures:4d} "
            f"| Méd: {entry.median_response_time:5.0f}ms "
            f"| p95: {entry.get_response_time_percentile(0.95):5.0f}ms"
        )
    print("=" * 60)
