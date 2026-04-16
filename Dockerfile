# 1. בחירת תמונה קלה של פייתון
FROM python:3.9-slim

# 2. הגדרת תיקיית העבודה בתוך הקונטיינר
WORKDIR /app

# 3. התקנת תלויות מערכת בסיסיות (ליתר ביטחון)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 4. העתקת קובץ הדרישות והתקנת הספריות
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. העתקת שאר קבצי הקוד (app.py, logic.py וכו')
COPY . .

# 6. חשיפת הפורט ש-Streamlit משתמש בו (ברירת מחדל 8501)
EXPOSE 8501

# 7. פקודת ההרצה של האפליקציה
# הכתובת 0.0.0.0 מאפשרת גישה מבחוץ לקונטיינר
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]