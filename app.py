import os
from flask import Flask, render_template, redirect, url_for, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from models import db, User, Post, Reaction, Follow, Comment, Notification, Message # Import your models
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import or_, desc, func
import re

# --- Flask App Initialization ---
app = Flask(__name__)

# Basic configuration
# NOTE: Replace 'a_super_secret_key' with a strong, random key in production
app.config['SECRET_KEY'] = 'a_super_secret_key' 
# SQLite for development: a file named chirp.db will be created in the instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chirp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirects unauthenticated users to this route

# --- User Loader (For Flask-Login) ---
@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to reload the user object from the session ID."""
    return User.query.get(int(user_id))

# --- Database Setup Command ---
@app.cli.command('init-db')
def init_db():
    """Create all tables and a dummy user."""
    with app.app_context():
        db.create_all()
        
        # Create a dummy user for testing the login
        if User.query.filter_by(username='testuser').first() is None:
            test_user = User(username='testuser', email='test@chirp.com')
            test_user.set_password('password') # Password is 'password'
            db.session.add(test_user)
            db.session.commit()
            print("Database initialized and 'testuser' created (password: 'password').")
        else:
            print("Database tables already exist.")

# --- Frontend Routes (Serving HTML) ---

@app.route('/')

@app.route('/signup', methods=['GET'])
def signup():
    """Serve the sign-up page."""
    if current_user.is_authenticated:
        return redirect(url_for('timeline'))
    return render_template('signup.html')

@app.route('/login', methods=['GET'])
def login():
    """Serve the sign-in page."""
    if current_user.is_authenticated:
        return redirect(url_for('timeline'))
    return render_template('login.html') 

@app.route('/timeline')
@login_required 
def timeline():
    """Serve the main timeline page."""
    # NOTE: We are serving the static file for now. 
    # In a real app, this would query the DB and pass data to a Jinja template.
    return render_template('timeline.html', active_page='timeline') 

@app.route('/bookmarks')
@login_required
def bookmarks_page():
    """Serves the bookmarks view page (bookmarks.html)."""
    # This is the function name your Jinja link is expecting!
    return render_template('bookmarks.html', active_page='bookmarks') 

@app.route('/profile/<username>')
@login_required
def profile(username):
    """Serves the user profile page (profile.html)."""

    return render_template('profile.html', active_page='profile', target_username=username)

@app.route('/relationships/<view_type>/<username>')
@login_required
def relationships_page(view_type, username):
    """Serves the page listing followers or following."""
    return render_template('relationships.html', active_page='profile', target_username=username, view_type=view_type)

@app.route('/notifications')
@login_required
def notifications():
    """Renders the Notifications page."""
    return render_template('notifications.html', active_page='notifications')

@app.route('/messages')
@login_required
def messages():
    """Renders the Direct Messages page."""
    return render_template('messages.html', active_page='messages' )

@app.route('/search')
@login_required
def search_page():
    """Renders the Search page."""
    return render_template('search.html', active_page='search')

# --- Authentication API Routes ---

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handles the login form submission from login.html (via app.js fetch)."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    
    if user is None or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    login_user(user)
    return jsonify({'success': True, 'redirect': url_for('timeline')})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    """Handles new user registration."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password) 
    
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    
    return jsonify({
        'success': True, 
        'message': 'Account created successfully!',
        'redirect': url_for('timeline')
    })

@app.route('/logout')
def logout():
    """Logs out the current user."""
    logout_user()
    return redirect(url_for('login'))

# --- Image Upload Helper Functions ---

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Image Upload API Routes ---

@app.route('/api/upload/profile-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Upload profile picture for current user."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
    
    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"profile_{current_user.id}_{datetime.utcnow().timestamp()}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        
        current_user.profile_image = f"uploads/{filename}"
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile image updated',
            'image_url': f"/static/uploads/{filename}"
        })
    
    except Exception as e:
        print(f"Error uploading profile image: {e}")
        return jsonify({'success': False, 'message': 'Error uploading file'}), 500

