# app.py - Updated with authentication and removed assigned_to
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from validations import TaskValidator, sanitize_input, flash_errors, get_safe_form_data

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), nullable=True)
    due_date = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default="Not Started")
    duration = db.Column(db.Integer, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'


# Create database tables
with app.app_context():
    db.create_all()


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username = get_safe_form_data(request, 'username')
            email = get_safe_form_data(request, 'email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters long.')
            
            if not email or '@' not in email:
                errors.append('Please enter a valid email address.')
            
            if not password or len(password) < 6:
                errors.append('Password must be at least 6 characters long.')
            
            if password != confirm_password:
                errors.append('Passwords do not match.')
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                errors.append('Username already exists.')
            
            if User.query.filter_by(email=email).first():
                errors.append('Email already registered.')
            
            if errors:
                flash_errors(errors)
                return render_template('register.html')
            
            # Create new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration error: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username = get_safe_form_data(request, 'username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
                
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = session.get('username')
    session.clear()
    flash(f'Goodbye, {username}!', 'success')
    return redirect(url_for('login'))


@app.route("/")
@login_required
def index():
    """Display user's tasks"""
    user_id = session.get('user_id')
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()

    today = datetime.today().date()

    for t in tasks:
        # Convert string date to real date
        if t.due_date:
            if isinstance(t.due_date, str):
                t.due_date = datetime.strptime(t.due_date, "%Y-%m-%d").date()

            # Calculate remaining days
            t.days_left = (t.due_date - today).days
        else:
            t.days_left = None

    return render_template("index.html", tasks=tasks)


@app.route('/add', methods=['POST'])
@login_required
def add_task():
    """Add a new task with validation"""
    try:
        user_id = session.get('user_id')
        
        # Get and sanitize form data
        title = get_safe_form_data(request, 'title')
        description = get_safe_form_data(request, 'description')
        priority = get_safe_form_data(request, 'priority', 'None')
        due_date = get_safe_form_data(request, 'due_date')
        
        # Validate data
        is_valid, errors = TaskValidator.validate_task_data(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )
        
        if not is_valid:
            flash_errors(errors)
            return redirect(url_for('index'))
        
        # Create new task
        new_task = Task(
            title=title,
            description=description or None,
            priority=priority,
            due_date=due_date,
            status=request.form.get("status") or "Not Started",
            duration=int(request.form.get("duration") or 0),
            user_id=user_id
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash('Task added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding task: {str(e)}', 'error')
    
    return redirect(url_for('index'))


@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task with validation"""
    try:
        user_id = session.get('user_id')
        task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
        
        if request.method == 'POST':
            # Get and sanitize form data
            title = get_safe_form_data(request, 'title')
            description = get_safe_form_data(request, 'description')
            priority = get_safe_form_data(request, 'priority', 'None')
            due_date = get_safe_form_data(request, 'due_date')
            
            # Validate data
            is_valid, errors = TaskValidator.validate_task_data(
                title=title,
                description=description,
                priority=priority,
                due_date=due_date
            )
            
            if not is_valid:
                flash_errors(errors)
                return render_template('edit.html', task=task)
            
            # Update task
            task.title = title
            task.description = description
            task.priority = priority or 'None'
            task.due_date = due_date
            task.status = request.form.get("status") or "Not Started"
            task.duration = int(request.form.get("duration") or 0)
            
            db.session.commit()
            
            flash('Task updated successfully!', 'success')
            return redirect(url_for('index'))
        
        return render_template('edit.html', task=task)
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating task: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle task completion status"""
    try:
        user_id = session.get('user_id')
        task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
        task.completed = not task.completed
        db.session.commit()
        
        status = 'completed' if task.completed else 'reopened'
        flash(f'Task {status} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling task: {str(e)}', 'error')
    
    return redirect(url_for('index'))


@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    try:
        user_id = session.get('user_id')
        task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
        db.session.delete(task)
        db.session.commit()
        
        flash('Task deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting task: {str(e)}', 'error')
    
    return redirect(url_for('index'))


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    flash('Page not found.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()      # Delete old tables
        db.create_all()    # Create new tables with updated schema
    app.run(debug=True)