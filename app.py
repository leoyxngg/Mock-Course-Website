from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e486d55fc5930d0d8d9879be0fc837064011536635f3e81aef5418b80e9b52f5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignment3.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes = 10)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Person(db.Model):
    __tablename__='Person'
    username=db.Column(db.String(20), primary_key=True)
    email=db.Column(db.String(30), unique=True, nullable=False)
    password=db.Column(db.String(50), nullable=False)
    position=db.Column(db.String(10), nullable=False)

class Mark(db.Model):
    __tablename__='Mark'
    mark_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_username=db.Column(db.String(20), db.ForeignKey(Person.username))
    assignment=db.Column(db.String(20), nullable=False)
    grade=db.Column(db.Integer, nullable=False)
    date_posted=db.Column(db.DateTime, nullable=False, default=datetime.now)
    regrade_requested=db.Column(db.Boolean, default=False)
    regrade_reason = db.Column(db.String(200))

class Feedback(db.Model):
    __tablename__='Feedback'
    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    instructor_username=db.Column(db.String(20), db.ForeignKey(Person.username))
    feedback1=db.Column(db.String(100), nullable=False)
    feedback2=db.Column(db.String(100), nullable=False)
    feedback3=db.Column(db.String(100), nullable=False)
    feedback4=db.Column(db.String(100), nullable=False)

@app.route('/')    
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'name' in session:
            flash('You already logged in!')
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']
        person = Person.query.filter_by(username = username).first()
        if not person or not bcrypt.check_password_hash(person.password, password):
            flash('Please check your login details and try again.', 'Error')
            return render_template('login.html')
        else:
            session['name']=username
            session['position']=person.position
            session.permanent=True
            return redirect(url_for('home'))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method=='GET':
        return render_template('register.html')
    else:
        user_name = request.form['username']
        email = request.form['email']
        hashed_password=bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        position=request.form['position']

        existing_user = Person.query.filter_by(username=user_name).first()
        existing_email = Person.query.filter_by(email=email).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'Error')
            return redirect(url_for('register'))
        elif existing_email:
            flash('Email already exists. Please use a different email address.', 'Error')
            return redirect(url_for('register'))
        else:
            reg_details = (user_name, email, hashed_password, position)
            add_users(reg_details)
            flash('Registration successful! Please login now.')
            return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('name', default = None)
    return redirect(url_for('login'))

def add_users(reg_details):
    user = Person(username = reg_details[0], email = reg_details[1], password = reg_details[2], position = reg_details[3])
    db.session.add(user)
    db.session.commit()

