from flask import Blueprint, render_template, request, session, redirect, url_for
from . import db
from flask_login import login_required, current_user
from .models import Recommendation, WatchedMovie
from .functions import QuizFunctions, MovieCards, DBAdditions, GeneralFunctions

#set up a blueprint for the flask application
views = Blueprint('views', __name__) 

# create a route 
@views.route('/')
@views.route('/home')
@login_required
#Changed this ****
def home():
    user_id = current_user.id
    return render_template("home.html", user=current_user)

@views.route('/profile', methods=['GET', 'POST'])
@login_required	
def profile():
    user_id = current_user.id
    recommended_ids = [recommended.movie_id for recommended in Recommendation.query.filter_by(user_id=user_id).all()]
    watched_ids = [watched.movie_id for watched in WatchedMovie.query.filter_by(user_id=user_id).all()]
    if request.method == 'POST':
        watched_items = [int(request.form[key]) for key in request.form if key.startswith('w')]
        """for recommendation_id in selected_recommendations:
            recommendation = Recommendation.query.get(recommendation_id)
            if recommendation:
                watched_movie = WatchedMovie(user_id=user_id, movie_id=recommendation.movie_id)
                db.session.add(watched_movie)

        db.session.commit()"""
    displayed_recommendations = MovieCards.display_information(recommended_ids)
    displayed_watched = MovieCards.display_information(watched_ids)
    return render_template('profile.html', user = current_user, displayed_recommendations=displayed_recommendations, displayed_watched=displayed_watched )
	
	
@views.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    return render_template('quiz.html', user=current_user)

@views.route('/quizsimilar', methods=['GET', 'POST'])
@login_required
def quiz_similar():
    user_id = current_user.id

    if request.method == 'POST':
        thirtyr = session.get('thirtyr', [])
        tempr = session.get('tempr', [])
        watched_items = [int(request.form[key]) for key in request.form if key.startswith('w')]
        not_interested_items = [int(request.form[key]) for key in request.form if key.startswith('ni')]

        all_affected_items = watched_items + not_interested_items
        for movie_id in all_affected_items:
            if movie_id in watched_items:
                DBAdditions.add_watched(user_id, movie_id)
            elif movie_id in not_interested_items:
                DBAdditions.add_not_interested(user_id, movie_id)
                #remove from recommendations
            thirtyr.remove(movie_id)
            tempr.remove(movie_id)
        if not all_affected_items:
            DBAdditions.add_recommended(user_id, tempr)
        session['thirtyr'] = thirtyr 
        session['tempr'] = tempr
        #regenerate thirtyr and tempr when they are less than 10

    if 'runqs1' not in session:
        session['runqs1'] = True
        thirtyr = QuizFunctions.generate_similar_quiz_results(user_id)
        tempr = thirtyr[:10]
        session['thirtyr'] = thirtyr
        session['tempr'] = tempr

    displayed = MovieCards.display_information(session.get('tempr', []))
    return render_template('quizsimilar.html', user=current_user, displayed=displayed)
 
