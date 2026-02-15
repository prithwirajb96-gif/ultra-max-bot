import os
import random
import numpy as np
import cv2
import librosa
import mediapipe as mp
from PIL import Image, ImageFilter, ImageEnhance
from moviepy.editor import *
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8286531718:AAHYIdl0bckod6_bJFdxLtGRceI5Fp0DIWY"
user_data = {}

mp_face = mp.solutions.face_detection.FaceDetection()

# ---------------- AI FACE SMOOTH ---------------- #
def face_smooth(image_path):
    img = cv2.imread(image_path)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = mp_face.process(rgb)

    if results.detections:
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = img.shape
            x, y = int(bbox.xmin*w), int(bbox.ymin*h)
            bw, bh = int(bbox.width*w), int(bbox.height*h)

            face = img[y:y+bh, x:x+bw]
            face = cv2.GaussianBlur(face, (25,25), 30)
            img[y:y+bh, x:x+bw] = face

    new_path = "smooth_" + image_path
    cv2.imwrite(new_path, img)
    return new_path

# ---------------- NEON EDGE ---------------- #
def neon_glow(frame):
    edges = cv2.Canny(frame,100,200)
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    glow = cv2.addWeighted(frame, 0.8, edges, 0.8, 0)
    return glow

# ---------------- FIRE OVERLAY ---------------- #
def fire_overlay(frame):
    h,w,_ = frame.shape
    overlay = frame.copy()
    for _ in range(100):
        x = random.randint(0,w-1)
        y = random.randint(h//2,h-1)
        overlay[y:y+3,x:x+3] = [0,0,255]
    return cv2.addWeighted(frame,0.9,overlay,0.3,0)

# ---------------- BEAT DETECT ---------------- #
def beat_times(audio):
    y,sr = librosa.load(audio)
    tempo,beats = librosa.beat.beat_track(y=y,sr=sr)
    return librosa.frames_to_time(beats,sr=sr)

# ---------------- CREATE MAX VIDEO ---------------- #
def create_ultra_max(photo_list, music="music.mp3"):
    clips=[]
    duration=3

    for photo in photo_list:
        clip = ImageClip(photo).set_duration(duration).resize((720,1280))
        clip = clip.resize(lambda t: 1+0.1*t)
        clip = clip.fl_image(neon_glow)
        clip = clip.fl_image(fire_overlay)
        clips.append(clip)

    final = concatenate_videoclips(clips)

    if os.path.exists(music):
        audio = AudioFileClip(music).subclip(0, final.duration)
        final = final.set_audio(audio)

    output="ULTRA_MAX.mp4"
    final.write_videofile(output,fps=30)
    return output

# ---------------- BOT ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 ULTRA MAX v3 AI BOT 🔥\nSend 3 Photos + music.mp3 in folder"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data:
        user_data[user_id]=[]

    file = await update.message.photo[-1].get_file()
    filename=f"{user_id}_{len(user_data[user_id])}.jpg"
    await file.download_to_drive(filename)

    smooth=face_smooth(filename)
    user_data[user_id].append(smooth)

    if len(user_data[user_id])==3:
        await update.message.reply_text("🚀 Rendering ULTRA MAX...")
        video=create_ultra_max(user_data[user_id])
        await update.message.reply_video(video=open(video,"rb"))

        for f in user_data[user_id]:
            os.remove(f)
        os.remove(video)
        user_data[user_id]=[]
    else:
        await update.message.reply_text(f"{3-len(user_data[user_id])} photos remaining...")

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.PHOTO,handle_photo))
app.run_polling()