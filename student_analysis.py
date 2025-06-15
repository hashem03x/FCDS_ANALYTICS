from pymongo import MongoClient
import pandas as pd
from typing import List, Dict
import json
from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB connection string
MONGO_URI = "mongodb+srv://marwaagamy:77d1hkPmMEnFUSrJ@cluster0.fed1s.mongodb.net/college-system?retryWrites=true&w=majority"

def connect_to_mongodb():
    """Establish connection to MongoDB"""
    try:
        client = MongoClient(MONGO_URI)
        db = client['college-system']
        # Test the connection
        client.admin.command('ping')
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def analyze_student_performance():
    """Analyze student performance by academic level and department"""
    db = connect_to_mongodb()
    if db is None:
        return {"error": "Failed to connect to the database"}

    # Get the users collection
    users = db.users

    # Pipeline for aggregation
    pipeline = [
        {
            "$match": {
                "role": "student"
            }
        },
        {
            "$group": {
                "_id": {
                    "academicLevel": "$performance.academicLevel",
                    "department": "$department"
                },
                "students": {
                    "$push": {
                        "studentId": "$_id",
                        "name": "$name",
                        "cgpa": "$performance.cgpa"
                    }
                }
            }
        },
        {
            "$project": {
                "academicLevel": "$_id.academicLevel",
                "department": "$_id.department",
                "students": {
                    "$sortArray": {
                        "input": "$students",
                        "sortBy": {"cgpa": -1}
                    }
                }
            }
        }
    ]

    try:
        # Execute aggregation
        results = list(users.aggregate(pipeline))
        
        if not results:
            return {"error": "No results found after aggregation"}

        # Create a list to store all student records
        all_students = []
        for group in results:
            for student in group['students']:
                all_students.append({
                    'Student ID': student['studentId'],
                    'Name': student['name'],
                    'CGPA': student['cgpa'],
                    'Academic Level': group['academicLevel'],
                    'Department': group['department']
                })

        if not all_students:
            return {"error": "No student records found in the results"}

        # Create DataFrame
        df = pd.DataFrame(all_students)

        # Prepare the analysis results
        analysis_results = {
            "overall_stats": {
                "total_students": len(df),
                "cgpa_stats": df['CGPA'].describe().to_dict()
            },
            "department_stats": {
                dept: {
                    "student_count": stats[('Student ID', 'count')],
                    "cgpa_mean": stats[('CGPA', 'mean')],
                    "cgpa_min": stats[('CGPA', 'min')],
                    "cgpa_max": stats[('CGPA', 'max')]
                }
                for dept, stats in df.groupby('Department').agg({
                    'CGPA': ['count', 'mean', 'min', 'max'],
                    'Student ID': 'count'
                }).round(2).to_dict().items()
            },
            "level_stats": {
                level: {
                    "student_count": stats[('Student ID', 'count')],
                    "cgpa_mean": stats[('CGPA', 'mean')],
                    "cgpa_min": stats[('CGPA', 'min')],
                    "cgpa_max": stats[('CGPA', 'max')]
                }
                for level, stats in df.groupby('Academic Level').agg({
                    'CGPA': ['count', 'mean', 'min', 'max'],
                    'Student ID': 'count'
                }).round(2).to_dict().items()
            },
            "top_5_overall": df.nlargest(5, 'CGPA')[['Name', 'Department', 'Academic Level', 'CGPA']].to_dict('records'),
            "top_10_by_department": {},
            "top_10_by_dept_level": {}
        }

        # Add top 10 students per department
        for dept in df['Department'].unique():
            dept_df = df[df['Department'] == dept].nlargest(10, 'CGPA')
            analysis_results["top_10_by_department"][dept] = dept_df[['Name', 'Academic Level', 'CGPA']].to_dict('records')

        # Add top 10 students per department and academic level
        for dept in df['Department'].unique():
            analysis_results["top_10_by_dept_level"][dept] = {}
            for level in df['Academic Level'].unique():
                combo_df = df[(df['Department'] == dept) & (df['Academic Level'] == level)]
                if not combo_df.empty:
                    top_10 = combo_df.nlargest(10, 'CGPA')
                    analysis_results["top_10_by_dept_level"][dept][str(level)] = top_10[['Name', 'CGPA']].to_dict('records')

        return analysis_results

    except Exception as e:
        return {"error": str(e)}

@app.route('/api/analysis')
def get_analysis():
    results = analyze_student_performance()
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 