def login_required(position=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'name' not in session:
                return redirect(url_for('login'))
            if position and session.get('position') != position:
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/home')
@login_required()
def home():
    pagename = 'Home'
    return render_template('index.html', pagename=pagename)

@app.route('/announcements')
@login_required()
def announcements():
    pagename = 'Announcements'
    return render_template('announcements.html', pagename=pagename)

@app.route('/faq')
@login_required()
def faq():
    pagename = 'FAQ'
    return render_template('faq.html', pagename=pagename)

@app.route('/lectures')
@login_required()
def lectures():
    pagename = 'Lectures'
    return render_template('lectures.html', pagename=pagename)

@app.route('/tutorials')
@login_required()
def tutorials():
    pagename = 'Tutorials'
    return render_template('tutorials.html', pagename=pagename)

@app.route('/calendar')
@login_required()
def calendar():
    pagename = 'Calendar'
    return render_template('calendar.html', pagename=pagename)

@app.route('/assignments')
@login_required()
def assignments():
    pagename = 'Assignments'
    return render_template('assignments.html', pagename=pagename)

@app.route('/courseteam')
@login_required()
def courseteam():
    pagename = 'Course Team'
    return render_template('course-team.html', pagename=pagename)

@app.route('/student-dashboard')
@login_required(position='student')
def student_dashboard():
    pagename = 'Student Dashboard'
    return render_template('student-dashboard.html', pagename=pagename)

@app.route('/instructor-dashboard')
@login_required(position='instructor')
def instructor_dashboard():
    pagename = 'Instructor Dashboard'
    return render_template('instructor-dashboard.html', pagename=pagename)

@app.route('/marks', methods = ['GET', 'POST'])
@login_required(position='student')
def marks():
    if request.method == 'GET':
        marks_query_results = query_marks(student=session['name'])
        pagename = 'Marks'
        return render_template('marks.html', pagename=pagename, marks_query_results=marks_query_results)
    else:
        mark_id = request.form['mark_id']
        regrade_reason = request.form['regrade_reason']
        mark = Mark.query.get(mark_id)
        mark.regrade_requested = True
        mark.regrade_reason = regrade_reason
        db.session.commit()
        return redirect(url_for('marks'))
    

@app.route('/feedback', methods = ['GET', 'POST'])
@login_required(position='student')
def feedback():
    if request.method=='GET':
        all_instructors = [instructor.username for instructor in Person.query.filter_by(position='instructor').all()]
        return render_template('feedback.html', instructors=all_instructors)
    else:
        instructor_username = request.form['instructor_username']
        feedback1 = request.form['feedback1']
        feedback2 = request.form['feedback2']
        feedback3 = request.form['feedback3']
        feedback4 = request.form['feedback4']
        feedback_details =(instructor_username,
                    feedback1,
                    feedback2,
                    feedback3,
                    feedback4)
        add_feedbacks(feedback_details)
        flash('Feedback for instructor submitted successfully!')
        return redirect(url_for('feedback'))     

@app.route('/all-grades')
@login_required(position='instructor')
def all_grades():
    marks_query_results = query_marks()
    pagename = 'Students Grades Overview'
    return render_template('all-grades.html', pagename=pagename, marks_query_results=marks_query_results)

@app.route('/view-feedback')
@login_required(position='instructor')
def view_feedback():
    feedback_query_results = query_feedbacks(instructor=session['name'])
    pagename = 'View Feedback'
    return render_template('view-feedback.html', pagename=pagename, feedback_query_results=feedback_query_results)

@app.route('/input-grades', methods = ['GET', 'POST'])
@login_required(position='instructor')
def input_grades():
    if request.method=='GET':
        all_students = [student.username for student in Person.query.filter_by(position='student').all()]
        return render_template('add-grades.html', students=all_students)
    else:
        user_name = request.form['username']
        assignment = request.form['assignment']
        grade=request.form['grade']
        existing_mark = Mark.query.filter_by(student_username=user_name, assignment=assignment).first()
        if existing_mark:
            existing_mark.grade = grade
            existing_mark.regrade_requested = False
            existing_mark.regrade_reason = None
            flash('The student has been regraded successfully!')
        else:
            new_mark = Mark(
                student_username=user_name,
                assignment=assignment,
                grade=grade
            )
            db.session.add(new_mark)
            flash('Mark for student inputted successfully!')
        db.session.commit()
        return redirect(url_for('input_grades'))

@app.route('/regrade-requests')
@login_required(position='instructor')
def regrade_requests():
    regrade_query_results = filter_marks()
    pagename = 'Regrade Requests'
    return render_template('regrade-requests.html', pagename=pagename, regrade_query_results=regrade_query_results)

def query_marks(student=None):
    if student is not None:
        marks = Mark.query.filter_by(student_username=student).all()
        return marks
    else:
        marks = Mark.query.all()
        return marks
    
def filter_marks():
    marks = Mark.query.filter_by(regrade_requested=True).all()
    return marks

def add_marks(mark_details):
    mark = Mark(student_username=mark_details[0], assignment=mark_details[1], grade=mark_details[2])
    db.session.add(mark)
    db.session.commit()

def query_feedbacks(instructor):
    feedbacks = Feedback.query.filter_by(instructor_username=instructor).all()
    return feedbacks

def add_feedbacks(feedback_details):
    feedback = Feedback(instructor_username=feedback_details[0], feedback1=feedback_details[1], feedback2=feedback_details[2], feedback3=feedback_details[3], feedback4=feedback_details[4])
    db.session.add(feedback)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)