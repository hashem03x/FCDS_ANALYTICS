from pymongo import MongoClient
from datetime import datetime
import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns

# MongoDB connection
MONGO_URI = "mongodb+srv://marwaagamy:77d1hkPmMEnFUSrJ@cluster0.fed1s.mongodb.net/college-system?retryWrites=true&w=majority"

def connect_to_mongodb():
    try:
        client = MongoClient(MONGO_URI)
        # Test the connection
        client.admin.command('ping')
        db = client['college-system']
        print("Successfully connected to MongoDB!")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_highest_course_grades(db):
    """Get the highest grades for each course"""
    if db is None:
        print("Database connection is not available")
        return None
        
    try:
        # Aggregate grades by course and find highest marks
        pipeline = [
            {
                "$group": {
                    "_id": "$courseCode",
                    "courseName": {"$first": "$courseName"},
                    "highestMark": {"$max": "$totalScore"},
                    "studentCount": {"$sum": 1}
                }
            },
            {"$sort": {"highestMark": -1}},
            {"$limit": 10}
        ]
        
        results = list(db.grades.aggregate(pipeline))
        
        if not results:
            print("No grade data found in the database")
            return None
            
        # Create a DataFrame for better visualization
        df = pd.DataFrame(results)
        df.columns = ['Course Code', 'Course Name', 'Highest Mark', 'Number of Students']
        
        print("\nTop 10 Courses by Highest Marks:")
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        
        # Create a bar plot
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='Course Code', y='Highest Mark')
        plt.title('Top 10 Courses by Highest Marks')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/top_courses.png')
        plt.close()
        
        return results
    except Exception as e:
        print(f"Error getting highest course grades: {e}")
        return None

def get_top_students_by_year_dept(db):
    """Get top 10 students by year and department"""
    if db is None:
        print("Database connection is not available")
        return None
        
    try:
        pipeline = [
            # First join with user collection to get student info
            {
                "$lookup": {
                    "from": "user",
                    "localField": "studentId",
                    "foreignField": "id",
                    "as": "studentInfo"
                }
            },
            {"$unwind": "$studentInfo"},
            {"$match": {"studentInfo.role": "student"}},
            
            # Group by student and calculate averages
            {
                "$group": {
                    "_id": {
                        "year": "$studentInfo.academicLevel",
                        "department": "$studentInfo.department",
                        "studentId": "$studentId",
                        "studentName": "$studentInfo.name"
                    },
                    "averageMark": {"$avg": "$totalScore"},
                    "courseCount": {"$sum": 1}
                }
            },
            
            # Group by year and department
            {
                "$group": {
                    "_id": {
                        "year": "$_id.year",
                        "department": "$_id.department"
                    },
                    "topStudents": {
                        "$push": {
                            "studentId": "$_id.studentId",
                            "studentName": "$_id.studentName",
                            "averageMark": "$averageMark",
                            "courseCount": "$courseCount"
                        }
                    }
                }
            },
            
            # Sort and get top 10 students for each year-department
            {
                "$project": {
                    "year": "$_id.year",
                    "department": "$_id.department",
                    "topStudents": {
                        "$slice": [
                            {
                                "$sortArray": {
                                    "input": "$topStudents",
                                    "sortBy": {"averageMark": -1}
                                }
                            },
                            10
                        ]
                    }
                }
            }
        ]
        
        results = list(db.grades.aggregate(pipeline))
        
        if not results:
            print("No student data found in the database")
            return None
            
        # Process and display results
        for result in results:
            year = result['year']
            dept = result['department']
            print(f"\nTop 10 Students in {year} - {dept} Department:")
            
            # Create DataFrame for this year and department
            df = pd.DataFrame(result['topStudents'])
            df.columns = ['Student ID', 'Student Name', 'Average Mark', 'Courses Taken']
            
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Create a bar plot for this year and department
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x='Student Name', y='Average Mark')
            plt.title(f'Top 10 Students in {year} - {dept} Department')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'static/top_students_{year}_{dept}.png')
            plt.close()
        
        return results
    except Exception as e:
        print(f"Error getting top students: {e}")
        return None

