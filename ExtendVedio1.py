import os
import time
import subprocess
from google import genai  # 新导入（统一 Google GenAI SDK）
from google.genai import types # 类型定义

# --- Configure your API Key ---
# 依赖环境变量（GEMINI_API_KEY 或 Vertex AI）

LOCAL_VIDEO_PATH = "dialogue_example1.mp4"  # 原视频（前8s，必须 Veo 生成）
VIDEO_MODEL_NAME = "veo-3.1-generate-preview"  # 2025年12月 preview，支持扩展

uploaded_video = None
full_path = "extended_full_16s.mp4"  # 输出完整视频

try:
    client = genai.Client()  # 自动使用 GEMINI_API_KEY 或 gcloud

    # Step 1: Upload 原视频（Veo 扩展需 Veo 原生视频）
    print(f"Uploading local video: '{LOCAL_VIDEO_PATH}'...")
    if not os.path.exists(LOCAL_VIDEO_PATH):
        raise FileNotFoundError(
            f"Video file not found at: {LOCAL_VIDEO_PATH}. Generate one first using the test block below!")

    uploaded_video = client.files.upload(file=LOCAL_VIDEO_PATH)
    print("File uploaded successfully! Server-side name:", uploaded_video.name)

    # Step 2: Poll until ACTIVE
    print("Waiting for file processing...")
    while uploaded_video.state.name != "ACTIVE":
        print(f"Current state: {uploaded_video.state.name} (wait 5s...)")
        time.sleep(5)
        uploaded_video = client.files.get(name=uploaded_video.name)
    if uploaded_video.state.name == "FAILED":
        raise ValueError(f"File processing failed: {uploaded_video.error}")
    print("File is ACTIVE and ready!")

    # Step 3: Generate extended video（Veo 自动拼接原视频 + 新部分）
    print("\n--- Starting Veo video extension task (~8s extension, total ~16s) ---")
    extension_prompt = """Extend this Veo-generated video seamlessly: Continue from the end where two people are staring at the cryptic wall drawing under flickering torchlight. The man’s finger traces the symbols. The drawing glows golden, dust falls, runes form a circle. They step back in awe; woman gasps and grabs his arm. Rumbling grows; central stone slides in, revealing blue-lit passage. Wind blows hair, extinguishes torch—darkness, then blue glow lights their stunned faces. Man whispers 'It’s… open.' Woman stares in fear/exhilaration. Slow push-in to entrance, fade to white. Match exact style, lighting, characters, camera, and atmosphere from the input video."""

    # Veo 扩展：用 contents=[video_part, prompt]（官方方法）
    video_part = types.Part.from_uri(
        file_uri=f"files/{uploaded_video.name}",  # URI 格式
        mime_type="video/mp4"
    )

    operation = client.models.generate_videos(
        model=VIDEO_MODEL_NAME,
        video = video_part,
        prompt=extension_prompt,
        config=types.GenerateVideosConfig(
            number_of_videos=1,
            resolution="720p"
        ),
    )

    # 异步轮询（5-15min）
    print("Video extension submitted. Waiting for completion...")
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # Download the video.
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)
    video.video.save("2.mp4")
    print("Generated video saved to 2.mp4")

    # Step 4: Download the full extended video（Veo 输出自动拼接）
    if operation.response and operation.response.parts and operation.response.parts[0].inline_data:
        # Veo 扩展输出在 inline_data（完整视频 bytes 或 URI）
        if hasattr(operation.response.parts[0].inline_data, 'data'):
            video_bytes = operation.response.parts[0].inline_data.data  # 直接 bytes
        else:
            video_uri = operation.response.parts[0].inline_data.uri
            video_bytes = client.files.download(file=video_uri)

        with open(full_path, "wb") as f:
            f.write(video_bytes)
        print(f"Full extended video saved to '{full_path}' (total ~16s, auto-spliced!)")
    else:
        raise ValueError(
            f"No video generated. Check operation.response: {operation.response} (Input must be Veo-generated?)")

except Exception as e:
    print(f"An error occurred: {e}")
    if "unexpected keyword argument 'video'" in str(e):
        print("旧错误：已切换到 contents=[video_part, prompt] + generate_content（官方 Veo 扩展）。")
    elif "must be Veo-generated" in str(e) or "invalid input video" in str(e):
        print("输入视频必须 Veo 原生！运行下面测试生成块创建 dialogue_example1.mp4。")
    elif "quota" in str(e).lower():
        print("配额超限：升级 paid tier 或 Vertex AI")
    elif "safety" in str(e).lower():
        print("Prompt 被过滤：简化描述，避免 'fear'/'whispers' 等词。")

finally:
    # Step 5: Clean up
    if uploaded_video:
        print(f"\nCleaning up: Deleting uploaded file '{uploaded_video.name}'.")
        client.files.delete(name=uploaded_video.name)
    print("Cleanup complete.")