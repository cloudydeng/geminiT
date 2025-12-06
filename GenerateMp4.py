import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """Traditional Chinese ink wash painting style animation, elderly Yu Gong and his family digging mountain day after day, seasons changing rapidly, spring cherry blossoms to winter snow, mountain slowly disappearing, time-lapse effect, flowing ink and brush strokes, mist and clouds swirling, extremely aesthetic, in the style of Shanghai Animation Film Studio 1960s classic, 4K --ar 16:9'"""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video.
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("dialogue_example1222.mp4")
print("Generated video saved to dialogue_example1.mp4")