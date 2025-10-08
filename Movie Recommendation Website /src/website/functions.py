from .models import Actor, Genre, Director, Movies, Writer, Language, Recommendation, WatchedMovie, NotInterested
from imdb import Cinemagoer
from . import db
import requests
from bs4 import BeautifulSoup
import itertools
import random


class QuizFunctions():
    def search_movies(genres=None, actors=None, directors=None, writers=None):
        query = Movies.query
        if genres:
            query = query.join(Genre).filter(Genre.genre.in_(genres))
        if actors:
            query = query.join(Actor).filter(Actor.actor.in_(actors))
        if directors:
            query = query.join(Director).filter(Director.director.in_(directors))
        if writers:
            query = query.join(Writer).filter(Writer.writer.in_(writers))
        query = query.distinct()
    
        return [movie.movie_id for movie in query.all()]

    def generate_similar_quiz_results(user_id):
        watched_ids = [watched.movie_id for watched in WatchedMovie.query.filter_by(user_id=user_id).all()]
        g = 0.25
        a = 0.35
        d = 0.1
        threshold_g = max(1, int(len(watched_ids) * g))
        threshold_a = max(1, int(len(watched_ids) * a))
        threshold_d = max(1, int(len(watched_ids) * d))
        genre_count = {}
        actor_count = {}
        director_count = {}
        
        for movie_id in watched_ids:
            genres = Genre.query.filter_by(movie_id=movie_id).all()
            actors = Actor.query.filter_by(movie_id=movie_id).all()
            directors = Director.query.filter_by(movie_id=movie_id).all()
    
            for genre in genres:
                if genre.genre in genre_count:
                    genre_count[genre.genre] += 1
                else:
                    genre_count[genre.genre] = 1
                    
            for actor in actors:
                if actor.actor in actor_count:
                    actor_count[actor.actor] += 1
                else:
                    actor_count[actor.actor] = 1
                    
            for director in directors:
                if director.director in director_count:
                    director_count[director.director] += 1
                else:
                    director_count[director.director] = 1
                    
        filtered_genre_count = {k: v for k, v in genre_count.items() if v >= threshold_g}
        filtered_actor_count = {k: v for k, v in actor_count.items() if v >= threshold_a}
        filtered_director_count = {k: v for k, v in director_count.items() if v >= threshold_d}
        
        sorted_genre_count = dict(sorted(filtered_genre_count.items(), key=lambda item: item[1], reverse=True))
        sorted_actor_count = dict(sorted(filtered_actor_count.items(), key=lambda item: item[1], reverse=True))
        sorted_director_count = dict(sorted(filtered_director_count.items(), key=lambda item: item[1], reverse=True))

        preferred_genres = list(sorted_genre_count.keys())
        preferred_actors = list(sorted_actor_count.keys())
        preferred_directors = list(sorted_director_count.keys())
        
        results = QuizFunctions.generate_combinations(preferred_genres, preferred_actors, preferred_directors, [])
        result = GeneralFunctions.remove_watched_ids(results, user_id)
        return result

    def generate_combinations(genres, actors, directors, writers):
        result = set()
        if  genres and actors and directors and writers:
            for genre, actor, director, writers in itertools.product(genres, actors, directors, writers):
                result.update(QuizFunctions.search_movies(genres=[genre], actors=[actor], directors=[director], writers=[writers]))
            for actor, director, writers in itertools.product(actors, directors, writers):
                result.update(QuizFunctions.search_movies(actors=[actor], directors=[director], writers=[writers]))
            for actor, genre, writers in itertools.product(actors, genres, writers):
                result.update(QuizFunctions.search_movies(actors=[actor], genres=[genre], writers=[writers]))
            for genre, director, writers in itertools.product(genres, directors, writers):
                result.update(QuizFunctions.search_movies(genres=[genre], directors=[director], writers=[writers]))

        if genres and actors and directors:
            for genre, actor, director in itertools.product(genres, actors, directors):
                result.update(QuizFunctions.search_movies(genres=[genre], actors=[actor], directors=[director]))
            for actor, director in itertools.product(actors, directors):
                result.update(QuizFunctions.search_movies(actors=[actor], directors=[director]))
            for actor, genre in itertools.product(actors, genres):
                result.update(QuizFunctions.search_movies(actors=[actor], genres=[genre]))
            for genre, director in itertools.product(genres, directors):
                result.update(QuizFunctions.search_movies(genres=[genre], directors=[director]))
    
        return list(result)

    def selection(selected_list, a):
        by_genre = {}
        if a == 1:
            for genre in selected_list:
                query = db.session.query(Actor.actor).join(Movies).join(Genre).filter(Genre.genre == genre)
                actors = query.distinct().all()
                actor_names = [actor[0] for actor in actors]
                if len(actor_names) > 20:
                    by_genre[genre] = random.sample(actor_names, 20)
                else:
                    by_genre[genre] = actor_names
        if a == 2:
            for genre in selected_list:
                query = db.session.query(Director.director).join(Movies).join(Genre).filter(Genre.genre == genre)
                directors = query.distinct().all()
                director_names = [director[0] for director in directors]
                if len(director_names) > 20:
                    by_genre[genre] = random.sample(director_names, 20)
                else:
                    by_genre[genre] = director_names

        return by_genre

    def get_writers(writer_ids):
        writers = Writer.query.filter(Writer.movie_id.in_(writer_ids)).distinct().all()
        writer_names = [writer.writer for writer in writers]
        return writer_names           

    def process_items(user_id, items, action, tempr, thirty_recommendations):
        for movie_id in items:
            if movie_id is not None:
                if action == 'watched':
                    #DBAdditions.add_watched(user_id, movie_id)
                    pass
                elif action == 'not_interested':
                    pass
                    #DBAdditions.add_not_interested(user_id, movie_id)
            
                try:
                    tempr.remove(movie_id)
                    thirty_recommendations.remove(movie_id)
                except ValueError:
                    pass

        #db.session.commit()