def get_top_students_by_level(db):
    """Get top 10 students for each academic level based on their performance"""
    if db is None:
        print("Database connection is not available")
        return None
        
    try:
        pipeline = [
            # Match only students
            {
                "$match": {
                    "role": "student"
                }
            },
            
            # Group by academic level from performance
            {
                "$group": {
                    "_id": "$performance.academicLevel",
                    "students": {
                        "$push": {
                            "studentId": "$id",
                            "studentName": "$name",
                            "department": "$department",
                            "cgpa": "$performance.cgpa",
                            "termGpa": "$performance.termGpa",
                            "totalCreditHours": "$performance.totalCreditHoursCompleted",
                            "remainingCreditHours": "$performance.remainingCreditHours",
                            "maxAllowedCreditHours": "$performance.maxAllowedCreditHours",
                            "termStatus": "$performance.termStatus",
                            "passedCourses": "$performance.passedCourses",
                            "failedCourses": "$performance.failedCourses"
                        }
                    }
                }
            },
            
            # Sort students within each level by CGPA
            {
                "$project": {
                    "level": "$_id",
                    "topStudents": {
                        "$slice": [
                            {
                                "$sortArray": {
                                    "input": "$students",
                                    "sortBy": {"cgpa": -1}
                                }
                            },
                            10
                        ]
                    }
                }
            }
        ]
        
        results = list(db.user.aggregate(pipeline))
        
        if not results:
            print("No student data found in the database")
            return None
            
        # Process and display results for each level
        for result in results:
            level = result['level']
            print(f"\nTop 10 Students in {level} Level:")
            
            # Create DataFrame for this level
            students_data = []
            for student in result['topStudents']:
                students_data.append({
                    'Student ID': student['studentId'],
                    'Student Name': student['studentName'],
                    'Department': student['department'],
                    'CGPA': round(student['cgpa'], 2),
                    'Term GPA': round(student['termGpa'], 2),
                    'Credit Hours': student['totalCreditHours'],
                    'Remaining Hours': student['remainingCreditHours'],
                    'Term Status': student['termStatus']
                })
            
            df = pd.DataFrame(students_data)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Create a bar plot for this level
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x='Student Name', y='CGPA')
            plt.title(f'Top 10 Students in {level} Level (by CGPA)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'static/top_students_{level}.png')
            plt.close()
            
            # Print detailed course information for each student
            print("\nDetailed Course Information:")
            for student in result['topStudents']:
                print(f"\n{student['studentName']} ({student['studentId']}):")
                print(f"CGPA: {student['cgpa']:.2f}")
                print(f"Term GPA: {student['termGpa']:.2f}")
                print(f"Total Credit Hours: {student['totalCreditHours']}")
                print(f"Remaining Credit Hours: {student['remainingCreditHours']}")
                print(f"Max Allowed Credit Hours: {student['maxAllowedCreditHours']}")
                print(f"Term Status: {student['termStatus']}")
                
                # Calculate grade distribution
                grade_counts = {}
                for course in student['passedCourses']:
                    grade = course['grade']
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
                
                print("\nGrade Distribution:")
                for grade, count in sorted(grade_counts.items()):
                    print(f"{grade}: {count} courses")
                
                # Create DataFrame for passed courses
                if student['passedCourses']:
                    course_df = pd.DataFrame(student['passedCourses'])
                    # Sort by term and then by course code
                    course_df = course_df.sort_values(['term', 'code'])
                    print("\nPassed Courses:")
                    print(tabulate(course_df, headers='keys', tablefmt='psql', showindex=False))
                
                # Create DataFrame for failed courses if any
                if student['failedCourses']:
                    failed_df = pd.DataFrame(student['failedCourses'])
                    print("\nFailed Courses:")
                    print(tabulate(failed_df, headers='keys', tablefmt='psql', showindex=False))
        
        return results
    except Exception as e:
        print(f"Error getting top students by level: {e}")
        return None

def analyze_student_performance(db):
    """Analyze overall student performance"""
    if db is None:
        print("Database connection is not available")
        return None
        
    try:
        pipeline = [
            # First join with user collection to get student info
            {
                "$lookup": {
                    "from": "users",
                    "localField": "studentId",
                    "foreignField": "id",
                    "as": "studentInfo"
                }
            },
            {"$unwind": "$studentInfo"},
            {"$match": {"studentInfo.role": "student"}},
            
            # Group by student and calculate averages
            {
                "$group": {
                    "_id": "$studentId",
                    "averageMark": {"$avg": "$totalScore"},
                    "courseCount": {"$sum": 1}
                }
            },
            
            # Join back with user collection to get department info
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "id",
                    "as": "studentInfo"
                }
            },
            {"$unwind": "$studentInfo"},
            
            # Group by department
            {
                "$group": {
                    "_id": "$studentInfo.department",
                    "departmentAverage": {"$avg": "$averageMark"},
                    "studentCount": {"$sum": 1}
                }
            },
            {"$sort": {"departmentAverage": -1}}
        ]
        
        results = list(db.grades.aggregate(pipeline))
        
        if not results:
            print("No performance data found in the database")
            return None
            
        # Create DataFrame
        df = pd.DataFrame(results)
        df.columns = ['Department', 'Average Mark', 'Number of Students']
        
        print("\nDepartment-wise Performance:")
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        
        # Create a bar plot
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='Department', y='Average Mark')
        plt.title('Department-wise Average Performance')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/department_performance.png')
        plt.close()
        
        return results
    except Exception as e:
        print(f"Error analyzing student performance: {e}")
        return None