@app.route('/api/upload/banner-image', methods=['POST'])
@login_required
def upload_banner_image():
    """Upload banner image for current user."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
    
    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"banner_{current_user.id}_{datetime.utcnow().timestamp()}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        
        current_user.banner_image = f"uploads/{filename}"
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Banner image updated',
            'image_url': f"/static/uploads/{filename}"
        })
    
    except Exception as e:
        print(f"Error uploading banner image: {e}")
        return jsonify({'success': False, 'message': 'Error uploading file'}), 500

# --- Core Chirp API Routes ---

@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    """
    Handles creating a new post (chirp) and creates notifications for any @mentions 
    found within the content.
    """
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'success': False, 'message': 'Content cannot be empty'}), 400

    new_post = Post(user_id=current_user.id, content=content)
    db.session.add(new_post)
    
    # 1. Commit the post to the database to get the unique post ID
    db.session.commit()

    notifications_to_add = []

    # --- A. MENTION DETECTION AND NOTIFICATION (EXISTING LOGIC) ---
    mentions = re.findall(r'@(\w+)', content)
    
    mentioned_user_ids = set() # Use a set to track users who were mentioned

    if mentions:
        unique_mentioned_usernames = list(set(mentions))
        for username in unique_mentioned_usernames:
            mentioned_user = User.query.filter_by(username=username).first()
            
            if mentioned_user and mentioned_user.id != current_user.id:
                # Add ID to set for later exclusion from follower notifications
                mentioned_user_ids.add(mentioned_user.id) 
                
                notification = Notification(
                    user_id=mentioned_user.id,
                    actor_id=current_user.id,
                    post_id=new_post.id,
                    type='mention' # Set the type of notification
                )
                notifications_to_add.append(notification)
    
    # --- B. NEW POST (FOLLOWER) NOTIFICATION LOGIC ---
    
    # Find all users currently following the author of the new post
    # current_user.follower_relationships returns the Follow objects
    followers = current_user.follower_relationships.all()
    
    for follow_relationship in followers:
        follower_id = follow_relationship.follower_id
        
        # EXCLUSION: Don't send a 'new_post' notification if the follower was already
        # sent a 'mention' notification for this same post.
        if follower_id not in mentioned_user_ids:
            new_post_notification = Notification(
                user_id=follower_id,           # The user receiving the notification
                actor_id=current_user.id,      # The author of the post
                post_id=new_post.id,           
                type='new_post'                # <-- NEW TYPE
            )
            notifications_to_add.append(new_post_notification)
            
    # --- C. COMMIT ALL GENERATED NOTIFICATIONS ---
    
    if notifications_to_add:
        db.session.add_all(notifications_to_add)
        db.session.commit()
    
    # ------------------ END INLINED LOGIC ----------------------

    return jsonify({
        'success': True, 
        'post': {
            'id': new_post.id,
            'username': current_user.username,
            'handle': '@' + current_user.username,
            'time': 'Just now',
            'content': new_post.content,
            'likes': 0,
            'retweets': 0,
            'comments': 0,
            'profile_image': current_user.profile_image or 'uploads/default-avatar.jpg',
        'canDelete': True
        }
    }), 201

@app.route('/api/posts', methods=['GET'])
@login_required
def get_timeline_posts():
    """
    Fetches posts for the timeline.
    Shows ONLY posts from users that the current user is following + their own posts.
    """
    following_relationships = current_user.following_relationships.all()
    following_ids = [rel.followed_id for rel in following_relationships]
    
    following_ids.append(current_user.id)
    
    posts = Post.query.filter(Post.user_id.in_(following_ids))\
                      .order_by(Post.timestamp.desc())\
                      .all()
    
    posts_list = []
    for post in posts:
        user = User.query.get(post.user_id)
        
        like_count = Reaction.query.filter_by(post_id=post.id, type='LIKE').count()
        retweet_count = Reaction.query.filter_by(post_id=post.id, type='RETWEET').count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        is_liked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='LIKE'
        ).first() is not None
        
        is_retweeted = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='RETWEET'
        ).first() is not None
        
        is_bookmarked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='BOOKMARK'
        ).first() is not None
        
        posts_list.append({
            'id': post.id,
            'username': user.username,
            'handle': '@' + user.username,
            'content': post.content,
            'time': post.timestamp.strftime('%b %d'),
            'likes': like_count,
            'retweets': retweet_count,
            'comments': comment_count,
            'isLiked': is_liked,
            'isRetweeted': is_retweeted,
            'isBookmarked': is_bookmarked,
        'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
        'canDelete': post.user_id == current_user.id,
        })
    
    return jsonify({
        'success': True,
        'posts': posts_list
    })

# --- Reaction/Bookmark API Route ---

@app.route('/api/react', methods=['POST'])
@login_required
def react_to_post():
    """Handles LIKE, RETWEET, and BOOKMARK actions."""
    data = request.get_json()
    post_id = data.get('postId')
    reaction_type = data.get('reactionType') 
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'message': 'Post not found'}), 404
        
    existing_reaction = Reaction.query.filter_by(
        user_id=current_user.id, 
        post_id=post_id, 
        type=reaction_type
    ).first()

    if existing_reaction:
        db.session.delete(existing_reaction)
        db.session.commit()
        toggled = False
    else:
        new_reaction = Reaction(
            user_id=current_user.id,
            post_id=post_id,
            type=reaction_type
        )
        db.session.add(new_reaction)
        db.session.commit()
        toggled = True

    new_count = Reaction.query.filter_by(post_id=post_id, type=reaction_type).count()

    return jsonify({
        'success': True,
        'reactionType': reaction_type,
        'newCount': new_count,
        'toggled': toggled
    })

# --- Delete Post API Route ---

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """
    Deletes a post. Only the author can delete their own post.
    Comments and reactions are automatically deleted via cascade.
    """
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'success': False, 'message': 'Post not found'}), 404
    
    # Check if current user is the author
    if post.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'You can only delete your own posts'}), 403
    
    # Delete the post (comments and reactions will be cascade deleted)
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Post deleted successfully'
    })

# --- Bookmarks API Route ---

@app.route('/api/bookmarks', methods=['GET'])
@login_required
def get_bookmarks():
    """
    Fetches all posts that the current user has bookmarked.
    """
    bookmarks = Reaction.query.filter_by(
        user_id=current_user.id,
        type='BOOKMARK'
    ).order_by(Reaction.timestamp.desc()).all()
    
    posts_list = []
    for bookmark in bookmarks:
        post = Post.query.get(bookmark.post_id)
        if not post:
            continue
            
        user = User.query.get(post.user_id)
        
        like_count = Reaction.query.filter_by(post_id=post.id, type='LIKE').count()
        retweet_count = Reaction.query.filter_by(post_id=post.id, type='RETWEET').count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        is_liked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='LIKE'
        ).first() is not None
        
        is_retweeted = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='RETWEET'
        ).first() is not None
        
        posts_list.append({
            'id': post.id,
            'username': user.username,
            'handle': '@' + user.username,
            'content': post.content,
            'time': post.timestamp.strftime('%b %d'),
            'likes': like_count,
            'retweets': retweet_count,
            'comments': comment_count,
            'isLiked': is_liked,
            'isRetweeted': is_retweeted,
            'isBookmarked': True,  
        'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
        'canDelete': post.user_id == current_user.id,
        })
    
    return jsonify({
        'success': True,
        'posts': posts_list
    })

# --- Comments API Routes ---

@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
@login_required
def get_comments(post_id):
    """
    Fetches all comments for a specific post.
    """
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'message': 'Post not found'}), 404
    
    comments = Comment.query.filter_by(post_id=post_id)\
                            .order_by(Comment.timestamp.asc())\
                            .all()
    
    comments_list = []
    for comment in comments:
        user = User.query.get(comment.user_id)
        comments_list.append({
            'id': comment.id,
            'username': user.username,
            'handle': '@' + user.username,
            'content': comment.content,
            'time': comment.timestamp.strftime('%b %d, %Y at %I:%M %p'),
            'canDelete': comment.user_id == current_user.id
        })
    
    return jsonify({
        'success': True,
        'comments': comments_list
    })

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def add_comment(post_id):
    """
    Adds a new comment to a specific post.
    """
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'message': 'Post not found'}), 404
    
    data = request.get_json()
    content = data.get('content')
    
    if not content or not content.strip():
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
    
    new_comment = Comment(
        user_id=current_user.id,
        post_id=post_id,
        content=content.strip()
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    comment_count = Comment.query.filter_by(post_id=post_id).count()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': new_comment.id,
            'username': current_user.username,
            'handle': '@' + current_user.username,
            'content': new_comment.content,
            'time': new_comment.timestamp.strftime('%b %d, %Y at %I:%M %p'),
            'canDelete': True
        },
        'newCommentCount': comment_count
    }), 201

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """
    Deletes a comment (only by the user who created it).
    """
    comment = Comment.query.get(comment_id)
    
    if not comment:
        return jsonify({'success': False, 'message': 'Comment not found'}), 404
    
    if comment.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Not authorized to delete this comment'}), 403
    
    post_id = comment.post_id
    
    db.session.delete(comment)
    db.session.commit()
    
    comment_count = Comment.query.filter_by(post_id=post_id).count()
    
    return jsonify({
        'success': True,
        'message': 'Comment deleted successfully',
        'newCommentCount': comment_count
    })

# --- Profile API Route ---

@app.route('/api/profile/<username>', methods=['GET'])
@login_required
def get_profile(username):
    """
    Fetches a user's profile information and their posts.
    Returns profile data and a list of posts authored by the user.
    """
    user = User.query.filter_by(username=username).first()
    
    if user is None:
        return jsonify({'success': False, 'message': f'User {username} not found.'}), 404
    
    follower_count = user.follower_relationships.count() 
    following_count = user.following_relationships.count() 
    
    is_following = Follow.query.filter_by(
        follower_id=current_user.id,
        followed_id=user.id
    ).first() is not None
    
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
    
    total_likes = 0
    total_retweets = 0
    total_comments = 0
    
    posts_list = []
    for post in posts:
        like_count = Reaction.query.filter_by(post_id=post.id, type='LIKE').count()
        retweet_count = Reaction.query.filter_by(post_id=post.id, type='RETWEET').count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        total_likes += like_count
        total_retweets += retweet_count
        total_comments += comment_count
        
        is_liked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='LIKE'
        ).first() is not None
        
        is_retweeted = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='RETWEET'
        ).first() is not None
        
        is_bookmarked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='BOOKMARK'
        ).first() is not None
        
        posts_list.append({
            'id': post.id,
            'username': user.username, 
            'handle': '@' + user.username, 
            'content': post.content,
            'time': post.timestamp.strftime('%b %d'), 
            'likes': like_count,
            'retweets': retweet_count,
            'comments': comment_count,
            'isLiked': is_liked,
            'isRetweeted': is_retweeted,
            'isBookmarked': is_bookmarked,
        'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
        'canDelete': post.user_id == current_user.id,
        })
    
    profile_data = {
        'username': user.username,
        'handle': '@' + user.username,
        'followerCount': follower_count,
        'followingCount': following_count,
        'isFollowing': is_following,
        'isOwnProfile': user.id == current_user.id,
        'joinedDate': user.created_at.strftime('%B %Y') if hasattr(user, 'created_at') and user.created_at else 'Unknown',
        'totalLikes': total_likes,
        'totalRetweets': total_retweets,
        'totalComments': total_comments,
        'profileImage': f"/static/{user.profile_image}" if user.profile_image else '/static/uploads/default-avatar.jpg',
        'bannerImage': f"/static/{user.banner_image}" if user.banner_image else None,
    }
    
    return jsonify({
        'success': True,
        'profile': profile_data,
        'posts': posts_list
    })

@app.route('/api/notifications', methods=['GET'])
@login_required
def api_load_notifications():
    """
    Fetches the current user's unread and recent notifications (mentions).
    Marks them as read upon retrieval.
    """
    try:
        # 1. Fetch notifications for the current user, ordered by newest first
        # Join with the User table to get the username of the 'actor' 
        notifications = db.session.query(Notification, User.username.label('actor_username'))\
            .join(User, Notification.actor_id == User.id)\
            .filter(Notification.user_id == current_user.id)\
            .order_by(Notification.timestamp.desc())\
            .limit(50)\
            .all()

        # 2. Prepare the data for JSON response
        notifications_list = []
        unread_ids = []

        for notification, actor_username in notifications:
            notifications_list.append({
                'id': notification.id,
                'post_id': notification.post_id,
                'actor_id': notification.actor_id,
                'actor_username': actor_username,
                'type': notification.type, 
                'is_read': notification.is_read,
                # Use .isoformat() to send a proper string for JavaScript's Date object
                'timestamp': notification.timestamp.isoformat() 
            })
            
            # 3. Collect unread notification IDs to mark them as read
            if not notification.is_read:
                unread_ids.append(notification.id)

        # 4. Mark unread notifications as read in the database
        if unread_ids:
            # Efficiently update all relevant rows in one go
            Notification.query.filter(Notification.id.in_(unread_ids)).update(
                {'is_read': True}, 
                synchronize_session='fetch'
            )
            db.session.commit()

        # 5. Return the list of notifications
        return jsonify({
            'success': True, 
            'notifications': notifications_list
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error loading notifications for user {current_user.id}: {e}")
        return jsonify({'success': False, 'message': 'Internal server error while fetching notifications.'}), 500

# --- Profile Interaction Endpoints (Liked, Retweeted, Commented) ---

@app.route('/api/profile/<username>/liked', methods=['GET'])
@login_required
def get_user_liked_posts(username):
    """
    Fetches all posts that the user has liked.
    """
    user = User.query.filter_by(username=username).first()
    
    if user is None:
        return jsonify({'success': False, 'message': f'User {username} not found.'}), 404
    
    liked_reactions = Reaction.query.filter_by(user_id=user.id, type='LIKE')\
                                     .order_by(Reaction.timestamp.desc())\
                                     .all()
    
    posts_list = []
    for reaction in liked_reactions:
        post = Post.query.get(reaction.post_id)
        if not post:
            continue
            
        post_author = User.query.get(post.user_id)
        
        like_count = Reaction.query.filter_by(post_id=post.id, type='LIKE').count()
        retweet_count = Reaction.query.filter_by(post_id=post.id, type='RETWEET').count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        is_liked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='LIKE'
        ).first() is not None
        
        is_retweeted = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='RETWEET'
        ).first() is not None
        
        is_bookmarked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='BOOKMARK'
        ).first() is not None
        
        posts_list.append({
            'id': post.id,
            'username': post_author.username,
            'handle': '@' + post_author.username,
            'content': post.content,
            'time': post.timestamp.strftime('%b %d'),
            'likes': like_count,
            'retweets': retweet_count,
            'comments': comment_count,
            'isLiked': is_liked,
            'isRetweeted': is_retweeted,
            'isBookmarked': is_bookmarked,
        'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
        'canDelete': post.user_id == current_user.id,
        })
    
    return jsonify({
        'success': True,
        'posts': posts_list
    })

@app.route('/api/profile/<username>/retweeted', methods=['GET'])
@login_required
def get_user_retweeted_posts(username):
    """
    Fetches all posts that the user has retweeted.
    """
    user = User.query.filter_by(username=username).first()
    
    if user is None:
        return jsonify({'success': False, 'message': f'User {username} not found.'}), 404
    
    retweet_reactions = Reaction.query.filter_by(user_id=user.id, type='RETWEET')\
                                       .order_by(Reaction.timestamp.desc())\
                                       .all()
    
    posts_list = []
    for reaction in retweet_reactions:
        post = Post.query.get(reaction.post_id)
        if not post:
            continue
            
        post_author = User.query.get(post.user_id)
        
        like_count = Reaction.query.filter_by(post_id=post.id, type='LIKE').count()
        retweet_count = Reaction.query.filter_by(post_id=post.id, type='RETWEET').count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        is_liked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='LIKE'
        ).first() is not None
        
        is_retweeted = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='RETWEET'
        ).first() is not None
        
        is_bookmarked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='BOOKMARK'
        ).first() is not None
        
        posts_list.append({
            'id': post.id,
            'username': post_author.username,
            'handle': '@' + post_author.username,
            'content': post.content,
            'time': post.timestamp.strftime('%b %d'),
            'likes': like_count,
            'retweets': retweet_count,
            'comments': comment_count,
            'isLiked': is_liked,
            'isRetweeted': is_retweeted,
            'isBookmarked': is_bookmarked,
        'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
        'canDelete': post.user_id == current_user.id,
        })
    
    return jsonify({
        'success': True,
        'posts': posts_list
    })

@app.route('/api/profile/<username>/commented', methods=['GET'])
@login_required
def get_user_commented_posts(username):
    """
    Fetches all posts that the user has commented on.
    """
    user = User.query.filter_by(username=username).first()
    
    if user is None:
        return jsonify({'success': False, 'message': f'User {username} not found.'}), 404
    
    comments = Comment.query.filter_by(user_id=user.id)\
                            .order_by(Comment.timestamp.desc())\
                            .all()
    
    seen_post_ids = set()
    posts_list = []
    
    for comment in comments:
        if comment.post_id in seen_post_ids:
            continue
        seen_post_ids.add(comment.post_id)
        
        post = Post.query.get(comment.post_id)
        if not post:
            continue
            
        post_author = User.query.get(post.user_id)
        
        like_count = Reaction.query.filter_by(post_id=post.id, type='LIKE').count()
        retweet_count = Reaction.query.filter_by(post_id=post.id, type='RETWEET').count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        is_liked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='LIKE'
        ).first() is not None
        
        is_retweeted = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='RETWEET'
        ).first() is not None
        
        is_bookmarked = Reaction.query.filter_by(
            user_id=current_user.id, 
            post_id=post.id, 
            type='BOOKMARK'
        ).first() is not None
        
        posts_list.append({
            'id': post.id,
            'username': post_author.username,
            'handle': '@' + post_author.username,
            'content': post.content,
            'time': post.timestamp.strftime('%b %d'),
            'likes': like_count,
            'retweets': retweet_count,
            'comments': comment_count,
            'isLiked': is_liked,
            'isRetweeted': is_retweeted,
            'isBookmarked': is_bookmarked,
        'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
        'canDelete': post.user_id == current_user.id,
        })
    
    return jsonify({
        'success': True,
        'posts': posts_list
    })

@app.route('/api/follow', methods=['POST'])
@login_required
def toggle_follow():
    data = request.get_json()
    target_username = data.get('username')
    
    target_user = User.query.filter_by(username=target_username).first()

    if target_user is None:
        return jsonify({'success': False, 'message': 'User not found'}), 404
        
    if target_user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot follow yourself'}), 400

    follow_relationship = Follow.query.filter_by(
        follower_id=current_user.id, 
        followed_id=target_user.id
    ).first()

    if follow_relationship:
        db.session.delete(follow_relationship)
        db.session.commit()
        return jsonify({
            'success': True, 
            'action': 'unfollowed', 
            'message': f'Unfollowed {target_username}'
        })
    else:
        new_follow = Follow(follower_id=current_user.id, followed_id=target_user.id)
        db.session.add(new_follow)
        db.session.commit()
        return jsonify({
            'success': True, 
            'action': 'followed', 
            'message': f'Now following {target_username}'
        })

# app.py

@app.route('/api/follow', methods=['GET'])
@login_required
def get_following():
    """
    Returns a list of users the current user is following.
    This list will be used to populate the 'Start a new message' section.
    """
    
    # current_user.following_relationships should be a backref defined 
    # on your User model via your Follow model. It returns Follow objects.
    following_users = [
        follow.followed 
        for follow in current_user.following_relationships
    ]
    
    following_list = [
        {
            'id': user.id,
            'username': user.username,
            # Add any other data needed (e.g., display name, avatar URL)
        }
        for user in following_users
    ]
    
    return jsonify({'success': True, 'following': following_list})

@app.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """
    Searches for users across the entire database based on a query parameter 'q'.
    This route will resolve the 404 error you are currently seeing.
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': True, 'users': []})

    # Search for users whose username starts with the query (case-insensitive)
    # Filter out the current user to prevent self-messaging via search
    users = User.query.filter(
        User.username.ilike(f'{query}%'),
        User.id != current_user.id
    ).limit(10).all() 

    user_list = [
        {
            'id': user.id,
            'username': user.username,
        }
        for user in users
    ]
    
    return jsonify({'success': True, 'users': user_list})

