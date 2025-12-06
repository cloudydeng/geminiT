from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import os

client = genai.Client()

response = client.models.generate_images(
    model='imagen-4.0-generate-001',
    prompt='Robot holding a red skateboard',
    config=types.GenerateImagesConfig(
        number_of_images=4,
    )
)

output_dir = 'generated_images'
os.makedirs(output_dir, exist_ok=True)

for idx, generated in enumerate(response.generated_images):
    gimg = generated.image

    # Base64 解码（关键）
    b64_bytes = gimg.image_bytes  # bytes 类型，但内容是 base64 字符串
    raw_bytes = base64.b64decode(b64_bytes)  # 转为真实 PNG 字节

    # 转成 PIL 图像
    img = Image.open(BytesIO(raw_bytes))

    # 显示
    img.show()

    # 保存
    path = os.path.join(output_dir, f"img_{idx + 1}.png")
    img.save(path)
    print("Saved:", path)