@views.route('/newquiz', methods=['GET', 'POST'])
@login_required
def quiz_new():
    user_id = current_user.id
    genre_list = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
                  'Fantasy', 'Film-Noir', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Short',
                  'Sport', 'Thriller', 'War', 'Western']

    if request.method == 'POST':
        if 'selected_genres' not in session:
            genre_select = [request.form[key] for key in request.form if key.startswith('s')]
            session['selected_genres'] = genre_select
            return redirect(url_for('views.quiz_new'))
        if 'selected_actors' not in session:
            actor_select = [request.form[key] for key in request.form if key.startswith('a')]
            session['selected_actors'] = actor_select
            return redirect(url_for('views.quiz_new'))

        if 'selected_directors' not in session:
            director_select = [request.form[key] for key in request.form if key.startswith('d')]
            session['selected_directors'] = director_select
            return redirect(url_for('views.quiz_new'))

        if 'selected_languages' not in session:
            language_select = [request.form[key] for key in request.form if key.startswith('l')]
            session['selected_languages'] = language_select
            return redirect(url_for('views.quiz_new'))

        if 'selected_movies' not in session:
            movies_selected = [int(request.form[key]) for key in request.form if key.startswith('w')]
            #movies_selected_havent_watched = [int(request.form[key]) for key in request.form if key.startswith('dw')]
            for movie in movies_selected:
                DBAdditions.add_watched(user_id, movie)
            session['selected_movies'] = movies_selected
            return redirect(url_for('views.quiz_new'))

        if 'writer_info' not in session:
            movies_liked = [int(request.form[key]) for key in request.form if key.startswith('li')]
            movies_didnt_like = [int(request.form[key]) for key in request.form if key.startswith('dl')]
            for movie in movies_didnt_like:
                DBAdditions.add_not_interested(user_id, movie)
            session['writer_info'] = movies_liked
            return redirect(url_for('views.quiz_new'))

    if 'selected_genres' not in session:
        return render_template('newquiz.html', user=current_user, stage='genre_selection', genre_list=genre_list)

    if 'selected_actors' not in session:
        selected_genres = session.get('selected_genres', [])
        actor_list = QuizFunctions.selection(selected_genres, 1) if selected_genres else {}
        return render_template('newquiz.html', user=current_user, stage='actor_display', actor_list=actor_list)

    if 'selected_directors' not in session:
        selected_genres = session.get('selected_genres', [])
        director_list = QuizFunctions.selection(selected_genres, 2) if selected_genres else {}
        return render_template('newquiz.html', user=current_user, stage='director_display', director_list=director_list)

    if 'selected_languages' not in session:
        language_list = ['American Sign Language', 'Arabic', 'Bangla', 'Cantonese', 'Chaozhou', 'Chinese', 'Czech', 'Dinka', 
                         'Dutch', 'English', 'Finnish', 'French', 'German', 'Greek', 'Hebrew', 'Hindi', 'Indonesian', 'Irish', 
                         'Italian', 'Japanese', 'Korean', 'Latin', 'Mandarin', 'North American Indian', 'Nepali','Persian', 
                         'Portuguese', 'Russian', 'Spanish', 'Turkish']
        return render_template('newquiz.html', user=current_user, stage='language_display', language_list=language_list)
    
    if 'selected_movies' not in session:
        movie_list = QuizFunctions.generate_combinations(session['selected_genres'], session['selected_actors'], session['selected_directors'], [])
        displayed = MovieCards.display_information(movie_list[:20])
        session['movies_displayed'] = movie_list
        return render_template('newquiz.html', user=current_user, stage='movie_display', displayed=displayed)

    if 'writer_info' not in session:
        show_watched = session.get('selected_movies')
        new_displayed = MovieCards.display_information(show_watched)
        return render_template('newquiz.html', user=current_user, stage='movie_display2', displayed=new_displayed)

    writer_ids = session.get('writer_info')
    writers = QuizFunctions.get_writers(writer_ids)
    movie_list = QuizFunctions.generate_combinations(session['selected_genres'],  session['selected_actors'], session['selected_directors'], writers)
    new_list = GeneralFunctions.remove_watched_ids(movie_list, user_id)
    new_list = new_list[:10]
    for t in new_list:
        new_recommendation = Recommendation(user_id=user_id, movie_id=t)
        db.session.add(new_recommendation)
    db.session.commit()
    #remove old recommendtions, always run reset after this too

    displayed = MovieCards.display_information(new_list)
    return render_template('newquiz.html', user=current_user, stage='movie_display3', displayed=displayed)



@views.route('/reset_quiz')
@login_required
def reset_quiz():
    session.pop('selected_genres', None)
    session.pop('selected_actors', None)
    session.pop('selected_directors', None)
    session.pop('selected_languages', None)
    session.pop('selected_movies', None)
    session.pop('writer_info', None)
    return redirect(url_for('views.quiz_new'))


