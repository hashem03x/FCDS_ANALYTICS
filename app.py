from flask import Flask, jsonify, send_file
from flask_cors import CORS
from student_analytics import (
    connect_to_mongodb,
    analyze_students_by_level,
    analyze_students_by_department,
    get_highest_course_grades,
    analyze_student_performance
)
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

def create_visualization(data, title, x_label, y_label, x_key, y_key):
    plt.figure(figsize=(12, 6))
    sns.barplot(data=data, x=x_key, y=y_key)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

@app.route('/api/analytics/top-by-level', methods=['GET'])
def get_top_by_level():
    try:
        db = connect_to_mongodb()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        results = analyze_students_by_level(db)
        if results is None:
            return jsonify({"error": "No student data found"}), 404
            
        # Convert results to a more API-friendly format
        formatted_results = {}
        for result in results:
            level = result['level']
            formatted_results[level] = []
            for student in result['topStudents']:
                # Calculate grade distribution
                grade_counts = {}
                for course in student['passedCourses']:
                    grade = course['grade']
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
                
                # Calculate percentage of A grades
                total_courses = len(student['passedCourses'])
                a_grades = grade_counts.get('A', 0) + grade_counts.get('A-', 0)
                a_percentage = (a_grades / total_courses * 100) if total_courses > 0 else 0
                
                formatted_results[level].append({
                    'studentId': student['studentId'],
                    'studentName': student['studentName'],
                    'department': student['department'],
                    'cgpa': round(student['cgpa'], 2),
                    'termGpa': round(student['termGpa'], 2),
                    'totalCreditHours': student['totalCreditHours'],
                    'aGradesPercentage': round(a_percentage, 1),
                    'status': student['termStatus']
                })
        
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/top-by-department', methods=['GET'])
def get_top_by_department():
    try:
        db = connect_to_mongodb()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        results = analyze_students_by_department(db)
        if results is None:
            return jsonify({"error": "No student data found"}), 404
            
        # Convert results to a more API-friendly format
        formatted_results = {}
        for result in results:
            dept = result['department']
            formatted_results[dept] = []
            for student in result['topStudents']:
                # Calculate grade distribution
                grade_counts = {}
                for course in student['passedCourses']:
                    grade = course['grade']
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
                
                # Calculate percentage of A grades
                total_courses = len(student['passedCourses'])
                a_grades = grade_counts.get('A', 0) + grade_counts.get('A-', 0)
                a_percentage = (a_grades / total_courses * 100) if total_courses > 0 else 0
                
                formatted_results[dept].append({
                    'studentId': student['studentId'],
                    'studentName': student['studentName'],
                    'academicLevel': student['academicLevel'],
                    'cgpa': round(student['cgpa'], 2),
                    'termGpa': round(student['termGpa'], 2),
                    'totalCreditHours': student['totalCreditHours'],
                    'aGradesPercentage': round(a_percentage, 1),
                    'status': student['termStatus']
                })
        
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/highest-course-grades', methods=['GET'])
def get_highest_grades():
    try:
        db = connect_to_mongodb()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        results = get_highest_course_grades(db)
        if results is None:
            return jsonify({"error": "No grade data found"}), 404
            
        # Convert results to a more API-friendly format
        formatted_results = []
        for result in results:
            formatted_results.append({
                'courseCode': result['_id'],
                'courseName': result['courseName'],
                'highestMark': result['highestMark'],
                'studentCount': result['studentCount']
            })
        
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/department-performance', methods=['GET'])
def get_department_performance():
    try:
        db = connect_to_mongodb()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        results = analyze_student_performance(db)
        if results is None:
            return jsonify({"error": "No performance data found"}), 404
            
        # Convert results to a more API-friendly format
        formatted_results = []
        for result in results:
            formatted_results.append({
                'department': result['_id'],
                'averageMark': round(result['departmentAverage'], 2),
                'studentCount': result['studentCount']
            })
        
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/visualization/<type>/<identifier>', methods=['GET'])
def get_visualization(type, identifier):
    try:
        db = connect_to_mongodb()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500

        if type == 'level':
            results = analyze_students_by_level(db)
            for result in results:
                if result['level'] == identifier:
                    data = pd.DataFrame(result['topStudents'])
                    buf = create_visualization(
                        data,
                        f'Top Students in {identifier} Level',
                        'Student Name',
                        'CGPA',
                        'studentName',
                        'cgpa'
                    )
                    return send_file(buf, mimetype='image/png')

        elif type == 'department':
            results = analyze_students_by_department(db)
            for result in results:
                if result['department'] == identifier:
                    data = pd.DataFrame(result['topStudents'])
                    buf = create_visualization(
                        data,
                        f'Top Students in {identifier} Department',
                        'Student Name',
                        'CGPA',
                        'studentName',
                        'cgpa'
                    )
                    return send_file(buf, mimetype='image/png')

        elif type == 'courses':
            results = get_highest_course_grades(db)
            data = pd.DataFrame(results)
            buf = create_visualization(
                data,
                'Top Courses by Highest Marks',
                'Course Code',
                'Highest Mark',
                '_id',
                'highestMark'
            )
            return send_file(buf, mimetype='image/png')

        elif type == 'performance':
            results = analyze_student_performance(db)
            data = pd.DataFrame(results)
            buf = create_visualization(
                data,
                'Department Performance',
                'Department',
                'Average Mark',
                '_id',
                'departmentAverage'
            )
            return send_file(buf, mimetype='image/png')

        return jsonify({"error": "Visualization not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 