def serialize_user_relationship(user_obj, current_user_id):
    """
    Helper function to serialize user data for relationship lists.
    Also checks if the current logged-in user follows this user.
    """
    is_following = Follow.query.filter_by(
        follower_id=current_user_id,
        followed_id=user_obj.id
    ).first() is not None
    
    return {
        'username': user_obj.username,
        'user_id': user_obj.id,
        'isFollowing': is_following,
    }

@app.route('/api/relationships/<view_type>/<username>', methods=['GET'])
@login_required
def get_relationships(view_type, username):
    """
    Fetches the list of users that the target user is following or is followed by.
    view_type can be 'following' or 'followers'.
    """
    target_user = User.query.filter_by(username=username).first()
    
    if target_user is None:
        return jsonify({'success': False, 'message': f'User {username} not found.'}), 404
        
    users_list = []

    if view_type == 'following':
        relationships = target_user.following_relationships.all()
        users_list = [r.followed for r in relationships]

    elif view_type == 'followers':
        relationships = target_user.follower_relationships.all()
        users_list = [r.follower for r in relationships]
        
    else:
        return jsonify({'success': False, 'message': 'Invalid relationship view type.'}), 400

    serialized_users = [
        serialize_user_relationship(user, current_user.id) 
        for user in users_list
    ]
    
    return jsonify({
        'success': True,
        'users': serialized_users,
        'current_user': current_user.username 
    })