def analyze_students_by_level(db):
    """Analyze students grouped by academic level"""
    if db is None:
        print("Database connection is not available")
        return None
        
    try:
        pipeline = [
            # Match only students
            {
                "$match": {
                    "role": "student"
                }
            },
            
            # Group by academic level
            {
                "$group": {
                    "_id": "$performance.academicLevel",
                    "students": {
                        "$push": {
                            "studentId": "$id",
                            "studentName": "$name",
                            "department": "$department",
                            "cgpa": "$performance.cgpa",
                            "termGpa": "$performance.termGpa",
                            "totalCreditHours": "$performance.totalCreditHoursCompleted",
                            "remainingCreditHours": "$performance.remainingCreditHours",
                            "termStatus": "$performance.termStatus",
                            "passedCourses": "$performance.passedCourses"
                        }
                    }
                }
            },
            
            # Sort students within each level by CGPA
            {
                "$project": {
                    "level": "$_id",
                    "topStudents": {
                        "$slice": [
                            {
                                "$sortArray": {
                                    "input": "$students",
                                    "sortBy": {"cgpa": -1}
                                }
                            },
                            10
                        ]
                    }
                }
            }
        ]
        
        results = list(db.users.aggregate(pipeline))
        
        if not results:
            print("No student data found in the database")
            return None
            
        print("\n=== Top Students by Academic Level ===")
        for result in results:
            level = result['level']
            print(f"\nTop 10 Students in {level} Level:")
            
            # Create DataFrame for this level
            students_data = []
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
                
                students_data.append({
                    'Student ID': student['studentId'],
                    'Student Name': student['studentName'],
                    'Department': student['department'],
                    'CGPA': round(student['cgpa'], 2),
                    'Term GPA': round(student['termGpa'], 2),
                    'Credit Hours': student['totalCreditHours'],
                    'A Grades %': round(a_percentage, 1),
                    'Status': student['termStatus']
                })
            
            df = pd.DataFrame(students_data)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Create a bar plot for this level
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x='Student Name', y='CGPA')
            plt.title(f'Top 10 Students in {level} Level (by CGPA)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'static/top_students_{level}.png')
            plt.close()
        
        return results
    except Exception as e:
        print(f"Error analyzing students by level: {e}")
        return None

def analyze_students_by_department(db):
    """Analyze students grouped by department"""
    if db is None:
        print("Database connection is not available")
        return None
        
    try:
        pipeline = [
            # Match only students
            {
                "$match": {
                    "role": "student"
                }
            },
            
            # Group by department
            {
                "$group": {
                    "_id": "$department",
                    "students": {
                        "$push": {
                            "studentId": "$id",
                            "studentName": "$name",
                            "academicLevel": "$performance.academicLevel",
                            "cgpa": "$performance.cgpa",
                            "termGpa": "$performance.termGpa",
                            "totalCreditHours": "$performance.totalCreditHoursCompleted",
                            "remainingCreditHours": "$performance.remainingCreditHours",
                            "termStatus": "$performance.termStatus",
                            "passedCourses": "$performance.passedCourses"
                        }
                    }
                }
            },
            
            # Sort students within each department by CGPA
            {
                "$project": {
                    "department": "$_id",
                    "topStudents": {
                        "$slice": [
                            {
                                "$sortArray": {
                                    "input": "$students",
                                    "sortBy": {"cgpa": -1}
                                }
                            },
                            10
                        ]
                    }
                }
            }
        ]
        
        results = list(db.users.aggregate(pipeline))
        
        if not results:
            print("No student data found in the database")
            return None
            
        print("\n=== Top Students by Department ===")
        for result in results:
            dept = result['department']
            print(f"\nTop 10 Students in {dept} Department:")
            
            # Create DataFrame for this department
            students_data = []
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
                
                students_data.append({
                    'Student ID': student['studentId'],
                    'Student Name': student['studentName'],
                    'Academic Level': student['academicLevel'],
                    'CGPA': round(student['cgpa'], 2),
                    'Term GPA': round(student['termGpa'], 2),
                    'Credit Hours': student['totalCreditHours'],
                    'A Grades %': round(a_percentage, 1),
                    'Status': student['termStatus']
                })
            
            df = pd.DataFrame(students_data)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Create a bar plot for this department
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x='Student Name', y='CGPA')
            plt.title(f'Top 10 Students in {dept} Department (by CGPA)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'static/top_students_{dept}.png')
            plt.close()
        
        return results
    except Exception as e:
        print(f"Error analyzing students by department: {e}")
        return None

def main():
    try:
        # Connect to MongoDB
        db = connect_to_mongodb()
        if db is None:
            print("Failed to connect to the database. Exiting...")
            return
        
        # Analyze students by academic level
        print("\nAnalyzing students by academic level...")
        level_analysis = analyze_students_by_level(db)
        
        # Analyze students by department
        print("\nAnalyzing students by department...")
        dept_analysis = analyze_students_by_department(db)
        
        print("\nAnalysis complete! Check the generated PNG files for visualizations.")
        
    except Exception as e:
        print(f"An error occurred during analysis: {e}")
    finally:
        # Close the MongoDB connection
        if 'db' in locals() and db is not None:
            db.client.close()
            print("MongoDB connection closed.")

if __name__ == "__main__":
    main()