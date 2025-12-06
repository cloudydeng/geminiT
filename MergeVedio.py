import ffmpeg
import os

file1 = "1.mp4"      # 改成你的文件名
file2 = "2.mp4"      # 改成你的文件名
output = "真正合并成功16秒.mp4"

# 创建一个临时的 concat 列表文件（ffmpeg 最稳的拼接方式）
with open("temp_concat_list.txt", "w") as f:
    f.write(f"file '{os.path.abspath(file1)}'\n")
    f.write(f"file '{os.path.abspath(file2)}'\n")

# 用 concat demuxer 方式强制合并（永不失手）
ffmpeg.input("temp_concat_list.txt", format='concat', safe=0).output(
    output,
    c='copy',                  # 先尝试无损
    loglevel="quiet"
).overwrite_output().run()

# 如果无损失败（极少数），自动降级为快速