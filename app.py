from flask import Flask, jsonify
from flask_cors import CORS
from student_analytics import (
    connect_to_mongodb,
    analyze_students_by_level,
    analyze_students_by_department,
    get_highest_course_grades,
    analyze_student_performance
)

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/api/*": {
    "origins": [
        "http://localhost:3000",
        "https://fcds-system.vercel.app",
        "https://fcds-system-git-main-ahmedmohamed2002.vercel.app"
    ],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})

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

if __name__ == '__main__':
    app.run(debug=True, port=5000) 