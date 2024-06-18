from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Book, Genre, Cover, Review, Role
import os
import hashlib

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    books = Book.query.order_by(Book.year.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('index.html', books=books.items, pagination=books)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember='remember' in request.form)
            return redirect(url_for('main.index'))
        else:
            flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def save_cover_file(file):
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])

    file.save(file_path)
    return filename

@bp.route('/book/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_admin():
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        year = request.form['year']
        publisher = request.form['publisher']
        author = request.form['author']
        volume = request.form['volume']
        genres = request.form.getlist('genres')

        if 'cover' not in request.files or request.files['cover'].filename == '':
            flash('Обложка обязательна для загрузки.', 'danger')
            return redirect(request.url)

        cover_file = request.files['cover']
        cover_filename = save_cover_file(cover_file)

        cover = Cover(filename=cover_filename, mime_type=cover_file.mimetype,
                      md5_hash=hashlib.md5(cover_file.read()).hexdigest())
        db.session.add(cover)
        db.session.commit()

        book = Book(title=title, description=description, year=year, publisher=publisher,
                    author=author, volume=volume, cover=cover)
        book.genres = [Genre.query.get(id) for id in genres]
        db.session.add(book)
        db.session.commit()
        flash('Книга успешно добавлена', 'success')
        return redirect(url_for('main.index'))

    genres = Genre.query.all()
    return render_template('book_form.html', title='Добавить книгу', genres=genres, selected_genres=[])

@bp.route('/book/<int:book_id>')
def view_book(book_id):
    book = Book.query.get_or_404(book_id)
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    return render_template('view_book.html', book=book, user_review=user_review)

@bp.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if not current_user.is_admin() and not current_user.is_moderator():
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.index'))

    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.title = request.form['title']
        book.description = request.form['description']
        book.year = request.form['year']
        book.publisher = request.form['publisher']
        book.author = request.form['author']
        book.volume = request.form['volume']
        genres = request.form.getlist('genres')
        book.genres = [Genre.query.get(id) for id in genres]

        if 'cover' in request.files and request.files['cover'].filename != '':
            cover_file = request.files['cover']
            cover_filename = save_cover_file(cover_file)
            book.cover.filename = cover_filename
            book.cover.mime_type = cover_file.mimetype
            book.cover.md5_hash = hashlib.md5(cover_file.read()).hexdigest()

        db.session.commit()
        flash('Книга успешно обновлена', 'success')
        return redirect(url_for('main.view_book', book_id=book.id))

    genres = Genre.query.all()
    selected_genres = [genre.id for genre in book.genres]
    return render_template('book_form.html', title='Редактировать книгу', book=book, genres=genres, selected_genres=selected_genres)

@bp.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    if not current_user.is_admin():
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.index'))

    book = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book.id).all()
    for review in reviews:
        db.session.delete(review)

    cover = book.cover

    db.session.delete(book)
    db.session.commit()

    if cover:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], cover.filename))
        except FileNotFoundError:
            pass
        db.session.delete(cover)
        db.session.commit()

    flash('Книга успешно удалена', 'success')
    return redirect(url_for('main.index'))


@bp.route('/review/add/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    book = Book.query.get_or_404(book_id)
    user_review = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()

    if user_review:
        flash('Вы уже оставили рецензию на эту книгу.', 'warning')
        return redirect(url_for('main.view_book', book_id=book_id))

    if request.method == 'POST':
        rating = request.form['rating']
        text = request.form['text']
        
        if not rating or not text:
            flash('Оценка и текст рецензии обязательны для заполнения.', 'danger')
            return redirect(request.url)

        review = Review(rating=rating, text=text, user_id=current_user.id, book_id=book_id)
        db.session.add(review)
        db.session.commit()
        flash('Рецензия успешно добавлена', 'success')
        return redirect(url_for('main.view_book', book_id=book_id))

    return render_template('review_form.html', title='Написать рецензию', book=book)

