// --- Constants and Utility Functions ---
const LOGIN_FORM_ID = 'login-form';
const NEW_CHIRP_FORM_ID = 'new-chirp-form';
const TIMELINE_ID = 'timeline';
const SIGNUP_FORM_ID = 'signup-form';
const PROFILE_DETAILS_CONTAINER_ID = 'profile-details-container'; 
const PROFILE_POSTS_CONTAINER_ID = 'profile-posts-container';     
const PROFILE_HEADER_ID = 'profile-header';                      
const PROFILE_POST_COUNT_ID = 'profile-post-count';               
const BOOKMARKS_CONTAINER_ID = 'bookmarks-container';

/**
 * Creates and returns the inner HTML for a post's action buttons.
 * This function is used by createPostElement and when updating a post's reactions.
 */
function createPostActionsHTML(postData) {
    const comments = postData.comments || 0;
    
    const isLiked = postData.isLiked;
    const isRetweeted = postData.isRetweeted;
    const isBookmarked = postData.isBookmarked;
    
    const likeIconClass = isLiked ? 'fas fa-heart' : 'far fa-heart';
    
    const retweetIconClass = 'fas fa-retweet'; 
    
    const bookmarkIconClass = isBookmarked ? 'fas fa-bookmark' : 'far fa-bookmark'; 

    return `
        <div class="post-actions">
            <div class="action-button comment ${comments > 0 ? 'has-comments' : ''}" data-reaction-type="COMMENT" title="Comment">
                <i class="far fa-comment fa-lg"></i><span>${comments > 0 ? comments : ''}</span>
            </div>
            
            <div class="action-button like ${isLiked ? 'active active-LIKE' : ''}" data-reaction-type="LIKE" title="Like">
                <i class="${likeIconClass} fa-lg"></i><span>${postData.likes > 0 ? postData.likes : ''}</span>
            </div>
            
            <div class="action-button retweet ${isRetweeted ? 'active active-RETWEET' : ''}" data-reaction-type="RETWEET" title="Retweet">
                <i class="${retweetIconClass} fa-lg"></i><span>${postData.retweets > 0 ? postData.retweets : ''}</span>
            </div>
            
            <div class="action-button bookmark ${isBookmarked ? 'active active-BOOKMARK' : ''}" data-reaction-type="BOOKMARK" title="Bookmark">
                <i class="${bookmarkIconClass} fa-lg"></i><span></span>
            </div>
        </div>
    `;
}

// --- Login Handler ---
async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const username = form.elements.username.value;
    const password = form.elements.password.value;

    console.log(`Attempting login for: ${username}`);
    
    try {
        const response = await fetch('/api/login', { 
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({ username, password }) 
        });

        const data = await response.json();

        if (response.ok && data.success) {
            console.log('Login successful.');
            window.location.href = data.redirect; 
        } else {
            alert(`Login failed: ${data.message || 'Invalid credentials'}`);
        }
    } catch (error) {
        console.error('Network or server error during login:', error);
        alert('Could not connect to the server. Please try again.');
    }
}

async function handleSignup(event) {
    event.preventDefault(); 

    const username = document.getElementById('signup-username').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;
    const messageElement = document.getElementById('signup-message');

    messageElement.textContent = ''; 

    if (password !== confirmPassword) {
        messageElement.textContent = 'Error: Passwords do not match.';
        return;
    }
    
    if (password.length < 6) {
        messageElement.textContent = 'Error: Password must be at least 6 characters long.';
        return;
    }

    try {
        const response = await fetch('/api/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = data.redirect;
        } else {
            messageElement.textContent = `Signup Failed: ${data.message}`;
        }
    } catch (error) {
        console.error('Signup fetch error:', error);
        messageElement.textContent = 'An unexpected error occurred. Please try again.';
    }
}

async function handleNewChirp(event) {
    event.preventDefault();
    const form = event.target;
    const content = form.elements.content.value.trim();

    if (!content) {
        alert('Chirp content cannot be empty.');
        return;
    }

    try {
        const response = await fetch('/api/posts', { 
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content }) 
        });

        const data = await response.json();

        if (response.ok && data.success) {
            const postData = data.post;
            
            postData.isLiked = false;
            postData.isRetweeted = false;
            postData.isBookmarked = false;
            postData.comments = 0;
            
            const postElement = createPostElement(postData);
            const timeline = document.getElementById(TIMELINE_ID);
            
            if (timeline) {
                timeline.prepend(postElement); 
            }
            
            form.elements.content.value = '';
        } else {
            alert(`Error posting chirp: ${data.message || 'Server error'}`);
        }
    } catch (error) {
        console.error('Error posting chirp:', error);
        alert('Network error while posting chirp.');
    }
}

async function handleReaction(event) {
    const actionButton = event.currentTarget;
    const postElement = actionButton.closest('.post');
    const postId = postElement.dataset.postId;
    const reactionType = actionButton.dataset.reactionType;
    
    const iconElement = actionButton.querySelector('i');
    let countElement = actionButton.querySelector('span');

    const activeClass = `active-${reactionType}`;
    
    if (reactionType === 'COMMENT') {
        showCommentModal(postId);
        return;
    }
    
    console.log(`Attempting Reaction: ${reactionType} on Post ID: ${postId}`);

    try {
        const response = await fetch('/api/react', { 
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ postId, reactionType }) 
        });
        
        const data = await response.json();

        if (response.ok && data.success) {
            const newCount = data.newCount;

            if (data.toggled) {
                actionButton.classList.add('active', activeClass);
                
                if (iconElement) {
                    iconElement.classList.remove('far');
                    iconElement.classList.add('fas');
                }
                
            } else {
                actionButton.classList.remove('active', activeClass);
                
                if (iconElement && reactionType !== 'RETWEET') {
                    iconElement.classList.remove('fas');
                    iconElement.classList.add('far');
                }
            }
            
            countElement.textContent = newCount > 0 ? newCount : '';

            if (reactionType === 'BOOKMARK' && window.location.pathname.startsWith('/bookmarks') && !data.toggled) {
                 postElement.remove(); 
            }

        } else {
            alert(`Error processing reaction: ${data.message || 'Server error'}`);
        }
    } catch (error) {
        console.error('Error handling reaction:', error);
        alert('Network error while reacting to post.');
    }
}

