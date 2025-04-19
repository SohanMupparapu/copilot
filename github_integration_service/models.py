# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tokens = db.relationship('GitHubToken', backref='user', lazy=True, cascade="all, delete-orphan")
    subscriptions = db.relationship('RepositorySubscription', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

class GitHubToken(db.Model):
    __tablename__ = 'github_tokens'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    access_token = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<GitHubToken for user_id={self.user_id}>'

class RepositorySubscription(db.Model):
    __tablename__ = 'repo_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    repository_url = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_event_id = db.Column(db.String(60), nullable=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    last_run_id = db.Column(db.Integer, nullable=True)
    new_tests_available = db.Column(db.Boolean, default=False, nullable=False)
    runs = db.relationship('TestRun', backref='subscription', lazy=True, cascade="all, delete-orphan")
    document = db.relationship(
        'Document', backref='subscription', uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<RepositorySubscription {self.repository_url}>'
class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(
        db.Integer, db.ForeignKey('repo_subscriptions.id'),
        nullable=False, unique=True
    )
    filename = db.Column(db.String(200), nullable=False)
    content = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

class TestRun(db.Model):
    __tablename__ = 'test_runs'
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('repo_subscriptions.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    new_tests = db.Column(db.Integer, nullable=False)
    removed_tests = db.Column(db.Integer, nullable=False)
    error_message = db.Column(db.Text)
    log = db.Column(db.Text)

    def __repr__(self):
        return f'<TestRun {self.id} - {self.status}>'

# Repositories (Data Access Layer)
class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)
    
    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def create(username):
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
        return user

class TokenRepository:
    @staticmethod
    def get_for_user(user_id):
        return GitHubToken.query.get(user_id)
    
    @staticmethod
    def store(user_id, token):
        record = TokenRepository.get_for_user(user_id)
        if record:
            record.access_token = token
            record.updated_at = datetime.utcnow()
        else:
            record = GitHubToken(user_id=user_id, access_token=token)
            db.session.add(record)
        db.session.commit()
        return record

class SubscriptionRepository:
    @staticmethod
    def get_active_subscriptions():
        return RepositorySubscription.query.filter_by(is_active=True).all()
    
    @staticmethod
    def get_user_subscriptions(user_id):
        return RepositorySubscription.query.filter_by(user_id=user_id).all()
    @staticmethod
    def create(user_id, repository_url):
        # Avoid duplicate subscriptions
        existing = RepositorySubscription.query.filter_by(
            user_id=user_id,
            repository_url=repository_url
        ).first()
        if existing:
            return None  # or raise a custom DuplicateSubscriptionError

        sub = RepositorySubscription(
            user_id=user_id,
            repository_url=repository_url
        )
        db.session.add(sub)
        db.session.commit()
        return sub
    
    @staticmethod
    def update_last_event(subscription, event_id):
        subscription.last_event_id = event_id
        subscription.updated_at = datetime.utcnow()
        db.session.commit()

class TestRunRepository:
    @staticmethod
    def create(subscription_id, status, new_tests=0, removed_tests=0, error_message=None, log=None):
        test_run = TestRun(
            subscription_id=subscription_id,
            status=status,
            new_tests=new_tests,
            removed_tests=removed_tests,
            error_message=error_message,
            log=log
        )
        db.session.add(test_run)
        db.session.commit()
        return test_run