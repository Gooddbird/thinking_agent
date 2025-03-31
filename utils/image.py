import base64
from PIL import Image
from io import BytesIO

class ImageUtil:
    @staticmethod
    def show_base64_image(base64_str):
        img = Image.open(BytesIO(base64.b64decode(base64_str)))
        img.show()  # 或使用 matplotlib 显示

    @staticmethod
    def save_base64_image(base64_str, file_path):
        img = Image.open(BytesIO(base64.b64decode(base64_str)))
        img.save(file_path)
        return file_path

    @staticmethod
    def reduce_base64_image(base64_str,
                            format='JPEG',  # 目标格式：JPEG/WebP/PNG
                            quality=75,  # 压缩质量（仅对JPEG/WebP有效）
                            scale=0.8  # 缩放比例（0.1~1.0）
                            ):
        """
        压缩Base64编码的图片并返回新Base64字符串
        :param base64_str: 原始Base64字符串（可带data URL前缀）
        :param format: 目标格式（推荐JPEG/WebP）
        :param quality: 压缩质量（数值越小文件越小，建议50~80）
        :param scale: 缩放比例（0.1~1.0，1.0为原尺寸）
        :return: 压缩后的Base64字符串
        """
        # 1. 处理带前缀的Base64字符串（如data:image/png;base64,）
        if 'base64,' in base64_str:
            base64_data = base64_str.split('base64,')[-1]
        else:
            base64_data = base64_str

        # 2. 解码Base64为图片对象
        try:
            img_bytes = base64.b64decode(base64_data)
            img = Image.open(BytesIO(img_bytes))
        except Exception as e:
            print(f"解码失败: {e}")
            return None

        # 3. 缩小尺寸（保持宽高比）
        original_width, original_height = img.size
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        # 4. 转换格式并压缩（使用BytesIO临时存储）
        output_buffer = BytesIO()
        if format == 'JPEG':
            img_resized.convert('RGB').save(output_buffer, format=format, quality=quality, optimize=True)
        elif format == 'WEBP':
            img_resized.convert('RGB').save(output_buffer, format=format, quality=quality, lossless=False)
        elif format == 'PNG':
            img_resized.save(output_buffer, format=format, optimize=True)
        else:
            print("不支持的格式，请选择JPEG/WebP/PNG")
            return None

        # 5. 重新编码为Base64
        output_buffer.seek(0)
        encoded = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        return encoded