// --- Delete Post Handler ---
async function handleDeletePost(event) {
    event.stopPropagation(); 
    
    const deleteBtn = event.currentTarget;
    const postElement = deleteBtn.closest('.post');
    const postId = deleteBtn.dataset.postId;
    
    if (!confirm('Are you sure you want to delete this chirp? This will also delete all comments and reactions.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/posts/${postId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            postElement.remove();
            console.log('Post deleted successfully');
        } else {
            alert(`Error deleting chirp: ${data.message || 'Server error'}`);
        }
    } catch (error) {
        console.error('Error deleting post:', error);
        alert('Network error while deleting chirp.');
    }
}

// --- Dynamic Post Generation Utility ---
function createPostElement(postData) {
    const postDiv = document.createElement('div');
    postDiv.className = 'post';
    postDiv.dataset.postId = postData.id;

    let profileImageUrl = '/static/uploads/default-avatar.jpg';
    if (postData.profile_image && postData.profile_image.trim() !== '') {
        if (postData.profile_image.startsWith('static/')) {
            profileImageUrl = `/${postData.profile_image}`;
        } else {
            profileImageUrl = `/static/${postData.profile_image}`;
        }
    }
    
    console.log('Post data:', postData);
    console.log('Profile image URL:', profileImageUrl);

    postDiv.innerHTML = `
        <div class="post-container">
            <div class="post-avatar clickable-avatar" data-username="${postData.username}">
                <img src="${profileImageUrl}" alt="${postData.username}" class="profile-pic" onerror="this.src='/static/uploads/default-avatar.jpg'">
            </div>
            <div class="post-main">
                <div class="post-header">
                    <span class="username clickable-username" data-username="${postData.username}">${postData.username}</span>
                    <span class="handle">${postData.handle}</span>
                    <span class="handle time">· ${postData.time}</span>
                    ${postData.canDelete ? `
                        <button class="delete-post-btn" data-post-id="${postData.id}" title="Delete chirp">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
                <div class="post-content">
                    ${postData.content}
                </div>
                ${createPostActionsHTML(postData)}
            </div>
        </div>
    `;
    
    postDiv.querySelectorAll('.action-button').forEach(button => {
        button.addEventListener('click', handleReaction);
    });
    
    const deleteBtn = postDiv.querySelector('.delete-post-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', handleDeletePost);
    }
    
    const avatar = postDiv.querySelector('.clickable-avatar');
    const username = postDiv.querySelector('.clickable-username');
    
    if (avatar) {
        avatar.addEventListener('click', (e) => {
            e.stopPropagation(); 
            window.location.href = `/profile/${postData.username}`;
        });
    }
    
    if (username) {
        username.addEventListener('click', (e) => {
            e.stopPropagation(); 
            window.location.href = `/profile/${postData.username}`;
        });
    }

    return postDiv;
}

// --- Comment Modal Functions ---
let commentModalInitialized = false; 

function setupCommentModal() {
    if (commentModalInitialized) return; 
    
    const modal = document.getElementById('comment-modal');
    if (!modal) return; 
    
    commentModalInitialized = true; 
    
    const closeBtn = modal.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };
    }
    
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
    
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', submitComment);
    }
}

function showCommentModal(postId) {
    const modal = document.getElementById('comment-modal');
    if (!modal) return;
    
    modal.style.display = 'block';
    modal.dataset.postId = postId;
    
    loadComments(postId);
}

async function loadComments(postId) {
    try {
        const response = await fetch(`/api/posts/${postId}/comments`);
        const data = await response.json();
        
        const commentsList = document.getElementById('comments-list');
        if (!commentsList) return;
        
        if (data.success && data.comments.length > 0) {
            commentsList.innerHTML = data.comments.map(comment => `
                <div class="comment" data-comment-id="${comment.id}">
                    <div class="comment-header">
                        <a href="/profile/${comment.username}">
                            <strong>${comment.username}</strong>
                        </a>
                        <span class="handle">${comment.handle}</span>
                        <span class="time">${comment.time}</span>
                        ${comment.canDelete ? `
                            <button class="delete-comment-btn" data-comment-id="${comment.id}">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                    <div class="comment-content">${comment.content}</div>
                </div>
            `).join('');
            
            attachDeleteCommentListeners();
        } else {
            commentsList.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">No comments yet. Be the first to comment!</p>';
        }
    } catch (error) {
        console.error('Error loading comments:', error);
    }
}