class GeneralFunctions():
    def remove_watched_ids(movie_id_list, user_id):
        watched_ids = [watched.movie_id for watched in WatchedMovie.query.filter_by(user_id=user_id).all()]
        not_interested_ids = [not_interested.movie_id for not_interested in NotInterested.query.filter_by(user_id=user_id).all()]
        new_list = [movie_id for movie_id in movie_id_list if movie_id not in watched_ids and movie_id not in not_interested_ids]
        return new_list


class DBAdditions():
    def extract_movie_titles(url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            h2_tags = soup.find_all('h2')
            movie_titles = []
            for tag in h2_tags:
                a_tags = tag.find_all('a')
                if a_tags:
                    for a_tag in a_tags:
                        movie_title = a_tag.get_text().strip()
                        if movie_title:
                            movie_titles.append(movie_title)
            return movie_titles    
        except Exception as e:
            print(e)
            return

    def add_movies(titles, year):
        ia = Cinemagoer()
        for title in titles:
            try:
                if Movies.query.filter_by(title=title, year=year).first():
                    print(title, " already exists")
                    continue

                else:
                    movie_result = ia.search_movie(title)
                    if not movie_result:
                        print(title, " doesn't exist")
                        continue
                    movie = movie_result[0]
                    ia.update(movie)
                    if movie['kind'] != 'movie':
                        print(title, " isn't a movie")
                        continue
                    tid = movie.movieID
                    if tid and movie.get('full-size cover url') is not None:
                        new_movie = Movies(movie_id = tid, title=title, url=movie['full-size cover url'], year=year)
                        db.session.add(new_movie)
                    elif tid and movie.get('full-size cover url') is None:
                        new_movie = Movies(movie_id = tid, title=title, url=None, year=year)
                        db.session.add(new_movie)

                    if 'genres' in movie: 
                        for genre in movie['genres']:
                            if(genre):
                                new_genre = Genre(movie_id = tid, genre=genre)
                                db.session.add(new_genre)
                    else:
                        print(title, " doesnt have genres")

                    if 'languages' in movie: 
                        for language in movie['languages']:
                            if(language):
                                new_language = Language(movie_id = tid, language=language)
                                db.session.add(new_language)
                    else:
                        print(title, " doesnt have languages")

                    if 'director' in movie:
                        for director in movie['director'][:2]:
                            if director:
                                new_director = Director(movie_id=tid, director=director['name'])
                                db.session.add(new_director)  
                    else:
                        print(title, " doesn't have directors")

                    if 'writer' in movie: 
                        for writer in movie['writers'][:2]:
                            if(writer):
                                new_writer = Writer(movie_id = tid, writer=writer['name'])
                                db.session.add(new_writer)
                    else:
                        print(title, " doesnt have writers")

                    if 'cast' in movie:
                        for actor in movie['cast'][:8]:
                            if actor:
                                new_actor = Actor(movie_id=tid, actor=actor['name'])
                                db.session.add(new_actor)
                    else:
                        print(title, " doesnt have cast")
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

    def add_watched(user_id, movie_id):
        movie_exists = Movies.query.filter_by(movie_id=movie_id).first()
        watched = WatchedMovie.query.filter_by(movie_id=movie_id, user_id=user_id).first()
        if not movie_exists:
            print(user_id, " tried to add movie ", movie_id, " that doesnt exist in movie table")
        if not watched:
            try:
                new_watched_movie = WatchedMovie(user_id = user_id, movie_id=movie_id)
                db.session.add(new_watched_movie)
                db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 print(e)

    def add_not_interested(user_id, movie_id):
        movie_exists = Movies.query.filter_by(movie_id=movie_id).first()
        in_not_interested = WatchedMovie.query.filter_by(movie_id=movie_id, user_id=user_id).first()
        if not movie_exists:
            print(user_id, " tried to add movie ", movie_id, " that doesnt exist in movie table")
        if not in_not_interested:
            try:
                new_not_interested = NotInterested(user_id = user_id, movie_id=movie_id)
                db.session.add(new_not_interested)
                db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 print(e)

    def add_recommended(user_id, movie_id_list):
        for movie_id in movie_id_list:
            movie_exists = Movies.query.filter_by(movie_id=movie_id).first()
            in_recommended = Recommendation.query.filter_by(movie_id=movie_id, user_id=user_id).first()
            if not movie_exists:
                print(user_id, " tried to add movie ", movie_id, " that doesnt exist in movie table")
            if not in_recommended:
                try:
                    new_recommendation = Recommendation(user_id = user_id, movie_id=movie_id)
                    db.session.add(new_recommendation)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(e)


class MovieCards():
    def display_information(movie_id_list):
        returned_info = {}
        for tid in movie_id_list:
            temp = Movies.query.filter_by(movie_id=tid).first()
            movie_info = {
                "movie_id": temp.movie_id,
                "title": temp.title,
                "url": temp.url,
                "year": temp.year
            }
            returned_info[tid] = movie_info
        return returned_info
"""       
    def display_friend_watch(user_id, time):
        t = []
        fl = GeneralFunctions.get_friend_list(user_id)
        for friend in friend_list:
            query watched movies
            if (movie.timestamp > time)
            

        sortedt = sort(t.bytimestamp)
        return sortedt

    def reveiws(user_id, number):
        pass
    #grabs friendlist reviews
    def update(6 params, x, time):
        reviews(movie_id, x+10)
        10, 11-20, 
         display_friend_watch(time)"""
