from flask import Flask, render_template, request, session, jsonify
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)
app.secret_key = 'your_secret_key'
dotnet_api_url = 'http://localhost:5135' 

# Cargar datos desde archivos CSV
movies = pd.read_csv('movies.csv')
ratings = pd.read_csv('ratings.csv')
tags = pd.read_csv('tags.csv')

# Crear una tabla pivote para tener usuarios en filas y películas en columnas
user_movie_ratings = ratings.pivot_table(index='userId', columns='movieId', values='rating')
user_movie_ratings = user_movie_ratings.fillna(0)

# Calcular similitud coseno entre usuarios
user_similarity = cosine_similarity(user_movie_ratings)

# Inicializar el modelo k-NN
knn_model = NearestNeighbors(metric='cosine', algorithm='brute')
knn_model.fit(user_movie_ratings)

def get_movie_recommendations(user_id, num_neighbors=5):
    user_index = user_movie_ratings.index.get_loc(user_id)
    distances, indices = knn_model.kneighbors(user_movie_ratings.iloc[user_index, :].values.reshape(1, -1), n_neighbors=num_neighbors+1)
    neighbor_movies = user_movie_ratings.iloc[indices.flatten()[1:], :]
    avg_ratings = neighbor_movies.mean()
    user_ratings = user_movie_ratings.iloc[user_index, :]
    unrated_movies = user_ratings[user_ratings == 0].index
    recommendations = avg_ratings[unrated_movies].sort_values(ascending=False)
    session['recommendations'] = recommendations.index[:6].tolist()
    return session['recommendations']

@app.route('/neighbors_data', methods=['GET'])
def show_neighbors_data():
    neighbors_data = session.get('neighbors_data', [])
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify(neighbors_data)
    
    return render_template('neighbors_data.html', neighbors_data=neighb0ors_data)

@app.route('/', methods=['POST', 'GET'])
def show_recommendations():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id is not None and user_id.isdigit():
            user_id = int(user_id)
            recommendations = get_movie_recommendations(user_id)
            recommended_movies = movies[movies['movieId'].isin(recommendations)]

            if request.headers.get('Content-Type') == 'application/json':
                return jsonify(recommended_movies.to_dict(orient='records'))
            
            return render_template('index.html', user_id=user_id, recommended_movies=recommended_movies)
    
    return render_template('index.html', user_id=None, recommended_movies=pd.DataFrame())

@app.route('/temp_results', methods=['GET'])
def show_temp_results():
    recommendations = session.get('recommendations', [])
    recommended_movies = movies[movies['movieId'].isin(recommendations)]
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify(recommended_movies.to_dict(orient='records'))
    
    return render_template('temp_results.html', recommended_movies=recommended_movies)

# Nueva ruta para la API
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations_api():
    recommendations = session.get('recommendations', [])
    recommended_movies = movies[movies['movieId'].isin(recommendations)]
    return jsonify(recommended_movies.to_dict(orient='records'))

@app.route('/movies')
def show_movies():
    return render_template('movies.html', movies=movies)

@app.route('/ratings')
def show_ratings():
    return render_template('ratings.html', ratings=ratings)

@app.route('/tags')
def show_tags():
    return render_template('tags.html', tags=tags)

if __name__ == '__main__':
    app.run(debug=True)