@app.route('/api/search_user', methods=['GET'])
@login_required
def search_user():
    """
    Searches for a user based on a partial or full username query.
    Expected usage: GET /api/search_user?q=alice
    """
    query = request.args.get('q')
    
    if not query:
        return jsonify({'success': False, 'message': 'Search query cannot be empty.'}), 400

    user = User.query.filter_by(username=query).first()
    
    if user is None:
        # NOTE: Using ilike for case-insensitive search
        #user = User.query.filter(User.username.ilike(f'%{query}%')).first()
        # If you only want exact match (case insensitive):
         user = User.query.filter(User.username.ilike(query)).first()

    if user is None:
        return jsonify({'success': True, 'user': None}) # Return success with no user found

    # 3. Check if the user is the current logged-in user
    if user.id == current_user.id:
        # Optionally hide the current user from search results, or let the frontend handle the 'follow yourself' error
        return jsonify({'success': True, 'user': None})
        
    # 4. Serialize the user data and check follow status
    
    # Check if the current user is following the user found in the search
    is_following = Follow.query.filter_by(
        follower_id=current_user.id,
        followed_id=user.id
    ).first() is not None
    
    user_data = {
        'username': user.username,
        'user_id': user.id,
        # IMPORTANT: The frontend (app.js) uses this flag to set the button text/class
        'isFollowing': is_following,
    }
    
    return jsonify({
        'success': True,
        'user': user_data
    })

