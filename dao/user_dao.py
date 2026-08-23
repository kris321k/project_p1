from models.user import User
from config.database import db
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

class UserDao :

    def create_user(self, user) :
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except SQLAlchemyError as error:
            db.session.rollback()
            raise error
    
    def get_user_by_id(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)
    
    def get_user_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        return db.session.scalar(
            db.select(User).where(func.lower(User.email) == normalized_email)
        )
    
    def get_user_by_username(self, username: str) -> User | None:
        return User.query.filter_by(
            username = username
        ).first()


    def get_all_users(self) -> list[User]:
        return list(db.session.scalars(db.select(User).order_by(User.username)))
    
    def update_user(self, user: User) -> User | None:
        try:
            db.session.commit()
            return user
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating user: {e}")
            return None
        
    def delete_user(self, user: User) -> bool:
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error deleting user: {e}")
            return False
    