# resources/admin/image.py
from flask import current_app
from flask_restful import Resource
from PIL import Image, ImageDraw, ImageFont
from app.utils.response import APIResponse
import os


class AdminImageResource(Resource):
    def get(self):
        """图片处理接口[^1]"""
        try:
            # 读取原始图片
            input_path = os.path.join(current_app.static_folder, 'img/rsic.jpeg')
            img = Image.open(input_path)

            # 获取图片尺寸
            width, height = img.size

            # 创建绘图对象
            draw = ImageDraw.Draw(img)

            # 设置字体
            try:
                font = ImageFont.truetype('arial.ttf', 20)
            except IOError:
                font = ImageFont.load_default()

            # 添加文字
            text = 'The quick brown fox'
            text_width, text_height = draw.textsize(text, font=font)
            x = width - text_width - 20
            y = height - text_height - 20
            draw.text((x, y), text, font=font, fill=(0, 0, 0))

            # 保存处理后的图片
            output_path = os.path.join(current_app.static_folder, 'img/rsic2.png')
            img.save(output_path)

            return APIResponse.success()
        except Exception as e:
            current_app.logger.error(f'图片处理失败: {str(e)}')
            return APIResponse.error('图片处理失败', 500)