@app.route('/api/search', methods=['GET'])
@login_required
def search():
    """
    Universal search endpoint that searches for both users and posts.
    Expected usage: GET /api/search?q=query&type=users OR GET /api/search?q=query&type=chirps
    """
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'users')  # Default to users
    
    if not query:
        return jsonify({'success': False, 'message': 'Search query cannot be empty'}), 400
    
    if search_type == 'users':
        # Search for users by username (case-insensitive partial match)
        users = User.query.filter(
            User.username.ilike(f'%{query}%')
        ).filter(
            User.id != current_user.id  # Exclude current user
        ).limit(20).all()
        
        users_list = []
        for user in users:
            # Check if current user is following this user
            is_following = Follow.query.filter_by(
                follower_id=current_user.id,
                followed_id=user.id
            ).first() is not None
            
            users_list.append({
                'username': user.username,
                'user_id': user.id,
                'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
                'isFollowing': is_following
            })
        
        return jsonify({
            'success': True,
            'results': users_list,
            'type': 'users'
        })
    
    elif search_type == 'chirps':
        # Search for posts by content (case-insensitive partial match)
        posts = Post.query.filter(
            Post.content.ilike(f'%{query}%')
        ).order_by(Post.timestamp.desc()).limit(20).all()
        
        posts_list = []
        for post in posts:
            user = User.query.get(post.user_id)
            
            like_count = Reaction.query.filter_by(post_id=post.id, type='LIKE').count()
            retweet_count = Reaction.query.filter_by(post_id=post.id, type='RETWEET').count()
            comment_count = Comment.query.filter_by(post_id=post.id).count()
            
            is_liked = Reaction.query.filter_by(
                user_id=current_user.id, 
                post_id=post.id, 
                type='LIKE'
            ).first() is not None
            
            is_retweeted = Reaction.query.filter_by(
                user_id=current_user.id, 
                post_id=post.id, 
                type='RETWEET'
            ).first() is not None
            
            is_bookmarked = Reaction.query.filter_by(
                user_id=current_user.id, 
                post_id=post.id, 
                type='BOOKMARK'
            ).first() is not None
            
            posts_list.append({
                'id': post.id,
                'username': user.username,
                'handle': '@' + user.username,
                'content': post.content,
                'time': post.timestamp.strftime('%b %d'),
                'likes': like_count,
                'retweets': retweet_count,
                'comments': comment_count,
                'isLiked': is_liked,
                'isRetweeted': is_retweeted,
                'isBookmarked': is_bookmarked,
                'profile_image': user.profile_image or 'uploads/default-avatar.jpg',
                'canDelete': post.user_id == current_user.id,
            })
        
        return jsonify({
            'success': True,
            'results': posts_list,
            'type': 'chirps'
        })
    
    else:
        return jsonify({'success': False, 'message': 'Invalid search type'}), 400

