from time import sleep
from flask import jsonify,request, Flask, render_template, abort, redirect, url_for, flash,send_from_directory
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap
import os
from flask_sqlalchemy import SQLAlchemy
from forms import ContactForm, LoginForm,ProjectForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from flask_googletrans import translator
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect




app = Flask(__name__)
app.config['SECRET_KEY'] = "asdasdasd"
CKEditor(app)
Bootstrap(app)
translator(app)
csrf = CSRFProtect(app)
cors = CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
invasor =False
login_attempts = {}


##CONNECT TO DB AND MANAGER LOGIN
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
#app.config['SESSION_COOKIE_SECURE'] = True 


@login_manager.user_loader
def load_user(user_id):
    return Adm.query.get(int(user_id))


# CONFIGURE TABLEs
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    message = db.Column(db.Text, nullable=False)
    dat = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Project(db.Model):
    __tablename__ = "Project"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle=db.Column(db.String(100),nullable=False)
    description= db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Adm(UserMixin,db.Model):
    __tablename__ = "ADM"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), unique=True, nullable=False)
    password = db.Column(db.String(250),nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


#create tables
#db.create_all()


#add a adm 
#example 

#hash_and_salted_password = generate_password_hash(
#    "12345hello",
#    method='pbkdf2:sha256',
#    salt_length=8
#)
#user = Adm(
#    name="adm1",
#    password=hash_and_salted_password,
#)

#db.session.add(user)
#db.session.commit()


#write clients data in file  
def write_file():
    users = db.session.query(User).all()
    users =[user.to_dict() for user in users]
    with open('static/files/clients.txt','w') as f:
        for line in users:
            f.write('email : '+ line['email'])
            f.write('\n')
            f.write('message :'+line['message'])
            f.write('\n')
            f.write('date : '+ line['dat'])
            f.write('\n\n')


#tradutor languages
def What_accept_languages():
    languages=str(request.accept_languages)
    x =languages.split(",")
    print(x)
    if x[0] =="pt-PT" or x[0] =="pt-BR":
        return True
    else:
        return False


#contact email
@app.route('/', methods=["GET", "POST"])
def index():
    posts = Project.query.all()
    formCont = ContactForm()
    portguese = What_accept_languages()

    if formCont.validate_on_submit():
        if User.query.filter_by(email=formCont.email.data).first():
            var=User.query.filter_by(email=formCont.email.data).first()
            var.message = formCont.message.data
            var.dat=str(date.today())
            db.session.commit()
            return render_template("index.html",all_posts=posts,send=True,lg=portguese,logged_in=current_user.is_authenticated)

        new_user = User(email=formCont.email.data, message=formCont.message.data,dat=str(date.today()),)
        db.session.add(new_user)
        db.session.commit()
        return render_template("index.html",all_posts=posts, send=True,lg=portguese,logged_in=current_user.is_authenticated)

    return render_template("index.html", form=formCont, send=False, all_posts=posts, logged_in=current_user.is_authenticated,lg=portguese)


#limit login error

def loginError():
    global login_attempts

    ip_address = request.remote_addr
    today = str(date.today())
    print(login_attempts)

   
    if ip_address not in login_attempts:
        login_attempts[ip_address] = {}

    
    if today not in login_attempts[ip_address]:
        login_attempts[ip_address][today] = 1
    else:
       login_attempts[ip_address][today] += 1
        

    return False


#write  login_attempt     
def write_login_attempts(ip,dat):
    with open('static/files/warning.txt','a') as f:
        f.write(f'\n{ip} -> {dat} ')


def ip_count():
    global login_attempts
    today = str(date.today())
    ip_address = request.remote_addr
    
    if ip_address not in login_attempts:
        return False
    if login_attempts[ip_address][today] > 3:
        write_login_attempts(ip_address, today)
        print("-----------------save---------------")
        return True
        
    return False




#login adm
@app.route('/login', methods=["GET", "POST"])
def login():
    global invasor
    
    if ip_count() == True:
        invasor=True
        
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Adm.query.filter_by(name=form.name.data).first()

        # doesn't exist or password incorrect.
        if not user:
            flash("That name does not exist, please try again.")
            loginError()
            return redirect(url_for('login'))

        elif not check_password_hash(user.password, form.password.data):
            flash('Password incorrect, please try again.')
            loginError()
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('secrets'))

    return render_template("login.html", logged_in=current_user.is_authenticated,form=form)



#dowloads files 
@app.route('/download_users',methods=["GET"])
@login_required
def download_clients():
    write_file()
    return send_from_directory('static', path='files/clients.txt')


@app.route('/download_warning',methods=["GET"])
@login_required
def download_warnings():
    global invasor
    if invasor == True:
        invasor=False
    
    return send_from_directory('static', path='files/warning.txt')


# add new post
@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = ProjectForm()
    if form.validate_on_submit():
        new_post = Project(
            title=form.title.data,
            subtitle=form.subtitle.data,
            description=form.description.data,
            img_url=form.img_url.data,
            )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("make_post.html", form=form,logged_in=current_user.is_authenticated)


#delete post
@app.route("/delete/<int:post_id>",methods=["GET", "POST"])
@login_required
def delete_post(post_id):
    post_to_delete = Project.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('index'))

#delete all clients
@app.route("/delete_All",methods=["GET", "POST"])
@login_required
def delete_all():
    user = User.query.all()
    for u in user:
        db.session.delete(u)

    db.session.commit()
    return redirect(url_for('secrets'))

# view post (id)
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    portguese = What_accept_languages()
    requested_post = Project.query.get(post_id)
    return render_template("post.html", post=requested_post,lg=portguese,logged_in=current_user.is_authenticated)

#edit post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Project.query.get(post_id)
    edit_form = ProjectForm(
        title=post.title,
        subtitle=post.subtitle,
        description=post.description,
        img_url=post.img_url,
    )

    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle=edit_form.subtitle.data
        post.description = edit_form.description.data
        post.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make_post.html", form=edit_form, logged_in=current_user.is_authenticated)

#logout
@app.route('/logout',methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


#adm center
@app.route('/login/secrets',methods=["GET"])
@login_required
def secrets():
    global invasor
    return render_template("secrets.html",flag=invasor,logged_in=current_user.is_authenticated)



if __name__ == "__main__":
    app.run(debug=True)



