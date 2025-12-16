from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_login import UserMixin

db = SQLAlchemy()

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # The user who is being notified (i.e., the user who was mentioned)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # The user who created the post (the mentioner)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # The post where the mention occurred
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    # Type of notification (e.g., 'mention') - useful for future expansion (like, follow, etc.)
    type = db.Column(db.String(50), default='mention')
    
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    # A flag to check if the user has viewed it
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy='dynamic'))
    actor = db.relationship('User', foreign_keys=[actor_id]) # User who caused the notification
    post = db.relationship('Post', foreign_keys=[post_id]) 

    def __repr__(self):
        return f'<Notification {self.type} for User {self.user_id}>'

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # The user who sent the message
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # The user who received the message
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    is_read = db.Column(db.Boolean, default=False)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_messages', lazy='dynamic'))

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.recipient_id}>'

class Follow(db.Model):
    __tablename__ = 'follows'
    id = db.Column(db.Integer, primary_key=True)
    
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='_follower_followed_uc'),)

    follower = db.relationship('User', foreign_keys=[follower_id], backref=db.backref('following_relationships', lazy='dynamic'))
    followed = db.relationship('User', foreign_keys=[followed_id], backref=db.backref('follower_relationships', lazy='dynamic'))

    def __repr__(self):
        return f'<Follower {self.follower_id} follows {self.followed_id}>'

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)  
    banner_image = db.Column(db.String(255), nullable=True)   
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    reactions = db.relationship('Reaction', backref='reactor', lazy='dynamic')
    
    comments = db.relationship('Comment', backref='commenter', lazy='dynamic')

    def set_password(self, password):
        """Hashes the password for secure storage."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the stored hash against a provided password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def followers(self):
        return [r.follower for r in self.follower_relationships.all()]
    
    @property
    def following(self):
        return [r.followed for r in self.following_relationships.all()]

class Post(db.Model):
    __tablename__ = 'post'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    reactions = db.relationship('Reaction', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.id} by {self.user_id}>'

class Reaction(db.Model):
    __tablename__ = 'reaction'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    type = db.Column(db.String(20), nullable=False) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', 'type', name='_user_post_type_uc'),)

    def __repr__(self):
        return f'<Reaction {self.type} on Post {self.post_id} by User {self.user_id}>'

class Comment(db.Model):
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id} by User {self.user_id}>'