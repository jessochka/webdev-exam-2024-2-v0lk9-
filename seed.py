from app import create_app, db
from app.models import User, Role, Genre, Book, Cover
from werkzeug.security import generate_password_hash
import hashlib

def seed_data():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Initialize roles
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            admin_role = Role(name='Administrator', description='Full access to the system')
            db.session.add(admin_role)

        moderator_role = Role.query.filter_by(name='Moderator').first()
        if not moderator_role:
            moderator_role = Role(name='Moderator', description='Can edit books and moderate reviews')
            db.session.add(moderator_role)

        user_role = Role.query.filter_by(name='User').first()
        if not user_role:
            user_role = Role(name='User', description='Can leave reviews')
            db.session.add(user_role)

        db.session.commit()

        # Check if users exist before adding them
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('password'), last_name='Admin', first_name='Super', role_id=admin_role.id)
            db.session.add(admin)

        if not User.query.filter_by(username='moderator').first():
            moderator = User(username='moderator', password_hash=generate_password_hash('password'), last_name='Mod', first_name='Erat', role_id=moderator_role.id)
            db.session.add(moderator)

        if not User.query.filter_by(username='user').first():
            user = User(username='user', password_hash=generate_password_hash('password'), last_name='User', first_name='Regular', role_id=user_role.id)
            db.session.add(user)

        db.session.commit()

        # Check if genres exist before adding them
        genres = ['Фантастика', 'Научная фантастика', 'Мистика', 'Документальная литература', 'Детектив', 'Романтика']
        for genre_name in genres:
            if not Genre.query.filter_by(name=genre_name).first():
                genre = Genre(name=genre_name)
                db.session.add(genre)

        db.session.commit()

        # Check if covers exist before adding them
        if not Cover.query.filter_by(md5_hash=hashlib.md5(b'cover1').hexdigest()).first():
            cover1 = Cover(filename='cover1.jpg', mime_type='image/jpeg', md5_hash=hashlib.md5(b'cover1').hexdigest())
            db.session.add(cover1)

        if not Cover.query.filter_by(md5_hash=hashlib.md5(b'cover2').hexdigest()).first():
            cover2 = Cover(filename='cover2.jpg', mime_type='image/jpeg', md5_hash=hashlib.md5(b'cover2').hexdigest())
            db.session.add(cover2)

        db.session.commit()

        # Check if books exist before adding them
        if not Book.query.filter_by(title='Book One').first():
            book1 = Book(title='Book One', description='Description of book one', year=2021, publisher='Publisher One', author='Author One', volume=300, cover_id=cover1.id)
            db.session.add(book1)
            db.session.flush()  # Flush to get the id
            book1.genres.append(Genre.query.filter_by(name='Фантастика').first())
            book1.genres.append(Genre.query.filter_by(name='Научная фантастика').first())

        if not Book.query.filter_by(title='Book Two').first():
            book2 = Book(title='Book Two', description='Description of book two', year=2022, publisher='Publisher Two', author='Author Two', volume=250, cover_id=cover2.id)
            db.session.add(book2)
            db.session.flush()  # Flush to get the id
            book2.genres.append(Genre.query.filter_by(name='Документальная литература').first())

        db.session.commit()
        print('Database seeded successfully')

if __name__ == '__main__':
    seed_data()
