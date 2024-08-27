import flask
import os
from flask import Flask, request, redirect, url_for, render_template, session
from databaser import Databaser
from databaser import Databaser_user

devepment_commans = ["subscriptions", "studio", "delete"]
app = Flask(__name__)
db = Databaser()
db_user = Databaser_user()

UPLOAD_FOLDER_VIDEOS = 'static/videos'
UPLOAD_FOLDER_IMAGES = 'static/images'
UPLOAD_FOLDER_AVATAR = 'static/user_avatars'
app.config['UPLOAD_FOLDER_VIDEOS'] = UPLOAD_FOLDER_VIDEOS
app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
app.config['UPLOAD_FOLDER_AVATAR'] = UPLOAD_FOLDER_AVATAR

# Убедитесь, что папки существуют
if not os.path.exists(UPLOAD_FOLDER_VIDEOS):
    os.makedirs(UPLOAD_FOLDER_VIDEOS)
if not os.path.exists(UPLOAD_FOLDER_IMAGES):
    os.makedirs(UPLOAD_FOLDER_IMAGES)
if not os.path.exists(UPLOAD_FOLDER_AVATAR):
    os.makedirs(UPLOAD_FOLDER_AVATAR)

app.secret_key = 'your_secret_key'  # Задайте секретный ключ для шифрования сессий


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Используем метод verify для проверки логина
        if db_user.verify(password, username):
            session['user'] = username  # Добавляем пользователя в сессию
            return redirect(url_for('root'))  # Перенаправляем на главную страницу
        else:
            return "не успешно"

    return render_template('login.html')


@app.route('/help')
def help():
    return render_template("help.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        avatar = request.files.get('image_file')

        if username and password:
            # Сохраняем пользователя в базу данных
            db_user.add_user(username, password)

            if avatar and avatar.filename.lower().endswith('.png'):
                avatar_filename = f"{username}.png"
                avatar_filepath = os.path.join(app.config['UPLOAD_FOLDER_AVATAR'], avatar_filename)
                avatar.save(avatar_filepath)

            return redirect(url_for('login'))
        else:
            return render_template('register.html', title="Создание аккаунта")
    return render_template('register.html', title="Создание аккаунта")


@app.route('/logout')
def logout():
    session.pop('user', None)  # Удаляем пользователя из сессии
    session.pop('avatar', None)  # Удаляем аватар из сессии
    return redirect(url_for('login'))


@app.route('/account')
def account():
    if 'user' in session:
        videos_get = db.get_videos(session.get('user'))
        return render_template('index.html', videos=videos_get)
    else:
        return redirect(url_for('login'))


@app.route('/')
def root():
    videos = db.get_videos(None)
    user_logged_in = "Аккаунт" if 'user' in session else "Регистрация"  # Проверяем, авторизован ли пользователь
    return render_template('index.html', argument=user_logged_in, videos=videos, name=session.get('user'),
                           avatar=session.get('avatar'))


@app.route('/add_video', methods=['GET', 'POST'])
def add_video():
    if 'user' in session:
        username = session['user']
        if request.method == 'POST':
            try:
                # Получаем данные из формы
                name = request.form['name']
                text = request.form['text']
                video_file = request.files['video_file']
                image_file = request.files['image_file']
                video_filename = video_file.filename
                image_filename = image_file.filename

                # Сохраняем видеофайл в папку videos
                if video_file and len(video_filename) <= 40:
                    video_filepath = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], video_filename)
                    video_file.save(video_filepath)
                else:
                    return f"ошибка в загрузке: длина имени видео {len(video_filename)} больше 40"

                # Сохраняем изображение в папку static/images
                if image_file and len(image_filename) <= 40:
                    image_filepath = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_filename)
                    image_file.save(image_filepath)
                    db.add_video(name, text, session.get('user'), video_filename, image_filename)
                    return render_template("uplodet_succefyl.html")
                else:
                    return f"ошибка в загрузке: длина имени фото {len(image_filename)} больше 40"
            except Exception as e:
                return f"ошибка в загрузке: {e}"
        return render_template('add_video.html')
    else:
        return redirect(url_for('login'))


@app.route('/<video_id>')
def video_page(video_id):
    video = db.get_video(video_id)
    if video_id not in devepment_commans:
        if video is None:
            return 'Видео не найдено'
    else:
        return "команда в разработке"

    return render_template('video_page.html', video=video)


@app.route('/static/videos/<filename>')
def serve_video(filename):
    return flask.send_from_directory('static/videos', filename)


@app.route('/static/images/<filename>')
def serve_image(filename):
    return flask.send_from_directory('static/images', filename)


@app.route('/static/user_avatars/<filename>')
def serve_avatar(filename):
    return flask.send_from_directory('static/user_avatars', filename)


if __name__ == '__main__':
    app.run(debug=True)
