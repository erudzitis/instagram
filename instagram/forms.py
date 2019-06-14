from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

class Form1(FlaskForm):
    name = StringField('')
    search = SubmitField('search')

class FollowButtonForm(FlaskForm):
    follow_button = SubmitField('Follow')