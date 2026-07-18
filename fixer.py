# -*- coding: utf-8 -*-
import requests
import base64
import io
import time
import urllib3
import re
from PIL import Image

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# الإعدادات (تأكد من مطابقتها لسكربتك السابق)
SITE_URL = "https://dev-apk-lite.pantheonsite.io"
WP_API_URL = f"{SITE_URL}/wp-json/wp/v2"
WP_USERNAME = "mahdi18"
WP_APP_PASSWORD = "20101976"
CREDENTIALS = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
TOKEN = base64.b64encode(CREDENTIALS.encode('utf-8')).decode('utf-8')
HEADERS = {"Authorization": f"Basic {TOKEN}"}

def slugify(text):
    text = text.lower().replace(" ", "_")
    return re.sub(r'[^\w]', '', text)

def upload_gallery_image(image_url, game_name, index):
    """رفع صورة المعرض فقط"""
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        img = Image.open(io.BytesIO(response.content))
        output = io.BytesIO()
        img.save(output, format='WEBP', quality=80)
        output.seek(0)
        
        file_name = f"screenshot{index}_{slugify(game_name)}.webp"
        headers = {
            "Authorization": HEADERS["Authorization"],
            "Content-Disposition": f"attachment; filename={file_name}",
            "Content-Type": "image/webp"
        }
        res = requests.post(f"{WP_API_URL}/media", data=output.getvalue(), headers=headers, verify=False)
        return res.json().get('source_url')
    except:
        return None

def fix_only_gallery():
    print("[🔍] جاري فحص وتصحيح معارض الصور فقط...")
    response = requests.get(f"{WP_API_URL}/posts?per_page=50", headers=HEADERS, verify=False)
    for post in response.json():
        game_name = post.get('title', {}).get('rendered', 'game')
        acf = post.get('acf')
        
        if isinstance(acf, dict) and acf.get('app_gallery'):
            gallery_data = acf['app_gallery']
            # تحويل البيانات إلى قائمة روابط
            urls = gallery_data if isinstance(gallery_data, list) else str(gallery_data).split(',')
            
            new_urls = []
            needs_update = False
            
            for i, url in enumerate(urls):
                clean_url = url.strip()
                # إذا كان الرابط لا يزال رابطاً خارجياً (وليس رابط موقعنا)، فهذا يعني أنه يحتاج معالجة
                if clean_url.startswith('http') and SITE_URL not in clean_url:
                    print(f"[{game_name}] جاري تحويل صورة المعرض {i+1}...")
                    new_url = upload_gallery_image(clean_url, game_name, i+1)
                    if new_url:
                        new_urls.append(new_url)
                        needs_update = True
                else:
                    new_urls.append(clean_url)
            
            if needs_update:
                requests.post(f"{WP_API_URL}/posts/{post['id']}", 
                              json={"acf": {"app_gallery": ",".join(new_urls)}}, 
                              headers={**HEADERS, "Content-Type": "application/json"}, 
                              verify=False)
                print(f"[✅] تم تحديث معرض: {game_name}")
            
            time.sleep(0.5)

if __name__ == "__main__":
    fix_only_gallery()
    print("[🎉] انتهت عملية تصحيح المعارض!")