# app.py (Add this new route)

@app.route('/api/remove_follower', methods=['POST'])
@login_required
def remove_follower():
    """
    Allows the current logged-in user to remove a specific user from their list of followers.
    The current user is the 'followed_id', and the target is the 'follower_id'.
    """
    data = request.get_json()
    follower_username = data.get('follower_username')
    
    # 1. Find the user we want to remove from our followers
    target_follower = User.query.filter_by(username=follower_username).first()

    if target_follower is None:
        return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
    if target_follower.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot remove yourself'}), 400

    # 2. Find the specific Follow relationship
    # The relationship is: target_follower (is the follower_id) follows current_user (is the followed_id)
    follow_relationship = Follow.query.filter_by(
        follower_id=target_follower.id, 
        followed_id=current_user.id 
    ).first()

    if follow_relationship is None:
        # This happens if the user isn't actually following the current user
        return jsonify({'success': False, 'message': f'{follower_username} is not following you.'}), 400

    # 3. Delete the relationship
    db.session.delete(follow_relationship)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Successfully removed {follower_username} as a follower.'
    })

@app.route('/messages', defaults={'partner_username': None})
@app.route('/messages/<partner_username>')
@login_required
def chat_view(partner_username):
    """
    Renders the Direct Messages page.
    If partner_username is provided (e.g., /messages/alice), it tells the Jinja template 
    to load that specific chat history immediately.
    """
    
    # Optional check: ensure the partner exists before loading the template
    if partner_username:
        partner = User.query.filter_by(username=partner_username).first()
        if not partner:
            # If user is not found, redirect to the main inbox
            return redirect(url_for('messages', partner_username=None))
    
    return render_template(
        'messages.html', 
        active_page='messages', 
        partner_username=partner_username # <-- CRITICAL: Pass this to Jinja
    )

