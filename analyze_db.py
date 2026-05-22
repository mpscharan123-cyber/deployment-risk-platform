import sqlite3
import os

# Connect to the local backend database
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'test.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print('--- RISK LEVELS ---')
for row in c.execute('SELECT risk_level, COUNT(*) FROM risk_predictions GROUP BY risk_level'):
    print(f'{row[0]}: {row[1]}')

print('\n--- AVG RISK SCORE BY AUTHOR ---')
for row in c.execute('''
    SELECT d.author, ROUND(AVG(r.risk_score), 2) 
    FROM deployments d 
    JOIN risk_predictions r ON d.id=r.deployment_id 
    GROUP BY d.author
'''):
    print(f'{row[0]}: {row[1]}')

print('\n--- AVG FILES CHANGED BY RISK LEVEL ---')
for row in c.execute('''
    SELECT r.risk_level, ROUND(AVG(c.files_changed), 2) 
    FROM risk_predictions r 
    JOIN code_changes c ON r.deployment_id=c.deployment_id 
    GROUP BY r.risk_level
'''):
    print(f'{row[0]}: {row[1]} files')

conn.close()
