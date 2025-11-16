from PIL import Image, ImageStat, ImageFilter
import colorsys

class CropHealthAnalyzer:

    def analyze_image(self, image_path: str):
        img = Image.open(image_path).convert("RGB")
        stat = ImageStat.Stat(img)

        r, g, b = stat.mean
        brightness = (r + g + b) / 3
        greenness = g / max((r + g + b), 1)

        hsv_img = img.convert("HSV")
        h_stat = ImageStat.Stat(hsv_img)
        h, s, v = h_stat.mean 

        blurred = img.filter(ImageFilter.GaussianBlur(3))
        detail_img = Image.blend(img, blurred, -0.5)  
        texture_stat = ImageStat.Stat(detail_img.convert("L"))
        texture = texture_stat.stddev[0]  

        yellow_ratio = (r + g) / max((r + g + b), 1)
        brown_ratio = (r * 0.8 + g * 0.5) / max((r + g + b), 1)

        if greenness > 0.42 and brightness > 110 and texture < 18:
            return {"status": "HEALTHY", "score": 0.95}

        if yellow_ratio > 0.75 and g > r:  
            return {"status": "YELLOWING", "score": 0.40}

        if brightness < 80 and greenness < 0.32:
            return {"status": "WATER_STRESSED", "score": 0.30}

        if brightness > 170 and s < 60 and greenness < 0.35:
            return {"status": "SUN_STRESSED", "score": 0.45}

        if s < 50 and greenness < 0.38:
            return {"status": "NUTRIENT_DEFICIENT", "score": 0.50}

        if brown_ratio > 0.70 and brightness < 130:
            return {"status": "WILTING", "score": 0.35}

        if texture > 28:
            return {"status": "DISEASED", "score": 0.20}

        return {"status": "OBSERVE", "score": 0.60}
