from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from .models import Post, User, Comment, Like
from . import db, admin_permission

from datetime import datetime

views = Blueprint("views", __name__)


@views.route("/")
@views.route(" '/home/view/<int:page>' ,methods=['GET']")
@views.route("/home")
@login_required
def home(page=1):
    per_page = 100
    posts = Post.query.paginate(page,per_page,error_out=False)
    return render_template("home.html", user=current_user, posts=posts, flag=0)


@login_required
@views.route("/uploads/<path:name>")
def download_file(name):
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], name
    )


@views.route("/home/tag", methods=['POST'])
@login_required
def search_by_tags():
    tagname = request.form.get("tagname")
    posts = Post.query.filter(Post.text.contains(f"{tagname}")).all()
    return render_template("home.html", user=current_user, posts=posts, flag=1)


@views.route("/home", methods=['GET', 'POST'])
@login_required
def create_post():
    if not admin_permission.can():
        flash("You need to be an admin to add posts", category='error')
        return redirect(url_for('views.home'))

    if request.method == "POST":
        text = request.form.get('text')
        file = request.files.get("file")

        if file.filename == '':
            filename = None
        else:
            # hasher = hashlib.md5()
            # hasher.update(file.stream.read())
            filename = f"{datetime.utcnow()}_{file.filename}"
            file.save(current_app.config['UPLOAD_FOLDER'].joinpath(filename))

        if not text:
            flash('Post cannot be empty', category='error')
            return redirect(url_for('views.home'))
        else:
            post = Post(text=text, author=current_user.id, filename=filename)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('index.html', user=current_user)


@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')

    elif current_user.username != "admin":
        flash('You do not have permission to delete this post.', category='error')

    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))


@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)


@views.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(
                text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('views.home'))


@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('views.home'))


@views.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(
        author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})

@views.route("/profile")
def profile(page=1):
    if(current_user.username=="admin"):
        
        per_page = 100
        posts = Post.query.paginate(page,per_page,error_out=False)
        return render_template('profile_admin.html', user=current_user,posts=posts)
    else:
        return render_template('profile_user.html')

@views.route("/profile", methods=['GET', 'POST'])
@login_required
def create_post_adminpage():
    if not admin_permission.can():
        flash("You need to be an admin to add posts", category='error')
        return redirect(url_for('views.profile'))

    if request.method == "POST":
        text = request.form.get('text')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.profile'))

    return render_template('profile_admin.html', user=current_user)

@views.route("/friends", methods=['GET', 'POST'])
@login_required
def friends():
    return render_template('friends.html',user=current_user)

@views.route("/about")
def about():
    return render_template('about.html')