@app.route('/api/messages/conversations', methods=['GET'])
@login_required
def get_conversations():
    """
    Fetches a list of users the current user has exchanged messages with (their 'inbox').
    This is complex as it requires finding unique partners and the last message time.
    """
    # Find all unique user IDs the current user has sent or received messages from
    partner_ids_sent = db.session.query(Message.recipient_id).filter(Message.sender_id == current_user.id)
    partner_ids_received = db.session.query(Message.sender_id).filter(Message.recipient_id == current_user.id)
    
    # Combine and get unique partner IDs
    # Note: This is an advanced SQL query equivalent using SQLAlchemy's union
    partner_ids_subquery = partner_ids_sent.union(partner_ids_received).distinct().subquery()
    
    # Select User objects for these partners
    partners = User.query.filter(User.id.in_(partner_ids_subquery)).all()
    
    conversations = []
    
    for partner in partners:
        # Find the last message between current_user and this partner
        last_message = Message.query.filter(
            or_(
                (Message.sender_id == current_user.id) & (Message.recipient_id == partner.id),
                (Message.sender_id == partner.id) & (Message.recipient_id == current_user.id)
            )
        ).order_by(Message.timestamp.desc()).first()
        
        # Count unread messages *from* this partner
        unread_count = Message.query.filter_by(
            sender_id=partner.id, 
            recipient_id=current_user.id, 
            is_read=False
        ).count()

        if last_message:
            conversations.append({
                'partner_username': partner.username,
                'partner_id': partner.id,
                'last_message_content': last_message.content,
                'last_message_time': last_message.timestamp.isoformat(),
                'unread_count': unread_count,
            })

    # Sort conversations by the last message time (newest first)
    conversations.sort(key=lambda x: x['last_message_time'], reverse=True)
    
    return jsonify({'success': True, 'conversations': conversations})