async function submitComment(event) {
    event.preventDefault();
    
    const modal = document.getElementById('comment-modal');
    if (!modal) return;
    
    const postId = modal.dataset.postId;
    const contentInput = document.getElementById('comment-input');
    if (!contentInput) return;
    
    const content = contentInput.value.trim();
    
    if (!content) return;
    
    try {
        const response = await fetch(`/api/posts/${postId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            contentInput.value = '';
            loadComments(postId);
            updateCommentCount(postId, data.newCommentCount);
        }
    } catch (error) {
        console.error('Error submitting comment:', error);
    }
}

function attachDeleteCommentListeners() {
    document.querySelectorAll('.delete-comment-btn').forEach(button => {
        button.addEventListener('click', async function() {
            const commentId = this.dataset.commentId;
            const modal = document.getElementById('comment-modal');
            if (!modal) return;
            
            const postId = modal.dataset.postId;
            
            if (confirm('Delete this comment?')) {
                try {
                    const response = await fetch(`/api/comments/${commentId}`, {
                        method: 'DELETE'
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        loadComments(postId);
                        updateCommentCount(postId, data.newCommentCount);
                    }
                } catch (error) {
                    console.error('Error deleting comment:', error);
                }
            }
        });
    });
}

function updateCommentCount(postId, count) {
    const post = document.querySelector(`[data-post-id="${postId}"]`);
    if (post) {
        const commentBtn = post.querySelector('.action-button.comment');
        if (commentBtn) {
            const countSpan = commentBtn.querySelector('span');
            if (countSpan) {
                countSpan.textContent = count > 0 ? count : '';
            }
            if (count > 0) {
                commentBtn.classList.add('has-comments');
            } else {
                commentBtn.classList.remove('has-comments');
            }
        }
    }
}

// --- Chirp Modal Functions ---
let chirpModalInitialized = false; 

function setupChirpModal() {
    if (chirpModalInitialized) return; 
    
    const modal = document.getElementById('chirp-modal');
    if (!modal) return; 
    
    chirpModalInitialized = true; 
    
    const openBtn = document.getElementById('chirp-modal-btn');
    const closeBtn = modal.querySelector('.close');
    const form = document.getElementById('chirp-modal-form');
    
    if (openBtn) {
        openBtn.addEventListener('click', function() {
            modal.style.display = 'block';
            const textarea = document.getElementById('chirp-modal-input');
            if (textarea) {
                setTimeout(() => textarea.focus(), 100);
            }
        });
    }
    
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
            const textarea = document.getElementById('chirp-modal-input');
            if (textarea) textarea.value = '';
        };
    }
    
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
            const textarea = document.getElementById('chirp-modal-input');
            if (textarea) textarea.value = '';
        }
    });
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const textarea = document.getElementById('chirp-modal-input');
            const content = textarea.value.trim();
            
            if (!content) {
                alert('Chirp content cannot be empty.');
                return;
            }
            
            try {
                const response = await fetch('/api/posts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    textarea.value = '';
                    
                    modal.style.display = 'none';
                    
                    alert('Chirp posted successfully!');
                    
                    const timeline = document.getElementById('timeline');
                    if (timeline) {
                        loadTimeline();
                    }
                } else {
                    alert('Error posting chirp: ' + (data.message || 'Server error'));
                }
            } catch (error) {
                console.error('Error posting chirp:', error);
                alert('Network error while posting chirp.');
            }
        });
    }
}

// --- Timeline Page Functions ---
async function loadTimeline() {
    const timeline = document.getElementById(TIMELINE_ID);
    if (!timeline) return;
    
    try {
        const response = await fetch('/api/posts');
        const data = await response.json();
        
        if (data.success && data.posts.length > 0) {
            timeline.innerHTML = '';
            data.posts.forEach(postData => {
                const postElement = createPostElement(postData);
                timeline.appendChild(postElement);
            });
        } else {
            timeline.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">No chirps to show. Follow users to see their chirps!</p>';
        }
    } catch (error) {
        console.error('Error loading timeline:', error);
        timeline.innerHTML = '<p style="padding: 20px; text-align: center; color: red;">Error loading timeline.</p>';
    }
}

// --- Bookmarks Page Functions ---
async function loadBookmarks() {
    const container = document.getElementById(BOOKMARKS_CONTAINER_ID);
    if (!container) return;
    
    try {
        const response = await fetch('/api/bookmarks');
        const data = await response.json();
        
        if (data.success && data.posts.length > 0) {
            container.innerHTML = '';
            data.posts.forEach(postData => {
                const postElement = createPostElement(postData);
                container.appendChild(postElement);
            });
        } else {
            container.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">No bookmarks yet. Start bookmarking chirps!</p>';
        }
    } catch (error) {
        console.error('Error loading bookmarks:', error);
        container.innerHTML = '<p style="padding: 20px; text-align: center; color: red;">Error loading bookmarks.</p>';
    }
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    
    const loginForm = document.getElementById(LOGIN_FORM_ID);
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const signupForm = document.getElementById(SIGNUP_FORM_ID);
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }

    const newChirpForm = document.getElementById(NEW_CHIRP_FORM_ID);
    if (newChirpForm) {
        newChirpForm.addEventListener('submit', handleNewChirp);
    }
    
    const timeline = document.getElementById(TIMELINE_ID);
    if (timeline) {
        loadTimeline();
    }
    
    const bookmarksContainer = document.getElementById(BOOKMARKS_CONTAINER_ID);
    if (bookmarksContainer) {
        loadBookmarks();
    }

    const profileHeader = document.getElementById(PROFILE_HEADER_ID);
    if (profileHeader) {
        const targetUsername = profileHeader.querySelector('h2')?.textContent || null;
        if (targetUsername) {
            loadProfile(targetUsername);
        }
    }
    
    const relationshipsContainer = document.getElementById('relationships-list-container');
    if (relationshipsContainer) {
        loadRelationships();
    }
    
    const searchForm = document.getElementById('user-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleUserRelationshipSearch);
    }
    
    setupCommentModal();
    
    setupChirpModal();
});

/* --- PROFILE PAGE LOGIC --- */

let currentProfileUsername = null;

async function loadProfile(username) {
    currentProfileUsername = username; 
    
    const profileDetailsContainer = document.getElementById(PROFILE_DETAILS_CONTAINER_ID);
    const profilePostsContainer = document.getElementById(PROFILE_POSTS_CONTAINER_ID);
    const profileHeaderElement = document.getElementById(PROFILE_HEADER_ID);
    const profilePostCountElement = document.getElementById(PROFILE_POST_COUNT_ID);

    if (!profileDetailsContainer || !profilePostsContainer || !profileHeaderElement) {
        console.log('Profile containers not found in the DOM.');
        return;
    }

    profileDetailsContainer.innerHTML = '<p style="padding: 20px; text-align: center;">Loading profile...</p>';
    profilePostsContainer.innerHTML = '';

    try {
        const response = await fetch(`/api/profile/${username}`);
        const data = await response.json();

        if (!response.ok || !data.success) {
            profileHeaderElement.innerHTML = '<h2>Not Found</h2><p>User not found.</p>';
            profileDetailsContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: red;">This user does not exist.</p>';
            return;
        }

        const profile = data.profile;
        const isOwnProfile = profile.isOwnProfile;

        const followButtonHTML = isOwnProfile
            ? '' 
            : profile.isFollowing
                ? `<button class="secondary-button" id="follow-btn">Following</button>`
                : `<button class="primary-button" id="follow-btn">Follow</button>`;

        const bannerClass = isOwnProfile ? 'profile-banner clickable' : 'profile-banner';
        const avatarClass = isOwnProfile ? 'profile-avatar clickable' : 'profile-avatar';
        const bannerStyle = profile.bannerImage ? `background-image: url('${profile.bannerImage}'); background-size: cover; background-position: center;` : '';
        const avatarStyle = profile.profileImage 
            ? `background-image: url('${profile.profileImage}'); background-size: cover; background-position: center;` 
            : `background-image: url('/static/uploads/default-avatar.jpg'); background-size: cover; background-position: center;`;

        profileDetailsContainer.innerHTML = `
            <div class="profile-box">
                <div class="${bannerClass}" id="profile-banner" style="${bannerStyle}">
                    ${isOwnProfile ? '<div class="upload-overlay"><i class="fa-solid fa-camera"></i></div>' : ''}
                </div>
                <div class="${avatarClass}" id="profile-avatar" style="${avatarStyle}">
                    ${isOwnProfile ? '<div class="upload-overlay"><i class="fa-solid fa-camera"></i></div>' : ''}
                </div>
                <input type="file" id="banner-upload" accept="image/*" style="display: none;">
                <input type="file" id="avatar-upload" accept="image/*" style="display: none;">
                <div class="profile-info">
                    <h3>${profile.username}</h3>
                    <div style="color: var(--text-color-secondary); font-size: 15px; margin-top: 2px;">
                        ${profile.handle} · Joined ${profile.joinedDate || 'Unknown'}
                    </div>
                    <div class="profile-stats">
                        <a href="/relationships/following/${username}" class="stat-link">
                            <strong>${profile.followingCount}</strong> Following
                        </a>
                        <a href="/relationships/followers/${username}" class="stat-link">
                            <strong>${profile.followerCount}</strong> Followers
                        </a>
                    </div>
                    ${followButtonHTML}
                </div>
            </div>
        `;
        
        if (!isOwnProfile) {
            const followBtn = document.getElementById('follow-btn');
            if (followBtn) {
                followBtn.addEventListener('click', async () => {
                    try {
                        const response = await fetch('/api/follow', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username: profile.username })
                        });
                        const data = await response.json();
                        
                        if (data.success) {
                            if (data.action === 'followed') {
                                followBtn.textContent = 'Following';
                                followBtn.classList.remove('primary-button');
                                followBtn.classList.add('secondary-button');
                            } else {
                                followBtn.textContent = 'Follow';
                                followBtn.classList.remove('secondary-button');
                                followBtn.classList.add('primary-button');
                            }
                        }
                    } catch (error) {
                        console.error('Error toggling follow:', error);
                    }
                });
            }
        } else {
            setupProfileImageUpload();
        }

        const totalLikesElement = document.getElementById('total-likes');
        const totalRetweetsElement = document.getElementById('total-retweets');
        const totalCommentsElement = document.getElementById('total-comments');
        
        if (totalLikesElement) totalLikesElement.textContent = profile.totalLikes || 0;
        if (totalRetweetsElement) totalRetweetsElement.textContent = profile.totalRetweets || 0;
        if (totalCommentsElement) totalCommentsElement.textContent = profile.totalComments || 0;

        const posts = data.posts;
        if (posts.length === 0) {
            profilePostsContainer.innerHTML = '<p style="padding: 20px; text-align: center;">This user has not posted anything yet.</p>';
        } else {
            profilePostCountElement.textContent = `${posts.length} Chirp${posts.length === 1 ? '' : 's'}`;
            posts.forEach(postData => {
                const postElement = createPostElement(postData);
                profilePostsContainer.appendChild(postElement);
            });
        }

    } catch (error) {
        console.error('Error loading profile:', error);
        profileHeaderElement.innerHTML = '<h2>Network Error</h2><p>Could not load profile.</p>';
    }
    
    setupProfileTabs(username);
}

function setupProfileTabs(username) {
    const tabs = document.querySelectorAll('.profile-tabs .tab-item');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', async (e) => {
            e.preventDefault();
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const tabType = tab.dataset.tab;
            
            await loadProfilePosts(username, tabType);
        });
    });
}

// Load posts based on tab type
async function loadProfilePosts(username, tabType) {
    const profilePostsContainer = document.getElementById(PROFILE_POSTS_CONTAINER_ID);
    const profilePostCountElement = document.getElementById(PROFILE_POST_COUNT_ID);
    
    if (!profilePostsContainer) return;
    
    profilePostsContainer.innerHTML = '<p style="padding: 20px; text-align: center;">Loading...</p>';
    
    try {
        let endpoint = '';
        let tabLabel = '';
        
        switch(tabType) {
            case 'chirps':
                endpoint = `/api/profile/${username}`;
                tabLabel = 'Chirp';
                break;
            case 'liked':
                endpoint = `/api/profile/${username}/liked`;
                tabLabel = 'Liked chirp';
                break;
            case 'retweeted':
                endpoint = `/api/profile/${username}/retweeted`;
                tabLabel = 'Retweeted chirp';
                break;
            case 'commented':
                endpoint = `/api/profile/${username}/commented`;
                tabLabel = 'Commented chirp';
                break;
            default:
                endpoint = `/api/profile/${username}`;
                tabLabel = 'Chirp';
        }
        
        const response = await fetch(endpoint);
        const data = await response.json();
        
        if (!data.success) {
            profilePostsContainer.innerHTML = `<p style="padding: 20px; text-align: center; color: red;">Error loading posts.</p>`;
            return;
        }
        
        const posts = tabType === 'chirps' ? data.posts : data.posts;
        
        if (posts.length === 0) {
            let emptyMessage = '';
            switch(tabType) {
                case 'chirps':
                    emptyMessage = 'This user has not posted anything yet.';
                    break;
                case 'liked':
                    emptyMessage = `${username} hasn't liked any chirps yet.`;
                    break;
                case 'retweeted':
                    emptyMessage = `${username} hasn't retweeted any chirps yet.`;
                    break;
                case 'commented':
                    emptyMessage = `${username} hasn't commented on any chirps yet.`;
                    break;
            }
            profilePostsContainer.innerHTML = `<p style="padding: 20px; text-align: center;">${emptyMessage}</p>`;
            if (profilePostCountElement) {
                profilePostCountElement.textContent = '';
            }
        } else {
            profilePostsContainer.innerHTML = '';
            if (profilePostCountElement) {
                profilePostCountElement.textContent = `${posts.length} ${tabLabel}${posts.length === 1 ? '' : 's'}`;
            }
            posts.forEach(postData => {
                const postElement = createPostElement(postData);
                profilePostsContainer.appendChild(postElement);
            });
        }
        
    } catch (error) {
        console.error('Error loading profile posts:', error);
        profilePostsContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: red;">Error loading posts.</p>';
    }
}

