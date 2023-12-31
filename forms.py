from wtforms import StringField, SubmitField, PasswordField,TextAreaField, Form, StringField, validators
from wtforms.validators import DataRequired,URL
from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm


#forms
class ContactForm(FlaskForm):
    email=StringField("Email", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit =SubmitField("Send")

class LoginForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("login")


class ProjectForm(FlaskForm):
    title = StringField("Project", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    description= CKEditorField("Description", validators=[DataRequired()])
    img_url = StringField("Link")
    submit = SubmitField("Submit")




