from app import app, db

if __name__ == '__main__':
    # push the app context so SQLAlchemy knows which app to use
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Dropped & recreated all tables.")