// --- Profile Image Upload Functions ---
function setupProfileImageUpload() {
    const bannerElement = document.getElementById('profile-banner');
    const avatarElement = document.getElementById('profile-avatar');
    const bannerInput = document.getElementById('banner-upload');
    const avatarInput = document.getElementById('avatar-upload');
    
    if (!bannerElement || !avatarElement || !bannerInput || !avatarInput) return;
    
    bannerElement.addEventListener('click', () => {
        bannerInput.click();
    });
    
    avatarElement.addEventListener('click', () => {
        avatarInput.click();
    });
    
    bannerInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        await uploadImage(file, 'banner', bannerElement);
    });
    
    avatarInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        await uploadImage(file, 'avatar', avatarElement);
    });
}

async function uploadImage(file, type, element) {
    if (file.size > 5 * 1024 * 1024) {
        alert('File is too large. Maximum size is 5MB.');
        return;
    }
    
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        alert('Invalid file type. Please upload a PNG, JPG, GIF, or WebP image.');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const endpoint = type === 'banner' ? '/api/upload/banner-image' : '/api/upload/profile-image';
    
    try {
        element.style.opacity = '0.5';
        
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            element.style.backgroundImage = `url('${data.image_url}')`;
            element.style.backgroundSize = 'cover';
            element.style.backgroundPosition = 'center';
            element.style.opacity = '1';
            
            alert(`${type === 'banner' ? 'Banner' : 'Profile'} image updated successfully!`);
        } else {
            alert('Error uploading image: ' + data.message);
            element.style.opacity = '1';
        }
    } catch (error) {
        console.error('Error uploading image:', error);
        alert('Network error while uploading image.');
        element.style.opacity = '1';
    }
}

