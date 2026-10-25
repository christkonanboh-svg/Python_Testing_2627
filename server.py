import json
# pyrefly: ignore[missing-import]
from flask import Flask,render_template,request,redirect,flash,url_for


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    matched_clubs = [club for club in clubs if club['email'] == request.form['email']]
    if not matched_clubs:
        flash("Sorry, that email wasn't found.")
        return redirect(url_for('index'))
    club = matched_clubs[0]
    return render_template('welcome.html',club=club,competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition,club):
    matched_clubs = [c for c in clubs if c['name'] == club]
    matched_competitions = [c for c in competitions if c['name'] == competition]
    if not matched_clubs or not matched_competitions:
        flash("Something went wrong-please try again")
        return redirect(url_for('index'))
    foundClub = matched_clubs[0]
    foundCompetition = matched_competitions[0]
    return render_template('booking.html',club=foundClub,competition=foundCompetition)


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    matched_competitions = [c for c in competitions if c['name'] == request.form['competition']]
    matched_clubs = [c for c in clubs if c['name'] == request.form['club']]
    if not matched_competitions or not matched_clubs:
        flash("Something went wrong-please try again")
        return redirect(url_for('index'))
    competition = matched_competitions[0]
    club = matched_clubs[0]
    try:
        placesRequired = int(request.form['places'])
    except ValueError:
        flash("Please enter a valid number of places.")
        return render_template('booking.html', club=club, competition=competition)
    if placesRequired > int(competition['numberOfPlaces']):
        flash("Not enough places available in this competition.")
        return render_template('booking.html', club=club, competition=competition)
    if placesRequired > 12:
        flash("You cannot book more than 12 places per competition.")
        return render_template('booking.html', club=club, competition=competition)
    competition['numberOfPlaces'] = int(competition['numberOfPlaces'])-placesRequired
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))itions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))