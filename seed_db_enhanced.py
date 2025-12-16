from app import app
from models import db, User, Post, Follow
from datetime import datetime, timedelta
import random

def seed_database():
    with app.app_context():
        print("🌱 Starting enhanced database seeding...")
        
        # 1. Create test users
        users_data = [
            {'username': 'Kabir', 'email': 'Kabir@chirp.com', 'password': 'password'},
            {'username': 'Aditya', 'email': 'Aditya@chirp.com', 'password': 'password'},
            {'username': 'Testuser', 'email': 'Testuser@chirp.com', 'password': 'password'},
        ]
        
        created_users = {}
        
        print("\n👤 Creating users...")
        for user_data in users_data:
            # Check if user already exists
            existing_user = User.query.filter_by(username=user_data['username']).first()
            
            if existing_user:
                print(f"   ⚠️  User '{user_data['username']}' already exists. Skipping...")
                created_users[user_data['username']] = existing_user
            else:
                # Create new user
                new_user = User(
                    username=user_data['username'],
                    email=user_data['email']
                )
                new_user.set_password(user_data['password'])
                
                db.session.add(new_user)
                db.session.flush()  # Get the user ID without committing
                
                created_users[user_data['username']] = new_user
                print(f"   ✅ Created user: {user_data['username']}")
        
        # Commit users to database
        db.session.commit()
        
        # 2. Create test chirps with timestamps spread over last few days
        print("\n📝 Creating chirps...")
        chirps_data = [
            {'username': 'Kabir', 'content': 'Yo broncos are 11-2', 'days_ago': 0},
            {'username': 'Aditya', 'content': 'mbappe is the goat', 'days_ago': 0},
            {'username': 'Kabir', 'content': 'This team is on fire! 🔥', 'days_ago': 1},
            {'username': 'Aditya', 'content': 'Real Madrid vs Barcelona tomorrow, who you got?', 'days_ago': 1},
            {'username': 'Testuser', 'content': 'Just joined Chirp! This is awesome', 'days_ago': 10},
            {'username': 'Kabir', 'content': 'Game day vibes! Let\'s go!', 'days_ago': 2},
            {'username': 'Aditya', 'content': 'That goal was insane!!! 🤯', 'days_ago': 3},
        ]
        
        for chirp_data in chirps_data:
            user = created_users.get(chirp_data['username'])
            
            if user:
                timestamp = datetime.utcnow() - timedelta(days=chirp_data['days_ago'])
                
                new_post = Post(
                    user_id=user.id,
                    content=chirp_data['content'],
                    timestamp=timestamp
                )
                
                db.session.add(new_post)
                print(f"   ✅ Created chirp by {chirp_data['username']}: \"{chirp_data['content'][:40]}...\"")
            else:
                print(f"   ❌ User '{chirp_data['username']}' not found. Cannot create chirp.")
        
        # Commit chirps to database
        db.session.commit()
        
        # 3. Create follow relationships
        print("\n👥 Creating follow relationships...")
        follow_relationships = [
            {'follower': 'Testuser', 'followed': 'Kabir'},
            {'follower': 'Testuser', 'followed': 'Aditya'},
            {'follower': 'Kabir', 'followed': 'Aditya'},
            {'follower': 'Aditya', 'followed': 'Kabir'},
        ]
        
        for rel in follow_relationships:
            follower = created_users.get(rel['follower'])
            followed = created_users.get(rel['followed'])
            
            if follower and followed:
                # Check if relationship already exists
                existing_follow = Follow.query.filter_by(
                    follower_id=follower.id,
                    followed_id=followed.id
                ).first()
                
                if not existing_follow:
                    new_follow = Follow(
                        follower_id=follower.id,
                        followed_id=followed.id,
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(new_follow)
                    print(f"   ✅ {rel['follower']} now follows {rel['followed']}")
                else:
                    print(f"   ⚠️  {rel['follower']} already follows {rel['followed']}")
        
        # Commit follows to database
        db.session.commit()
        
        print("\n🎉 Database seeding completed successfully!")
        print("\n📊 Summary:")
        print(f"   Users: {len(created_users)}")
        print(f"   Chirps: {len(chirps_data)}")
        print(f"   Follow relationships: {len(follow_relationships)}")
        
        print("\n🔐 Login credentials (all use password: 'password'):")
        for username in created_users.keys():
            follower_count = Follow.query.filter_by(followed_id=created_users[username].id).count()
            following_count = Follow.query.filter_by(follower_id=created_users[username].id).count()
            post_count = Post.query.filter_by(user_id=created_users[username].id).count()
            
            print(f"   • {username:12} | {post_count} chirps | {following_count} following | {follower_count} followers")
        
        print("\n💡 Test scenarios:")
        print("   1. Login as 'Testuser' to see Kabir and Aditya's chirps (follower-only timeline)")
        print("   2. Login as 'Kabir' to see Aditya's chirps")
        print("   3. Login as 'Aditya' to see Kabir's chirps")
        print("   4. Try commenting on chirps!")
        print("   5. Try bookmarking chirps and view them in Bookmarks page")

if __name__ == '__main__':
    try:
        seed_database()
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()