/* --- RELATIONSHIPS (FOLLOW/FOLLOWERS) LOGIC --- */

function createUserElement(userData, viewType, canRemove) {
    const userDiv = document.createElement('div');
    userDiv.className = 'relationship-item';
    userDiv.dataset.username = userData.username;

    let buttonHTML = '';
    if (viewType === 'following' && canRemove) {
        const buttonText = userData.isFollowing ? 'Unfollow' : 'Follow';
        const buttonClass = userData.isFollowing ? 'secondary-button' : 'primary-button';
        buttonHTML = `<button class="${buttonClass} relationship-toggle-btn" data-username="${userData.username}">${buttonText}</button>`;
    } 
    else if (viewType === 'followers' && canRemove) {
        buttonHTML = `<button class="secondary-button relationship-remove-btn" data-username="${userData.username}">Remove</button>`;
    }

    const profileImageUrl = userData.profile_image 
        ? `/static/${userData.profile_image}` 
        : '/static/uploads/default-avatar.jpg';
    
    userDiv.innerHTML = `
        <div class="user-info">
            <div class="profile-avatar-small clickable-avatar" data-username="${userData.username}" style="background-image: url('${profileImageUrl}'); background-size: cover; background-position: center;"></div>
            <div>
                <strong class="clickable-username" data-username="${userData.username}">${userData.username}</strong>
                <p class="handle">@${userData.username}</p>
            </div>
        </div>
        ${buttonHTML}
    `;
    
    const toggleBtn = userDiv.querySelector('.relationship-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', handleFollowToggle);
    }
    const removeBtn = userDiv.querySelector('.relationship-remove-btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', handleFollowerRemoval);
    }
    
    const avatar = userDiv.querySelector('.clickable-avatar');
    const username = userDiv.querySelector('.clickable-username');
    
    if (avatar) {
        avatar.addEventListener('click', (e) => {
            e.stopPropagation();
            window.location.href = `/profile/${userData.username}`;
        });
    }
    
    if (username) {
        username.addEventListener('click', (e) => {
            e.stopPropagation();
            window.location.href = `/profile/${userData.username}`;
        });
    }

    return userDiv;
}

/**
 * Loads the list of following or followers for the target user.
 */
async function loadRelationships() {
    const pathParts = window.location.pathname.split('/');
    const viewType = pathParts[2]; 
    const targetUsername = pathParts[3];
    const listContainer = document.getElementById('relationships-list-container');
    
    if (!listContainer) return;
    listContainer.innerHTML = '<p style="padding: 20px; text-align: center;">Loading list...</p>';

    try {
        const response = await fetch(`/api/relationships/${viewType}/${targetUsername}`);
        const data = await response.json();

        listContainer.innerHTML = '';
        
        if (!data.success) {
            listContainer.innerHTML = `<p style="padding: 20px; text-align: center; color: red;">Error: ${data.message}</p>`;
            return;
        }
        
        const usersList = data.users;
        const currentUsername = data.current_user; 
        
        if (usersList.length === 0) {
             listContainer.innerHTML = `<p style="padding: 20px; text-align: center;">${targetUsername} has no ${viewType} yet.</p>`;
             return;
        }

        window.relationshipsData = {
            users: usersList,
            viewType: viewType,
            currentUsername: currentUsername,
            targetUsername: targetUsername
        };

        displayRelationships(usersList, viewType, currentUsername, targetUsername);

        if (viewType === 'followers') {
            setupFollowersSearch();
        }

    } catch (error) {
        console.error('Error loading relationships:', error);
        listContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: red;">Network error loading list.</p>';
    }
}

/**
 * Displays the relationships list (separated for search filtering)
 */
function displayRelationships(usersList, viewType, currentUsername, targetUsername) {
    const listContainer = document.getElementById('relationships-list-container');
    if (!listContainer) return;
    
    listContainer.innerHTML = '';
    
    if (usersList.length === 0) {
        listContainer.innerHTML = `<p style="padding: 20px; text-align: center;">No ${viewType} found matching your search.</p>`;
        return;
    }

    usersList.forEach(user => {
        const canRemove = (targetUsername === currentUsername);
        listContainer.appendChild(createUserElement(user, viewType, canRemove));
    });
}

/**
 * Setup search functionality for followers page
 */
