from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, request, redirect, url_for 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
import os

print("Current folder:", os.getcwd())
print("Database exists:", os.path.exists("instance/database.db"))
print("Database exists:", os.path.exists("database.db"))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
import os
print("Current Folder:", os.getcwd())
print("Database Path:", os.path.abspath("instance/database.db"))

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
app.secret_key = "your_secret_key"

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), default="default.png")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200))
    category = db.Column(db.String(50))
    likes = db.Column(db.Integer, default=0)
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

with app.app_context():
    db.create_all()
        
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db. ForeignKey('post.id'), nullable=False)    
@app.context_processor
def inject_like_model():
    return dict(Like=Like)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
 
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            login_user(user)
            return redirect(url_for("home"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/home")
def home():

    search = request.args.get("search", "").strip()

    if search:
        posts = Post.query.filter(
            db.or_(
                Post.title.ilike(f"%{search}%"),
                Post.content.ilike(f"%{search}%"),
                Post.category.ilike(f"%{search}%"),
                Post.author.ilike(f"%{search}%")
            )
        ).all()
    else:
        posts = Post.query.all()

    return render_template("home.html", posts=posts)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def view_post(post_id):

    post = Post.query.get_or_404(post_id)

    # Get all comments for this post
    comments = Comment.query.filter_by(post_id=post_id).all()

    if request.method == "POST":

        content = request.form["content"]

        comment = Comment(
            author=current_user.username,
            content=content,
            post_id=post.id
        )

        db.session.add(comment)
        db.session.commit()

        return redirect(url_for("view_post", post_id=post.id))

    # Show the blog page
    return render_template(
        "view_post.html",
        post=post,
        comments=comments
    )

@app.route("/delete_my_comment/<int:id>")
@login_required
def delete_my_comment(id):

    comment = comment.query.get_or_404(id)

    if comment.author != current_user.username:
        return "Acccess Denief! You cannot delete someone else's comment."

    post_id = comment.post_id

    db.session.delete(comment)
    db.session.commit()

    return redirect(url_for("view_post", post_id=post_id))
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


@app.route("/admin")
@login_required
def admin():

    # Only allow the admin account
    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    users = User.query.all()
    posts = Post.query.all()
    comments = Comment.query.all()

    return render_template(
        "admin.html",
        users=users,
        posts=posts,
        comments=comments
    )

@app.route("/delete_user/<int:id>")
@login_required
def delete_user(id):

    print("Current logged in email:", current_user.email)
    
    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/delete_comment/<int:id>")
@login_required
def delete_comment(id):

    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    comment = Comment.query.get_or_404(id)

    db.session.delete(comment)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/admin/delete_post/<int:id>")
@login_required
def admin_delete_post(id):

    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    post = Post.query.get_or_404(id)

    db.session.delete(post)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/admin/delete_user/<int:id>")
@login_required
def admin_delete_user(id):

    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    user = User.query.get_or_404(id)

    # Prevent deleting the admin account
    if user.email == "yugrahangdale56@gmail.com":
        return "You cannot delete the admin account."

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        author = current_user.username 
        category = request.form["category"]

        image = request.files["image"]
        filename = ""
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            image.save(
                os.path.join(app.config["UPLOAD_FOLDER"],filename)
            )

        post = Post(
            title=title,
            content=content,
            author=author,
            image=filename,
            category=category
        )

        db.session.add(post)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("create_post.html")

@app.route("/delete_post/<int:id>")
@login_required
def delete_post(id):

    post = Post.query.get_or_404(id)

    # Only the owner can delete the post
    if post.author != current_user.username:
        return "Access Denied! You cannot delete someone else's post."

    # Delete the uploaded image from the folder
    if post.image:
        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            post.image
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete the post from database
    db.session.delete(post)
    db.session.commit()

    return redirect(url_for("home"))

@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):

    post = Post.query.get_or_404(post_id)

    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        post_id=post.id
    ).first()

    if not existing_like:

        new_like = Like(
            user_id=current_user.id,
            post_id=post.id
        )

        db.session.add(new_like)

        post.likes += 1

        db.session.commit()

    return redirect(url_for("home"))

@app.route("/edit_post/<int:id>", methods=["GET", "POST"])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)

    if post.author != current_user.username:
        return "Access Denied! You cannot  edit someone else's post."

    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        
        db.session.commit()

        return redirect(url_for("/home"))

    return render_template("edit_post.html", post=post)

@app.route("/upload_profile", methods=["POST"])
@login_required
def upload_profile():

    image = request.files["profile_pic"]

    if image and image.filename != "":
        filename = secure_filename(image.filename)

        folder = os.path.join("static", "profile")
        os.makedirs(folder, exist_ok=True)

        image.save(os.path.join(folder, filename))

        current_user.profile_pic = filename

        db.session.commit()

    return redirect(url_for("profile"))

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()

        if not username:
            return "Username cannot be empty."

        if not email:
            return "Email cannot be empty."

        current_user.username = username
        current_user.email = email

        db.session.commit()

        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=current_user)

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))

@login_manager.user_loader
def load_user(user_id):
   return db.session.get(User, int(user_id))

