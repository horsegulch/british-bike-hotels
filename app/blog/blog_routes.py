# app/blog/blog_routes.py

from flask import render_template, abort
# This is the only import needed from the current blueprint package
from . import blog 
from .. import mongo

# Route to display the blog index page
@blog.route('/blog')
def index():
    """Renders the blog index page with all published posts."""
    posts = mongo.db.blog_posts.find({'status': 'published'}).sort("created_at", -1)
    return render_template('blog/index.html', posts=list(posts))

# Route to display a single blog post by its slug
@blog.route('/blog/post/<slug>')
def post(slug):
    """Renders a single blog post page, finding the post by its unique slug."""
    post = mongo.db.blog_posts.find_one({'slug': slug, 'status': 'published'})
    if not post:
        abort(404)  # If no post with that slug is found, return a 404 error
    return render_template('blog/post.html', post=post)
