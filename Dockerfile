# استخدم صورة أساسية رسمية لـ Python
FROM python:3.10-slim

# قم بتعيين مجلد العمل داخل الحاوية
WORKDIR /app

# قم بنسخ ملفات التبعيات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# قم بنسخ باقي ملفات التطبيق
COPY . .

# قم بتعيين منفذ الاستماع
EXPOSE 8080

# قم بتشغيل التطبيق عند بدء الحاوية
CMD ["python", "app.py"] # افترض أن اسم ملف تطبيقك هو app.py