@app.route("/profile")
@login_required
def profile():
    user = current_user

    posts = Post.query.filter_by(author=user.username).all()

    return render_template(
        "profile.html",
        user=user,
        posts=posts
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
    app.run(host="0.0.0.0", port=5000, debug=True)
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, request, redirect, url_for 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
import os

print("Current folder:", os.getcwd())
print("Database exists:", os.path.exists("instance/database.db"))
print("Database exists:", os.path.exists("database.db"))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
import os
print("Current Folder:", os.getcwd())
print("Database Path:", os.path.abspath("instance/database.db"))

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
app.secret_key = "your_secret_key"

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), default="default.png")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200))
    category = db.Column(db.String(50))
    likes = db.Column(db.Integer, default=0)
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db. ForeignKey('post.id'), nullable=False)    
@app.context_processor
def inject_like_model():
    return dict(Like=Like)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
 
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            login_user(user)
            return redirect(url_for("home"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/home")
def home():

    search = request.args.get("search", "").strip()

    if search:
        posts = Post.query.filter(
            db.or_(
                Post.title.ilike(f"%{search}%"),
                Post.content.ilike(f"%{search}%"),
                Post.category.ilike(f"%{search}%"),
                Post.author.ilike(f"%{search}%")
            )
        ).all()
    else:
        posts = Post.query.all()

    return render_template("home.html", posts=posts)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def view_post(post_id):

    post = Post.query.get_or_404(post_id)

    # Get all comments for this post
    comments = Comment.query.filter_by(post_id=post_id).all()

    if request.method == "POST":

        content = request.form["content"]

        comment = Comment(
            author=current_user.username,
            content=content,
            post_id=post.id
        )

        db.session.add(comment)
        db.session.commit()

        return redirect(url_for("view_post", post_id=post.id))

    # Show the blog page
    return render_template(
        "view_post.html",
        post=post,
        comments=comments
    )

@app.route("/delete_my_comment/<int:id>")
@login_required
def delete_my_comment(id):

    comment = comment.query.get_or_404(id)

    if comment.author != current_user.username:
        return "Acccess Denief! You cannot delete someone else's comment."

    post_id = comment.post_id

    db.session.delete(comment)
    db.session.commit()

    return redirect(url_for("view_post", post_id=post_id))
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


@app.route("/admin")
@login_required
def admin():

    # Only allow the admin account
    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    users = User.query.all()
    posts = Post.query.all()
    comments = Comment.query.all()

    return render_template(
        "admin.html",
        users=users,
        posts=posts,
        comments=comments
    )

@app.route("/delete_user/<int:id>")
@login_required
def delete_user(id):

    print("Current logged in email:", current_user.email)
    
    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/delete_comment/<int:id>")
@login_required
def delete_comment(id):

    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    comment = Comment.query.get_or_404(id)

    db.session.delete(comment)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/admin/delete_post/<int:id>")
@login_required
def admin_delete_post(id):

    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    post = Post.query.get_or_404(id)

    db.session.delete(post)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/admin/delete_user/<int:id>")
@login_required
def admin_delete_user(id):

    if current_user.email != "yugrahangdale56@gmail.com":
        return "Access Denied"

    user = User.query.get_or_404(id)

    # Prevent deleting the admin account
    if user.email == "yugrahangdale56@gmail.com":
        return "You cannot delete the admin account."

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        author = current_user.username 
        category = request.form["category"]

        image = request.files["image"]
        filename = ""
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            image.save(
                os.path.join(app.config["UPLOAD_FOLDER"],filename)
            )

        post = Post(
            title=title,
            content=content,
            author=author,
            image=filename,
            category=category
        )

        db.session.add(post)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("create_post.html")

@app.route("/delete_post/<int:id>")
@login_required
def delete_post(id):

    post = Post.query.get_or_404(id)

    # Only the owner can delete the post
    if post.author != current_user.username:
        return "Access Denied! You cannot delete someone else's post."

    # Delete the uploaded image from the folder
    if post.image:
        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            post.image
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete the post from database
    db.session.delete(post)
    db.session.commit()

    return redirect(url_for("home"))

@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):

    post = Post.query.get_or_404(post_id)

    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        post_id=post.id
    ).first()

    if not existing_like:

        new_like = Like(
            user_id=current_user.id,
            post_id=post.id
        )

        db.session.add(new_like)

        post.likes += 1

        db.session.commit()

    return redirect(url_for("home"))

@app.route("/edit_post/<int:id>", methods=["GET", "POST"])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)

    if post.author != current_user.username:
        return "Access Denied! You cannot  edit someone else's post."

    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        
        db.session.commit()

        return redirect(url_for("/home"))

    return render_template("edit_post.html", post=post)

@app.route("/upload_profile", methods=["POST"])
@login_required
def upload_profile():

    image = request.files["profile_pic"]

    if image and image.filename != "":
        filename = secure_filename(image.filename)

        folder = os.path.join("static", "profile")
        os.makedirs(folder, exist_ok=True)

        image.save(os.path.join(folder, filename))

        current_user.profile_pic = filename

        db.session.commit()

    return redirect(url_for("profile"))

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()

        if not username:
            return "Username cannot be empty."

        if not email:
            return "Email cannot be empty."

        current_user.username = username
        current_user.email = email

        db.session.commit()

        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=current_user)

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))

@login_manager.user_loader
def load_user(user_id):
   return db.session.get(User, int(user_id))

@app.route("/profile")
@login_required
def profile():
    user = current_user

    posts = Post.query.filter_by(author=user.username).all()

    return render_template(
        "profile.html",
        user=user,
        posts=posts
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
    app.run(host="0.0.0.0", port=5000, debug=True)