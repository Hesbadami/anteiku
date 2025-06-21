from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import markdown
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key

# Database setup
def init_db():
    conn = sqlite3.connect('anteiku.db')
    c = conn.cursor()
    
    # Create posts table
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create admin user table
    c.execute('''CREATE TABLE IF NOT EXISTS admin
                 (id INTEGER PRIMARY KEY,
                  username TEXT NOT NULL,
                  password_hash TEXT NOT NULL)''')
    
    # Create default admin user (username: admin, password: coffee123)
    admin_exists = c.execute('SELECT * FROM admin').fetchone()
    if not admin_exists:
        password_hash = generate_password_hash('coffee123')
        c.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', 
                 ('admin', password_hash))
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('anteiku.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    if post is None:
        return "Post not found", 404
    return render_template('post.html', post=post)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['logged_in'] = True
            flash('Welcome back, coffee master! ☕', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials. Even ghouls need the right password! 👻', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully. The coffee aroma lingers... ☕', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin.html', posts=posts)

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        if title and content:
            conn = get_db_connection()
            conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
            conn.commit()
            conn.close()
            flash('New post brewed successfully! ☕', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Title and content are required. Even coffee needs beans! ☕', 'error')
    
    return render_template('new_post.html')

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        if title and content:
            conn.execute('UPDATE posts SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                        (title, content, post_id))
            conn.commit()
            conn.close()
            flash('Post updated successfully! Like a perfect coffee blend ☕', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Title and content are required!', 'error')
    
    conn.close()
    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('Post deleted. Sometimes we must let go of even the finest brews... ☕', 'info')
    return redirect(url_for('admin'))

# Template filters
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text, extensions=['codehilite', 'fenced_code'])

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
