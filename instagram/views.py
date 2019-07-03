import flask
from flask import url_for, redirect, request, flash
import os
from PIL import Image
from flask.views import MethodView
import secrets
from instagram.forms import Form1

from flask_login import (
    login_user,
    current_user,
    login_required,
    logout_user,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from instagram.db import db

from instagram import models


def create_user(user_name, email, password):
    user = models.User(
        username=user_name,
        email=email,
        password=password
    )

    db.session.add(user)
    db.session.commit()


class UserRegistrationView(MethodView):
    def get(self):
        return flask.render_template('registration.html')

    def post(self):
        if current_user.is_authenticated:
            return redirect(url_for('feed'))
        user_name = flask.request.form['user_name']
        email = flask.request.form['email']
        password = flask.request.form['password']

        hashed_password = generate_password_hash(password)

        create_user(
            user_name=user_name,
            email=email,
            password=hashed_password,
        )

        return flask.redirect(url_for('login'))

class UserLoginView(MethodView):
    def get(self):
        return flask.render_template('login.html')

    def post(self):
        email = flask.request.form['email']
        password = flask.request.form['password']

        user = models.User.query.filter_by(email=email).first()

        logged_in = False

        if user:
            is_correct = check_password_hash(
                pwhash=user.password,
                password=password,
            )

            if is_correct:
                login_user(user)

                logged_in = True

        if logged_in:
            return flask.redirect(url_for('feed'))

        return 'Failed to log in'


class ProfilePhotos(MethodView):
    decorators = [
        login_required,
    ]

    def get(self, user_id):
        user_name = current_user.username
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        user = models.User.query.get(user_id)

        if user is None:
            return 'Profile not found', 404

        return flask.render_template('profile_photos.html', photos=user.photos, user_name=user_name, image_file=image_file, user_id=current_user.id, user=user)

    def post(self, user_id):
        if request.method == "POST":
            picture_file = flask.request.files['profilepicture']
            profile_photo = save_picture(picture_file)
            current_user.image_file = profile_photo
            db.session.commit()
            return flask.redirect(url_for('profile-photos', user_id=current_user.id))
        return flask.render_template('profile_photos.html', user_id=current_user.id)

class SearchedProfile(MethodView):

    def get(self, user_id):
        user = models.User.query.get(user_id)

        user_name = user.username
        image_file = url_for('static', filename='profile_pics/' + user.image_file)


        if user is None:
            return 'Profile not found', 404

        return flask.render_template('profile_photos.html', photos=user.photos, user_name=user_name, image_file=image_file, user_id=current_user.id, user=user)

    def post(self, user_id):
        user = models.User.query.get(user_id)

        user_name = user.username
        image_file = url_for('static', filename='profile_pics/' + user.image_file)

        return flask.render_template('profile_photos.html', user=user, user_name=user_name,
                                         image_file=image_file)


class FollowWiew(MethodView):
    def get(self, username):

        user = models.User.query.filter_by(username=username).first()

        if user == current_user:
            return 'You cannot follow yourself!'

        current_user.follow(user)
        db.session.commit()

        return 'You are following {}.'.format(username)

    def post(self, username):
        pass


class UnfollowWiew(MethodView):
    def get(self, username):
        user = models.User.query.filter_by(username=username).first()

        if user == current_user:
            return 'You cannot unfollow yourself!'

        current_user.unfollow(user)
        db.session.commit()
        return 'You are not following {}.'.format(username)

    def post(self, username):
        pass



class DetailPhoto(MethodView):
    def get(self, photo_id):


        photo = models.Photo.query.get(photo_id)

        return flask.render_template(
            template_name_or_list='photo.html',
            photo=photo,
        )


class UploadPhoto(MethodView):
    decorators = [
        login_required,
    ]

    def get(self):

        return flask.render_template('upload_photo.html')

    def post(self):

        file = flask.request.files['photo']

        file_name = flask.current_app.config['UPLOADS_DIRECTORY'] / file.filename

        file.save(str(file_name))

        photo = models.Photo(
            path=file.filename,
            user_id=current_user.id,
        )

        db.session.add(photo)
        db.session.commit()

        return redirect(url_for('profile-photos', user_id=current_user.id))


class ViewFile(MethodView):
    def get(self, file_name):
        uploads_directory = str(flask.current_app.config['UPLOADS_DIRECTORY'])

        return flask.send_from_directory(uploads_directory, file_name)


class AddLike(MethodView):
    def post(self, photo_id):
        already_liked = models.Like.query.filter(
            models.Like.user_id == current_user.id,
            models.Like.photo_id == photo_id,
        ).count()

        if already_liked:
            return 'Sorry, we can not accept your like more than 1'

        like = models.Like(
            user_id=current_user.id,
            photo_id=photo_id,
        )

        db.session.add(like)
        db.session.commit()

        photo = models.Photo.query.get(photo_id)

        redirect_url = flask.url_for(
            endpoint='photo-detail',
            photo_id=photo.id,
        )

        return flask.redirect(redirect_url)


class AddComment(MethodView):
    def post(self, photo_id):
        comment = models.Comment(
            user_id=current_user.id,
            photo_id=photo_id,
            content=flask.request.form['content'],
        )

        db.session.add(comment)
        db.session.commit()

        redirect_url = flask.url_for(
            endpoint='photo-detail',
            photo_id=photo_id,
        )

        return flask.redirect(redirect_url)

class WelcomePage(MethodView):
    def get(self):
        return flask.render_template('welcome_page.html')

    def post(self):
        return flask.render_template('welcome_page.html')


class Feed(MethodView):
    decorators = [
        login_required,
    ]

    def get(self):
        posts = current_user.followed_posts().all()
        user_id = current_user.id
        form = Form1(request.form)
        return flask.render_template('feed.html', user_id=user_id, form=form, posts=posts)

    def post(self):
        user_id = current_user.id

        form = Form1(request.form)

        posts = current_user.followed_posts().all()

        if request.method == "POST" and form.validate_on_submit():
            searched_username = form.name.data
            user = models.User.query.filter_by(username=searched_username).first()

            if user:
                user_id = str(user.id)

                return flask.redirect(url_for('searched-users', user_id=user_id))


        return flask.render_template('feed.html', user_id=user_id, form=form, posts=posts)

class SearchedUsers(MethodView):
    def get(self, user_id):
        user = models.User.query.filter_by(id=user_id).first()

        if user:
            return redirect(url_for('searched-profile', user_id=user_id))

        return flask.render_template('searched_users.html')

    def post(self, user_id):
        return flask.render_template('searched_users.html')

class Logout(MethodView):
    def get(self):
        logout_user()
        return redirect(url_for('welcome-page'))

    def post(self):
        logout_user()
        return redirect(url_for('welcome-page'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join('C:/Users/PC/Desktop/instagram-git/instagram/static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

class ProfileSettings(MethodView):
    decorators = [
        login_required,
    ]

    def get(self, user_id):
        user_name = current_user.username
        user_id = current_user.id
        return flask.render_template('profile_settings.html', user_id=user_id, user_name=user_name)

    def post(self, user_id):
        user_id = current_user.id
        return flask.render_template('profile_settings.html', user_id=user_id)

class EditUsername(MethodView):
    decorators = [
        login_required,
    ]

    def get(self, user_id):
        user_id = current_user.id
        user_name = current_user.username
        return flask.render_template('edit_username.html', user_id=user_id, user_name=user_name)

    def post(self, user_id):
        user_id = current_user.id
        if request.method == "POST":
            new_username = flask.request.form['new_username']

            user = models.User.query.filter_by(username=new_username).first()

            if user:
                flash("Username is taken", category="error")
            else:
                if len(new_username) > 0:
                    current_user.username = new_username
                    db.session.commit()
                    return flask.redirect(url_for('profile-settings', user_id=current_user.id))

        return flask.render_template('edit_username.html', user_id=user_id)

class ChangePassword(MethodView):
    decorators = [
        login_required,
    ]

    def get(self, user_id):
        user_name = current_user.username
        user_id = current_user.id
        return flask.render_template('change_password.html', user_id=user_id, user_name=user_name)

    def post(self, user_id):
        if request.method == "POST":
            current_password = flask.request.form["currentpassword"]
            new_password = flask.request.form["newpassword"]

            user = models.User.query.filter_by(username=current_user.username).first()

            if user:
                is_correct = check_password_hash(
                    pwhash=user.password,
                    password=current_password,
                )

                if is_correct:
                    hashed_password = generate_password_hash(new_password)
                    current_user.password = hashed_password
                    db.session.commit()
                    return flask.redirect(url_for('profile-settings', user_id=user_id))
                else:
                    return 'wrong password'