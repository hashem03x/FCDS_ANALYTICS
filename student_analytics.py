from pymongo import MongoClient
from datetime import datetime
import pandas as pd
from tabulate import tabulate

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
        
        results = list(db.users.aggregate(pipeline))
        
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
                    'Total Credit Hours': student['totalCreditHours'],
                    'Status': student['termStatus']
                })
            
            df = pd.DataFrame(students_data)
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        
        return results
    except Exception as e:
        print(f"Error getting top students by level: {e}")
        return None

def analyze_student_performance(db):
    """Analyze overall student performance by department"""
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
            
            # Group by department and calculate averages
            {
                "$group": {
                    "_id": "$department",
                    "departmentAverage": {"$avg": "$performance.cgpa"},
                    "studentCount": {"$sum": 1}
                }
            },
            
            # Sort by department average
            {"$sort": {"departmentAverage": -1}}
        ]
        
        results = list(db.users.aggregate(pipeline))
        
        if not results:
            print("No performance data found in the database")
            return None
            
        # Create DataFrame for better visualization
        df = pd.DataFrame(results)
        df.columns = ['Department', 'Average CGPA', 'Number of Students']
        
        print("\nDepartment Performance:")
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        
        return results
    except Exception as e:
        print(f"Error analyzing student performance: {e}")
        return None

def analyze_students_by_level(db):
    """Analyze top students by academic level"""
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
            
        return results
    except Exception as e:
        print(f"Error analyzing students by level: {e}")
        return None

def analyze_students_by_department(db):
    """Analyze top students by department"""
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
            
        return results
    except Exception as e:
        print(f"Error analyzing students by department: {e}")
        return None

def main():
    db = connect_to_mongodb()
    if db is None:
        return
        
    print("\n=== Student Analytics Report ===\n")
    
    # Get top students by level
    print("\n1. Top Students by Academic Level:")
    get_top_students_by_level(db)
    
    # Get top students by year and department
    print("\n2. Top Students by Year and Department:")
    get_top_students_by_year_dept(db)
    
    # Get highest course grades
    print("\n3. Highest Course Grades:")
    get_highest_course_grades(db)
    
    # Analyze overall performance
    print("\n4. Overall Performance Analysis:")
    analyze_student_performance(db)

if __name__ == "__main__":
    main()