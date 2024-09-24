from flask import Flask, request, jsonify
import yt_dlp
import asyncio
import logging
import os

app = Flask(__name__)

base_dir = os.path.expanduser("~/Downloads/")
videos_output = os.path.join(base_dir, "videos_output")
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': os.path.join(videos_output, '%(id)s.%(ext)s'),
    'noplaylist': True,
}

async def download_video(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return os.path.join(videos_output, f"{info['id']}.mp4"), info['id']
        except Exception as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return None, None


async def process_batch(url):
    logging.info(f"Processing URL: {url}")
    video_path, video_id = await download_video(url)
    if video_path:
        try:
            clips = await process_video(video_path, video_id)
            # if clips:
            #     await processed_queue.put((url, video_id, video_path, clips))
                
            #     # Move clip file deletion here
            #     for clip in clips:
            #         os.remove(clip['path'])
            
            # # Move video file deletion here, after processing
            # os.remove(video_path)
        except Exception as e:
            logging.error(f"Error processing video {video_path}: {str(e)}")


@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400

    try:
        await process_batch(video_url)

        return jsonify({'message': 'Video processed and clips uploaded'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    

if __name__ == '__main__':
    app.run(debug=True)
