from flask import Flask, request, jsonify
import yt_dlp
import asyncio
import logging
import os
from supabase import create_client, Client

app = Flask(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

base_dir = '/tmp/'  # Temporary directory for cloud environments like Render
videos_output = os.path.join(base_dir, "videos_output")

ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': os.path.join(videos_output, '%(id)s.%(ext)s'),
    'noplaylist': True,
    'cookiefile': './cookies.txt',
}

# Function to download video using yt-dlp
async def download_video(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return os.path.join(videos_output, f"{info['id']}.mp4"), info['id']
        except Exception as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return None, None

# Function to upload videos to Supabase
def upload_to_supabase(file_path, bucket_name, file_name):
    try:
        with open(file_path, "rb") as file_data:
            # Upload the video file to Supabase storage
            response = supabase.storage.from_(bucket_name).upload(f"videos/{file_name}", file_data.read())
            
            if response.get("status_code") == 200:
                logging.info(f"Uploaded {file_name} to Supabase successfully")
                return True
            else:
                logging.error(f"Failed to upload {file_name} to Supabase: {response}")
                return False
    except Exception as e:
        logging.error(f"Error uploading file to Supabase: {str(e)}")
        return False

# Process the batch to download and upload to Supabase
async def process_batch(url):
    logging.info(f"Processing URL: {url}")
    video_path, video_id = await download_video(url)
    
    if video_path:
        try:
            if upload_to_supabase(video_path, "youtube-video-snap", f'{video_id}.mp4'):
                logging.info(f"Uploaded {video_id} to Supabase successfully")
            else:
                logging.error(f"Failed to upload {video_id} to Supabase")

            os.remove(video_path)  # Remove after uploading
            
        except Exception as e:
            logging.error(f"Error processing video {video_path}: {str(e)}")

# Flask route to handle video processing
@app.route('/process_video', methods=['GET'])
def process_video():
    video_url = request.args.get('video_url')

    
    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400

    try:
        asyncio.run(process_batch(video_url))
        return jsonify({'message': 'Video processed and uploaded to Supabase'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))  # Default to port 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port, debug=True)
