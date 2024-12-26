from flask import Flask, request, jsonify
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import os
import requests
import tempfile
from pydub import AudioSegment
import json
import time
import shutil
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/convert": {"origins": "*"}})


def convert_video_to_text(video_path):
    try:
        # 1. استخراج الصوت من الفيديو
        video = VideoFileClip(video_path)
        audio_path = "audio_temp.wav"
        video.audio.write_audiofile(audio_path)
        video.close()  # إغلاق الفيديو بشكل صريح

        # 2. تحويل الصوت الى تنسيق WAV
        audio = AudioSegment.from_file(audio_path, format="wav")

        # 3. تقسيم الملفات الصوتية الكبيرة
        chunk_size = 600000  # 600000 مللي ثانية = 10 دقائق
        chunks = []
        for i in range(0, len(audio), chunk_size):
            chunks.append(audio[i:i + chunk_size])

        text = ""

        # 4. تحويل كل ملف صوتي إلى نص
        r = sr.Recognizer()
        for i, chunk in enumerate(chunks):
            chunk_file_path = f"audio_chunk_{i}.wav"
            chunk.export(chunk_file_path, format="wav")
            with sr.AudioFile(chunk_file_path) as source:
                audio_data = r.record(source)
                try:
                    chunk_text = r.recognize_google(audio_data, language="ar-AR") # يمكنك تغيير اللغة هنا
                    text += chunk_text + " "
                except sr.UnknownValueError:
                    text += "لا يمكن التعرف على الصوت "
                except sr.RequestError as e:
                    text += f"حدث خطأ في خدمة التعرف على الصوت: {e}"

            os.remove(chunk_file_path)

        # 5. حذف الملفات المؤقتة
        os.remove(audio_path)

        return text.strip()  # حذف المسافات الزائدة في البداية و النهاية

    except Exception as e:
        return str(e)


@app.route('/convert', methods=['POST'])
def convert_video():
    try:
        # check if request is json or multipart
        if request.content_type and request.content_type.startswith('application/json'):
            data = request.get_json()
            if not data or 'url' not in data:
                return jsonify({'error': 'لم يتم إرفاق رابط فيديو'}), 400

            video_url = data['url']

            # 1. تحميل الفيديو من الرابط
            response = requests.get(video_url, stream=True)
            response.raise_for_status()  # التأكد من أن الطلب نجح

            # 2. إنشاء ملف مؤقت لحفظ الفيديو
            # تحديد مسار ثابت للملف المؤقت
            temp_video_path = os.path.join(tempfile.gettempdir(), 'video_temp.mp4')

            with open(temp_video_path, 'wb') as temp_video_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_video_file.write(chunk)

            # 3. تحويل الفيديو إلى نص
            text = convert_video_to_text(temp_video_path)

            # 4. محاولة حذف الملف (مع معالجة الأخطاء)
            try:
                os.remove(temp_video_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

            return jsonify({'text': text})
        elif request.content_type and request.content_type.startswith('multipart/form-data'):
            if 'video' not in request.files:
                return jsonify({'error': 'لم يتم إرفاق ملف فيديو'}), 400

            video_file = request.files['video']
            if video_file.filename == '':
                return jsonify({'error': 'اسم ملف الفيديو غير صالح'}), 400

            # تحديد مسار ثابت للملف المؤقت
            temp_video_path = os.path.join(tempfile.gettempdir(), 'video_temp.mp4')
            video_file.save(temp_video_path)

            text = convert_video_to_text(temp_video_path)

            # 4. محاولة حذف الملف (مع معالجة الأخطاء)
            try:
                os.remove(temp_video_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

            return jsonify({'text': text})
        else:
            return jsonify({'error': 'نوع المحتوى غير مدعوم'}), 415
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'حدث خطأ في تحميل الفيديو: {e}'}), 400
    except Exception as e:
         return jsonify({'error': f'حدث خطأ في الخادم: {e}'}), 500
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)    