function setupFollowersSearch() {
    const searchInput = document.getElementById('followers-search-input');
    const searchButton = document.getElementById('followers-search-btn');
    
    if (!searchInput || !searchButton) return;
    
    const performSearch = () => {
        const query = searchInput.value.trim().toLowerCase();
        
        if (!window.relationshipsData) return;
        
        const { users, viewType, currentUsername, targetUsername } = window.relationshipsData;
        
        const filteredUsers = users.filter(user => 
            user.username.toLowerCase().includes(query)
        );
        
        displayRelationships(filteredUsers, viewType, currentUsername, targetUsername);
    };
    
    searchButton.addEventListener('click', performSearch);
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
    
    searchInput.addEventListener('input', performSearch);
}

/**
 * Handles the 'Follow' or 'Unfollow' action (only used on the 'Following' list).
 */
async function handleFollowToggle(event) {
    event.preventDefault();
    const button = event.target;
    const targetUsername = button.dataset.username;
    
    try {
        const response = await fetch('/api/follow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: targetUsername })
        });

        const data = await response.json();

        if (data.success) {
            if (data.action === 'followed') {
                button.textContent = 'Unfollow';
                button.classList.remove('primary-button');
                button.classList.add('secondary-button');
            } else {
                const item = button.closest('.relationship-item');
                if (item) item.remove();
            }
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Error toggling follow:', error);
        alert('Network error. Could not toggle follow status.');
    }
}

/**
 * Handles the 'Remove' action (only used on the 'Followers' list).
 */
async function handleFollowerRemoval(event) {
    event.preventDefault();
    const button = event.target;
    const targetUsername = button.dataset.username;
    
    if (!confirm(`Are you sure you want to remove @${targetUsername} as a follower? This is permanent.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/remove_follower', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ follower_username: targetUsername })
        });

        const data = await response.json();

        if (data.success) {
            const item = button.closest('.relationship-item');
            if (item) item.remove();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Error removing follower:', error);
        alert('Network error. Could not remove follower.');
    }
}


/**
 * Handles the search for a new user to follow (only runs on the 'Following' view).
 */
async function handleUserRelationshipSearch(event) {
    event.preventDefault();
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    const resultsContainer = document.getElementById('search-results-container');
    
    if (!query) return;

    resultsContainer.innerHTML = '<p class="search-message">Searching...</p>';

    try {
        const response = await fetch(`/api/search_user?q=${query}`);
        const data = await response.json();

        resultsContainer.innerHTML = ''; 

        if (!data.success) {
            resultsContainer.innerHTML = `<p class="search-message" style="color: red;">Error: ${data.message}</p>`;
            return;
        }
        
        if (data.user) {
            const userElement = createUserElement(data.user, 'following', true);
            resultsContainer.appendChild(userElement);
        } else {
            resultsContainer.innerHTML = '<p class="search-message">No user found with that username.</p>';
        }

    } catch (error) {
        console.error('Error during user search:', error);
        resultsContainer.innerHTML = '<p class="search-message" style="color: red;">Network error during search.</p>';
    }
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    });
}

/**
 * Creates and returns the HTML element for a single notification item.
 */
function createNotificationElement(notificationData) {
    const notifDiv = document.createElement('div');
    notifDiv.className = 'notification-item';
    
    notifDiv.onclick = () => {
        window.location.href = `/profile/${notificationData.actor_username}`; 
    };

    let iconHTML = '';
    let messageTextHTML = ''; 
    
    const actorLinkHTML = `
        <a href="/profile/${notificationData.actor_username}" 
           class="notification-actor-link"
           onclick="event.stopPropagation()">
            @${notificationData.actor_username}
        </a>
    `;

    switch (notificationData.type) {
        case 'mention':
            iconHTML = '<i class="fa-solid fa-at fa-lg" style="color: var(--color-primary);"></i>';
            messageTextHTML = `${actorLinkHTML} mentioned you in a chirp.`;
            break;
            
        case 'new_post': 
            iconHTML = '<i class="fa-solid fa-feather-alt fa-lg" style="color: var(--color-secondary);"></i>';
            messageTextHTML = `${actorLinkHTML} published a new chirp.`;
            break;

        default:
            iconHTML = '<i class="fa-solid fa-bell fa-lg"></i>';
            messageTextHTML = `New activity from ${actorLinkHTML}.`;
    }

    const timeString = formatTimestamp(notificationData.timestamp);
    
    if (!notificationData.is_read) {
        notifDiv.classList.add('notification-unread');
    }

    notifDiv.innerHTML = `
        <div class="notification-icon">${iconHTML}</div>
        <div class="notification-content">
            <p class="notification-message">${messageTextHTML}</p>
            <span class="notification-time">${timeString}</span>
        </div>
    `;

    return notifDiv;
}


/**
 * Fetches and renders the current user's notifications.
 * This also triggers the backend to mark them as read.
 */
async function loadNotifications() {
    const container = document.getElementById('notifications-list-container');
    if (!container) return;
    
    container.innerHTML = '<p class="loading-message">Loading your notifications...</p>';

    try {
        const response = await fetch('/api/notifications');
        const data = await response.json();
        
        if (data.success && data.notifications.length > 0) {
            container.innerHTML = ''; 
            
            data.notifications.forEach(notifData => {
                const notifElement = createNotificationElement(notifData);
                container.appendChild(notifElement);
            });
            
        } else {
            container.innerHTML = '<p class="empty-message">You have no new notifications.</p>';
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
        container.innerHTML = '<p class="error-message">Error loading notifications. Please try again.</p>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setupCommentModal();
    setupChirpModal();
    
    const notificationsContainer = document.getElementById('notifications-list-container');
    if (notificationsContainer) {
        loadNotifications();
    }
});

//  MESSAGING LOGIC 

// Helper function to update the chat header display
function updateChatHeader(partnerUsername) {
    const chatHeader = document.querySelector('.chat-header h3');
    if (chatHeader) {
        chatHeader.textContent = `@${partnerUsername}`;
    }
}

/**
 * Manages the slide-in transition, URL update, and content loading 
 * for the Single-Page Application (SPA) view.
 */
function updateChatView(partnerUsername) {
    const messagesContainer = document.querySelector('.messages-layout-container');
    const body = document.body;

    history.pushState(null, null, `/messages/${partnerUsername}`);
    
    body.setAttribute('data-partner-username', partnerUsername);

    if (messagesContainer) {
        messagesContainer.classList.add('chat-active');
    }

    updateChatHeader(partnerUsername);
    loadMessageHistory(partnerUsername);
}


/**
 * Loads the list of users the current user has messaged (the Inbox).
 */
async function loadConversations() {
    const container = document.getElementById('conversations-list-container');
    if (!container) return;

    container.innerHTML = '<p class="loading-message">Loading conversations...</p>';

    try {
        const response = await fetch('/api/messages/conversations');
        const data = await response.json();

        container.innerHTML = '';
        if (data.success && data.conversations.length > 0) {
            data.conversations.forEach(convo => {
                const convoElement = createConversationElement(convo);
                container.appendChild(convoElement);
            });
        } else {
            container.innerHTML = '<p class="empty-message">Start a new message to begin a conversation.</p>';
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        container.innerHTML = '<p class="error-message">Error loading conversations.</p>';
    }
}

/**
 * Creates the HTML for a single conversation item.
 */
function createConversationElement(convoData) {
    const div = document.createElement('div');
    div.className = 'conversation-item';
    
    div.onclick = () => {
        updateChatView(convoData.partner_username);
    };

    const timeString = formatTimestamp(convoData.last_message_time);
    
    const unreadBadge = convoData.unread_count > 0 
        ? `<span class="unread-badge">${convoData.unread_count}</span>` 
        : '';
    
    let profileImageUrl = '/static/uploads/default-avatar.jpg';
    
    if (convoData.profile_image && convoData.profile_image.trim() !== '') {
        if (convoData.profile_image.startsWith('static/')) {
            profileImageUrl = `/${convoData.profile_image}`;
        } else {
            profileImageUrl = `/static/${convoData.profile_image}`;
        }
    }

    div.innerHTML = `
        <div class="convo-avatar" style="background-image: url('${profileImageUrl}'); background-size: cover; background-position: center;">
        </div> 
        <div class="convo-content">
            <div class="convo-header">
                <strong>@${convoData.partner_username}</strong>
                <span class="convo-time">${timeString}</span>
            </div>
            <p class="convo-last-message">
                ${convoData.last_message_content.substring(0, 50)}...
            </p>
        </div>
        ${unreadBadge}
    `;
    return div;
}

/**
 * Loads and renders the message history with a specific partner.
 */
async function loadMessageHistory(partnerUsername) {
    const messagesContainer = document.getElementById('message-history-container');
    const sendForm = document.getElementById('send-message-form');

    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = '<p class="loading-message">Loading messages...</p>';

    try {
        const response = await fetch(`/api/messages/${partnerUsername}`);
        const data = await response.json();

        messagesContainer.innerHTML = '';
        if (data.success) {
            data.messages.forEach(msg => {
                const msgElement = createMessageElement(msg);
                messagesContainer.appendChild(msgElement);
            });
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            if (sendForm) {
                 sendForm.onsubmit = (e) => handleSendMessage(e, partnerUsername);
            }
        } else {
            messagesContainer.innerHTML = `<p class="empty-message">Start a conversation with @${partnerUsername}.</p>`;
        }
    } catch (error) {
        console.error('Error loading message history:', error);
        messagesContainer.innerHTML = '<p class="error-message">Error loading messages.</p>';
    }
}

/**
 * Creates the HTML for a single message bubble.
 */
function createMessageElement(messageData) {
    const div = document.createElement('div');
    const isOutgoing = messageData.is_outgoing;
    div.className = `message-bubble ${isOutgoing ? 'outgoing' : 'incoming'}`;
    
    const timeString = formatTimestamp(messageData.timestamp); 

    div.innerHTML = `
        <p>${messageData.content}</p>
        <span class="message-time">${timeString}</span>
    `;
    return div;
}

/**
 * Handles the submission of the message form.
 */
async function handleSendMessage(e, partnerUsername) {
    e.preventDefault();
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    const messagesContainer = document.getElementById('message-history-container');

    if (!content) return;
    
    try {
        const response = await fetch(`/api/messages/${partnerUsername}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ content: content })
        });
        const data = await response.json();

        if (data.success) {
            const msgElement = createMessageElement(data.message_data);
            messagesContainer.appendChild(msgElement);
            messageInput.value = ''; 
            messagesContainer.scrollTop = messagesContainer.scrollHeight; 
        } else {
            alert('Failed to send message: ' + data.message);
        }
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

