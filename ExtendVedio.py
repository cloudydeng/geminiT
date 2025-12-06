import os
import time
import subprocess
import google.generativeai as genai
from google.generativeai import types

# --- 1. 配置 ---
# 确保您的API Key已通过环境变量 `GOOGLE_API_KEY` 设置
# genai.configure(api_key="YOUR_API_KEY")

LOCAL_VIDEO_PATH = "base_video_from_veo.mp4"  # 输入视频，官方建议也由Veo生成
VIDEO_MODEL_NAME = "veo-1.0-preview"          # 请替换为您账户可用的Veo模型名称

uploaded_video_file = None
extension_path = "generated_extension.mp4"    # 预定义，便于在finally块中清理

try:
    client = genai.Client()

    # --- 2. 上传并等待视频处理 ---
    print(f"Uploading base video: '{LOCAL_VIDEO_PATH}'...")
    if not os.path.exists(LOCAL_VIDEO_PATH):
        raise FileNotFoundError(f"Base video file not found at: {LOCAL_VIDEO_PATH}")

    uploaded_video_file = genai.upload_file(path=LOCAL_VIDEO_PATH)
    print(f"File '{uploaded_video_file.display_name}' uploaded. Server name: {uploaded_video_file.name}")

    print("Waiting for video to become ACTIVE...")
    while uploaded_video_file.state.name != "ACTIVE":
        print(f"Current state: {uploaded_video_file.state.name}. Waiting 10 seconds...")
        time.sleep(10)
        uploaded_video_file = genai.get_file(name=uploaded_video_file.name)

    if uploaded_video_file.state.name == "FAILED":
        raise ValueError(f"Video processing failed: {uploaded_video_file.error}")
    print("Video is ACTIVE and ready for use.")


    # --- 3. 调用Veo进行视频扩展 (使用统一的 generate_content 接口) ---
    print("\nStarting video extension with Veo...")
    extension_prompt = "A fluffy white puppy with curious eyes runs into the frame, looks at the origami flower, and gently pats it with its paw."

    # 将视频文件封装为 Part 对象
    video_part = types.Part.from_uri(
        file_uri=uploaded_video_file.uri,
        mime_type=uploaded_video_file.mime_type
    )

    # **核心：使用 generate_content 并将视频和文本一起放入 contents 列表**
    response = client.models.generate_content(
        model=VIDEO_MODEL_NAME,
        contents=[video_part, extension_prompt], # <-- 您的正确思路
        config=types.GenerateContentConfig(     # <-- 使用对应的 Content 配置
            temperature=0.7,
        ),
    )

    # --- 4. 从响应中提取并保存视频 ---
    if response.parts and response.parts[0].inline_data and response.parts[0].inline_data.mime_type.startswith("video/"):
        video_bytes = response.parts[0].inline_data.data
        with open(extension_path, "wb") as f:
            f.write(video_bytes)
        print(f"Generated extension video saved to '{extension_path}'")
    else:
        # 如果模型返回了文本（例如，安全拒绝），则打印出来
        raise ValueError(f"No video was generated. Model response: {response.text or 'Empty'}")


    # --- 5. (可选) 使用 ffmpeg 拼接视频 ---
    print("\nSplicing original and extension videos with ffmpeg...")
    full_path = "final_extended_video.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", LOCAL_VIDEO_PATH,
        "-i", extension_path,
        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        full_path
    ], check=True, capture_output=True)

    print(f"Successfully created full video: '{full_path}'")


except Exception as e:
    print(f"\nAn error occurred: {e}")

finally:
    # --- 6. 清理资源 ---
    print("\nCleaning up resources...")
    if uploaded_video_file:
        print(f"Deleting uploaded file '{uploaded_video_file.name}' from the server.")
        genai.delete_file(name=uploaded_video_file.name)
    if os.path.exists(extension_path):
        print(f"Deleting temporary extension file '{extension_path}'.")
        os.remove(extension_path)
    print("Cleanup complete.")
