import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


def loadClubs():
    with open('clubs.json', encoding='utf-8') as c:
        listOfClubs = json.load(c)['clubs']
        return listOfClubs


def loadCompetitions():
    with open('competitions.json', encoding='utf-8') as comps:
        listOfCompetitions = json.load(comps)['competitions']
        return listOfCompetitions


def saveClubs(clubs_data):
    with open('clubs.json', 'w', encoding='utf-8') as c:
        json.dump({'clubs': clubs_data}, c, indent=4, ensure_ascii=False)


def saveCompetitions(competitions_data):
    with open('competitions.json', 'w', encoding='utf-8') as comps:
        json.dump(
            {'competitions': competitions_data}, comps, indent=4,
            ensure_ascii=False
        )


_real_saveClubs = saveClubs
_real_saveCompetitions = saveCompetitions

app = Flask(__name__)
app.secret_key = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-change-in-production'
)

competitions = loadCompetitions()
clubs = loadClubs()


@app.route('/')
def index():
    return render_template('index.html', clubs=clubs)


@app.route('/showSummary', methods=['POST'])
def showSummary():
    matched_clubs = [
        c for c in clubs if c['email'] == request.form['email']
    ]
    if not matched_clubs:
        flash("Désolé, cette adresse email n'a pas été trouvée.")
        return redirect(url_for('index'))
    club = matched_clubs[0]
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template(
        'welcome.html', club=club, competitions=competitions,
        clubs=clubs, now=now_str
    )


@app.route('/book/<competition>/<club>')
def book(competition, club):
    matched_clubs = [c for c in clubs if c['name'] == club]
    matched_competitions = [
        c for c in competitions if c['name'] == competition
    ]
    if not matched_clubs or not matched_competitions:
        flash("Une erreur est survenue, veuillez réessayer.")
        return redirect(url_for('index'))
    foundClub = matched_clubs[0]
    foundCompetition = matched_competitions[0]
    competition_date = datetime.strptime(
        foundCompetition['date'], '%Y-%m-%d %H:%M:%S'
    )
    if competition_date < datetime.now():
        flash(
            "Cette compétition a déjà eu lieu et ne peut plus être réservée."
        )
        return redirect(url_for('index'))
    return render_template(
        'booking.html', club=foundClub, competition=foundCompetition
    )


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    matched_competitions = [
        c for c in competitions if c['name'] == request.form['competition']
    ]
    matched_clubs = [
        c for c in clubs if c['name'] == request.form['club']
    ]
    if not matched_competitions or not matched_clubs:
        flash("Une erreur est survenue, veuillez réessayer.")
        return redirect(url_for('index'))
    competition = matched_competitions[0]
    club = matched_clubs[0]
    try:
        placesRequired = int(request.form['places'])
    except ValueError:
        flash("Veuillez saisir un nombre valide de places.")
        return render_template(
            'booking.html', club=club, competition=competition
        )
    if placesRequired <= 0:
        flash("Veuillez réserver au moins une place.")
        return render_template(
            'booking.html', club=club, competition=competition
        )
    if placesRequired > int(competition['numberOfPlaces']):
        flash("Pas assez de places disponibles pour cette compétition.")
        return render_template(
            'booking.html', club=club, competition=competition
        )
    if placesRequired > 12:
        flash("Vous ne pouvez pas réserver plus de 12 places par compétition.")
        return render_template(
            'booking.html', club=club, competition=competition
        )

    # Limite cumulative (max 12 places par club par compétition)
    bookings = competition.get('bookings', {})
    already_booked = int(bookings.get(club['name'], 0))
    if already_booked + placesRequired > 12:
        remaining = 12 - already_booked
        flash(
            f"Vous avez déjà réservé {already_booked} place(s) pour cette "
            f"compétition. Il vous reste {remaining} place(s) réservable(s) "
            f"(maximum 12 au total)."
        )
        return render_template(
            'booking.html', club=club, competition=competition
        )

    if placesRequired > int(club['points']):
        flash(
            "Vous n'avez pas assez de points pour réserver autant de places."
        )
        return render_template(
            'booking.html', club=club, competition=competition
        )

    competition['numberOfPlaces'] = (
        int(competition['numberOfPlaces']) - placesRequired
    )
    club['points'] = int(club['points']) - placesRequired

    # Mise à jour du suivi des réservations cumulatives
    if 'bookings' not in competition:
        competition['bookings'] = {}
    competition['bookings'][club['name']] = already_booked + placesRequired

    saveCompetitions(competitions)
    saveClubs(clubs)

    flash('Super ! Réservation effectuée avec succès.')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template(
        'welcome.html', club=club, competitions=competitions,
        clubs=clubs, now=now_str
    )


@app.route('/pointsDisplay')
@app.route('/leaderboard')
def pointsDisplay():
    sorted_clubs = sorted(
        clubs, key=lambda c: int(c['points']), reverse=True
    )
    return render_template('points.html', clubs=sorted_clubs)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