/**
 * Handles the input event on the search box to find any user in the DB.
 */
async function handleUserSearch(event) {
    const query = event.target.value.trim();
    const resultsContainer = document.getElementById('search-results-list'); 
    const inboxContainer = document.getElementById('conversation-list');

    if (query.length === 0) {
        resultsContainer.style.display = 'none';
        inboxContainer.style.display = 'block';
        return;
    }

    inboxContainer.style.display = 'none';
    resultsContainer.style.display = 'block';

    if (query.length < 2) {
        resultsContainer.innerHTML = '<p class="empty-message">Type at least 2 characters to search.</p>';
        return;
    }

    resultsContainer.innerHTML = '<p class="loading-message">Searching...</p>';

    try {
        const response = await fetch(`/api/users/search?q=${query}`);
        const data = await response.json();

        resultsContainer.innerHTML = '';
        if (data.success && data.users.length > 0) {
            data.users.forEach(user => {
                const userElement = createSearchResultItem(user);
                resultsContainer.appendChild(userElement);
            });
        } else {
            resultsContainer.innerHTML = '<p class="empty-message">No users found matching your search.</p>';
        }
    } catch (error) {
        console.error('Error searching users:', error);
        resultsContainer.innerHTML = '<p class="error-message">Error during search.</p>';
    }
}

/**
 * Creates the HTML element for a user in the search results list.
 */
function createSearchResultItem(userData) {
    const div = document.createElement('div');
    div.className = 'search-result-item conversation-item'; 

    div.onclick = () => {
        updateChatView(userData.username);
    };

    let profileImageUrl = '/static/uploads/default-avatar.jpg';
    
    if (userData.profile_image && userData.profile_image.trim() !== '') {
        if (userData.profile_image.startsWith('static/')) {
            profileImageUrl = `/${userData.profile_image}`;
        } else {
            profileImageUrl = `/static/${userData.profile_image}`;
        }
    }

    div.innerHTML = `
        <div class="convo-avatar" style="background-image: url('${profileImageUrl}'); background-size: cover; background-position: center;">
        </div>
        <div class="convo-content">
            <strong>@${userData.username}</strong>
            <span class="convo-time">Start New Chat</span>
        </div>
    `;
    return div;
}

