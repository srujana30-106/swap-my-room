from app import app, db, User, RoomPreference

with app.app_context():
    # First delete all room preferences (to handle foreign key constraints)
    RoomPreference.query.delete()
    db.session.commit()

    # Now delete all users
    User.query.delete()
    db.session.commit()

    print("All user credentials and room preferences have been deleted.")