@app.route('/api/messages/<partner_username>', methods=['GET'])
@login_required
def get_messages(partner_username):
    """
    Loads the history of messages between the current user and a specific partner.
    """
    partner = User.query.filter_by(username=partner_username).first()
    
    if not partner:
        return jsonify({'success': False, 'message': 'Partner not found.'}), 404

    # 1. Fetch all messages between the two users
    messages = Message.query.filter(
        or_(
            (Message.sender_id == current_user.id) & (Message.recipient_id == partner.id),
            (Message.sender_id == partner.id) & (Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all() # Load chronologically
    
    # 2. Mark all messages *sent by the partner* to the current user as read
    Message.query.filter_by(
        sender_id=partner.id, 
        recipient_id=current_user.id, 
        is_read=False
    ).update({'is_read': True}, synchronize_session='fetch')
    db.session.commit()
    
    # 3. Serialize messages
    messages_list = [
        {
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read,
            'is_outgoing': msg.sender_id == current_user.id,
            'sender_username': msg.sender.username,
        }
        for msg in messages
    ]
    
    return jsonify({
        'success': True, 
        'messages': messages_list,
        'partner_username': partner.username
    })


@app.route('/api/messages/<partner_username>', methods=['POST'])
@login_required
def send_message(partner_username):
    """
    Sends a new message from the current user to the specified partner.
    """
    partner = User.query.filter_by(username=partner_username).first()
    data = request.get_json()
    content = data.get('content')

    if not partner or not content:
        return jsonify({'success': False, 'message': 'Invalid data or recipient.'}), 400
    
    if current_user.id == partner.id:
        return jsonify({'success': False, 'message': 'Cannot message yourself.'}), 400

    new_message = Message(
        sender_id=current_user.id,
        recipient_id=partner.id,
        content=content,
        is_read=False # Always start as unread
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    # Return the new message data for immediate display on the frontend
    return jsonify({
        'success': True,
        'message_data': {
            'id': new_message.id,
            'content': new_message.content,
            'timestamp': new_message.timestamp.isoformat(),
            'is_read': new_message.is_read,
            'is_outgoing': True,
            'sender_username': current_user.username
        }
    }), 201

if __name__ == '__main__':
    # To run: flask init-db (first time) then flask run
    # For a simple run without the Flask CLI (less ideal for large apps):
    # with app.app_context():
    #     db.create_all() 
    # app.run(debug=True)
    pass