// MAIN ENTRY POINT AND EVENT LISTENERS

document.addEventListener('DOMContentLoaded', () => { 
    const messagesContainer = document.querySelector('.messages-layout-container');
    const body = document.body;
    
    const conversationsContainer = document.getElementById('conversations-list-container');
    if (conversationsContainer) {
        loadConversations();
    }

    const messageHistoryContainer = document.getElementById('message-history-container');
    if (messageHistoryContainer) {
        const partnerUsername = document.body.dataset.partnerUsername; 
        if (partnerUsername) {
            loadMessageHistory(partnerUsername);
        }
    }
    
    if (messagesContainer && document.body.dataset.partnerUsername) {
        messagesContainer.classList.add('chat-active');
    }

    const backButton = document.querySelector('.chat-header .back-button');
    if (backButton) {
        backButton.addEventListener('click', (event) => {
            event.preventDefault(); 
            window.location.href = '/messages'; 
        });
    }


    const searchInput = document.getElementById('new-message-search-input');
    const searchForm = document.getElementById('new-message-search-form');
    
    if (searchForm && searchInput) {
        searchForm.onsubmit = (e) => e.preventDefault(); 
        searchInput.addEventListener('input', handleUserSearch);
        
        searchInput.addEventListener('focus', () => {
             document.getElementById('search-results-list').style.display = 'block';
             document.getElementById('conversation-list').style.display = 'none';
        });
        
        searchInput.addEventListener('blur', () => {
            setTimeout(() => {
                if (searchInput.value.trim() === '') {
                    document.getElementById('search-results-list').style.display = 'none';
                    document.getElementById('conversation-list').style.display = 'block';
                }
            }, 150); 
        });
    }
});
// SEARCH PAGE LOGIC 

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    if (!searchForm) return; 
    
    const searchInput = document.getElementById('search-query-input');
    const usersResults = document.getElementById('users-results');
    const chirpsResults = document.getElementById('chirps-results');
    const tabButtons = document.querySelectorAll('.search-tab-btn');
    
    let currentTab = 'users';
    let currentQuery = '';
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => {
                b.classList.remove('active');
                b.style.borderBottomColor = 'transparent';
                b.style.color = 'var(--text-color-secondary)';
            });
            btn.classList.add('active');
            btn.style.borderBottomColor = 'var(--primary-color)';
            btn.style.color = 'var(--primary-color)';
            
            currentTab = btn.dataset.tab;
            if (currentTab === 'users') {
                usersResults.style.display = 'block';
                chirpsResults.style.display = 'none';
            } else {
                usersResults.style.display = 'none';
                chirpsResults.style.display = 'block';
            }
            
            if (currentQuery) {
                performSearch(currentQuery);
            }
        });
    });
    
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (!query) return;
        
        currentQuery = query;
        await performSearch(query);
    });
    
    async function performSearch(query) {
        const resultsContainer = currentTab === 'users' ? usersResults : chirpsResults;
        resultsContainer.innerHTML = '<p style="padding: 20px; text-align: center;">Searching...</p>';
        
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=${currentTab}`);
            const data = await response.json();
            
            if (!data.success) {
                resultsContainer.innerHTML = `<p style="padding: 20px; text-align: center; color: red;">${data.message}</p>`;
                return;
            }
            
            if (data.results.length === 0) {
                resultsContainer.innerHTML = `<p style="padding: 20px; text-align: center; color: var(--text-color-secondary);">No ${currentTab} found matching "${query}"</p>`;
                return;
            }
            
            resultsContainer.innerHTML = '';
            
            if (currentTab === 'users') {
                data.results.forEach(user => {
                    const userElement = createSearchUserElement(user);
                    resultsContainer.appendChild(userElement);
                });
            } else {
                data.results.forEach(post => {
                    const postElement = createPostElement(post);
                    resultsContainer.appendChild(postElement);
                });
            }
            
        } catch (error) {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: red;">Network error</p>';
        }
    }
    
    function createSearchUserElement(userData) {
        const userDiv = document.createElement('div');
        userDiv.className = 'relationship-item';
        
        const profileImageUrl = userData.profile_image 
            ? `/static/${userData.profile_image}` 
            : '/static/uploads/default-avatar.jpg';
        
        const buttonText = userData.isFollowing ? 'Unfollow' : 'Follow';
        const buttonClass = userData.isFollowing ? 'secondary-button' : 'primary-button';
        
        userDiv.innerHTML = `
            <div class="user-info">
                <div class="profile-avatar-small clickable-avatar" data-username="${userData.username}" style="background-image: url('${profileImageUrl}'); background-size: cover; background-position: center;"></div>
                <div>
                    <strong class="clickable-username" data-username="${userData.username}">${userData.username}</strong>
                    <p class="handle">@${userData.username}</p>
                </div>
            </div>
            <button class="${buttonClass} search-follow-btn" data-username="${userData.username}">${buttonText}</button>
        `;
        
        const avatar = userDiv.querySelector('.clickable-avatar');
        avatar.addEventListener('click', () => {
            window.location.href = `/profile/${userData.username}`;
        });
        
        const username = userDiv.querySelector('.clickable-username');
        username.addEventListener('click', () => {
            window.location.href = `/profile/${userData.username}`;
        });
        
        const followBtn = userDiv.querySelector('.search-follow-btn');
        followBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/follow', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: userData.username })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    if (result.action === 'followed') {
                        followBtn.textContent = 'Unfollow';
                        followBtn.classList.remove('primary-button');
                        followBtn.classList.add('secondary-button');
                    } else {
                        followBtn.textContent = 'Follow';
                        followBtn.classList.remove('secondary-button');
                        followBtn.classList.add('primary-button');
                    }
                }
            } catch (error) {
                console.error('Follow error:', error);
            }
        });
        
        return userDiv;
    }
});