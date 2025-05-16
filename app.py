from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# Initialize Flask and configure the app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}

db = SQLAlchemy(app)

# Create Student and Task models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    students = db.relationship('Student', backref='group', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    deadline = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    rating = db.Column(db.Integer, nullable=True)  # Column for rating

    # Add relationships
    task = db.relationship('Task', backref='submissions')
    student = db.relationship('Student', backref='submissions')




# Routes for Instructor Login, Task Creation, Student Registration
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/instructor_login', methods=['GET', 'POST'])
def instructor_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'instructor' and password == '123456':
            session['user'] = 'instructor'
            return redirect(url_for('create_student_group'))
        else:
            flash('Incorrect username or password', 'danger')
    return render_template('instructor_login.html')

@app.route('/create_student_group', methods=['GET', 'POST'])
def create_student_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        new_group = Group(name=group_name)
        db.session.add(new_group)
        db.session.commit()
    
    # Pass the list of groups to the template
    groups = Group.query.all()
    return render_template('create_student_group.html', groups=groups)

@app.route('/register_student/<int:group_id>', methods=['GET', 'POST'])
def register_student(group_id):
    if 'user' not in session:
        return redirect(url_for('instructor_login'))

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        new_student = Student(name=name, username=username, password=password, group_id=group_id)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('register_student', group_id=group_id))

    group = Group.query.get(group_id)
    students = Student.query.filter_by(group_id=group_id).all()
    return render_template('register_student.html', group=group, students=students)


from flask import send_from_directory

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route('/post_task/<int:group_id>', methods=['GET', 'POST'])
def post_task(group_id):
    if 'user' not in session:
        return redirect(url_for('instructor_login'))

    if request.method == 'POST':
        task_name = request.form['task_name']
        description = request.form['description']
        deadline = request.form['deadline']
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_task = Task(name=task_name, description=description, deadline=deadline, filename=filename, group_id=group_id)
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('post_task', group_id=group_id))

    group = Group.query.get(group_id)
    tasks = Task.query.filter_by(group_id=group_id).all()
    return render_template('post_task.html', group=group, tasks=tasks)


@app.route('/discussion/<int:group_id>', methods=['GET', 'POST'])
def discussion(group_id):
    if request.method == 'POST':
        message = request.form['message']
        sender = request.form['sender']
        new_message = Chat(message=message, sender=sender, group_id=group_id)
        db.session.add(new_message)
        db.session.commit()
    
    group = Group.query.get(group_id)
    messages = Chat.query.filter_by(group_id=group_id).all()
    return render_template('discussion.html', group=group, messages=messages)

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        student = Student.query.filter_by(username=username, password=password).first()  # Direct password check
        if student:
            session['student_id'] = student.id
            return redirect(url_for('view_tasks'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('student_login.html')


@app.route('/view_tasks', methods=['GET', 'POST'])
def view_tasks():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    student = db.session.get(Student, session['student_id'])
    tasks = Task.query.filter_by(group_id=student.group_id).all()

    # Fetch submissions for each task and include rating
    for task in tasks:
        submission = Submission.query.filter_by(task_id=task.id, student_id=student.id).first()
        task.submission = submission  # Attach submission to task

    return render_template('view_tasks.html', student=student, tasks=tasks)



@app.route('/upload/<int:task_id>', methods=['POST'])
def upload_file(task_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    student = Student.query.get(session['student_id'])
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        submission = Submission(filename=filename, student_id=student.id, task_id=task_id)
        db.session.add(submission)
        db.session.commit()
        flash('File uploaded successfully!', 'success')

    return redirect(url_for('view_tasks'))

@app.route('/upload_submission/<int:task_id>', methods=['POST'])
def upload_submission(task_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    student = db.session.get(Student, session['student_id'])
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        submission = Submission(task_id=task_id, student_id=student.id, filename=filename, rating=None)
        db.session.add(submission)
        db.session.commit()

        flash("File uploaded successfully!", "success")
    
    return redirect(url_for('view_tasks'))

@app.route('/view_submissions/<int:task_id>')
def view_submissions(task_id):
    if 'user' not in session:
        return redirect(url_for('instructor_login'))

    submissions = Submission.query.filter_by(task_id=task_id).all()
    return render_template('view_submissions.html', submissions=submissions)

@app.route('/update_rating/<int:submission_id>', methods=['POST'])
def update_rating(submission_id):
    if 'user' not in session:
        return redirect(url_for('instructor_login'))

    submission = Submission.query.get(submission_id)
    if submission:
        submission.rating = request.form['rating']
        db.session.commit()
        flash('Rating updated successfully!', 'success')

    return redirect(url_for('view_submissions', task_id=submission.task_id))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

import matplotlib.pyplot as plt
import io
import base64

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['user'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
    return render_template('admin_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('admin_login'))

    tasks = Task.query.all()  # Fetch all tasks
    submissions = Submission.query.all()  # Fetch all student submissions

    # Count submissions per task
    task_counts = {}
    for task in tasks:
        count = Submission.query.filter_by(task_id=task.id).count()
        task_counts[task.name] = count

    # Generate graph (submission count per task)
    img = generate_submission_chart(task_counts)

    return render_template('admin_dashboard.html', tasks=tasks, submissions=submissions, chart=img)


def generate_submission_chart(task_counts):
    """Generate a bar chart based on task submissions"""
    plt.figure(figsize=(8, 5))
    plt.bar(task_counts.keys(), task_counts.values(), color='skyblue')
    plt.xlabel('Tasks')
    plt.ylabel('Number of Submissions')
    plt.title('Student Submissions per Task')
    plt.xticks(rotation=45)

    # Save the plot to an image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return chart_url


# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
