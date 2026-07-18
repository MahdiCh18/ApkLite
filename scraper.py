import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import json
import datetime
import random
import time
import re
import subprocess
from io import BytesIO
from PIL import Image
import requests
from google_play_scraper import app, search
import g4f


# ==================== [ 1. إعدادات حساب GitHub ومستودع Cloudflare ] ====================
GITHUB_USER = "MahdiCh18"
GITHUB_EMAIL = "mahdicharafi12@gmail.com"
GITHUB_TOKEN = "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"
GITHUB_REPO = "ApkLite"


# 🎯 الهدف: كم عدد الصفحات الجديدة التي تريد توليدها اليوم قبل الرفع التلقائي؟
TARGET_NEW_POSTS_COUNT = 5 


# ==================== [ 2. إعدادات مسارات نظام الملفات المحلي (Linux) ] ====================
TEMPLATES_DIR = "templates"
APPS_DIR = "apps-pages"
GAMES_DIR = "games-pages"
IMAGES_DIR = "images"
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "script-template.html")


# إنشاء المجلدات محلياً فوراً إن لم تكن موجودة
for folder in [TEMPLATES_DIR, APPS_DIR, GAMES_DIR, IMAGES_DIR]:
    os.makedirs(folder, exist_ok=True)


# قالب HTML افتراضي غني مدعم بالـ 14 متغيراً والسكايما (في حال عدم وجود قالبك بعد)
if not os.path.exists(TEMPLATE_FILE):
    default_template = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تحميل {{APP_NAME}} ({{APP_VERSION}}) - {{APP_CATEGORY_ARABIC}}</title>
    <meta name="description" content="{{APP_SHORT_DESCRIPTION}}">
    <link rel="canonical" href="https://yourdomain.com/{{APP_PAGE_URL}}">
    <!-- Schema.org SoftwareApplication -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "{{APP_NAME}}",
      "operatingSystem": "Android {{APP_MIN_ANDROID}}",
      "applicationCategory": "{{APP_CATEGORY}}",
      "fileSize": "{{APP_SIZE}}",
      "author": { "@type": "Organization", "name": "{{APP_DEVELOPER}}" },
      "aggregateRating": { 
          "@type": "AggregateRating", 
          "ratingValue": "{{APP_RATING_VALUE}}", 
          "ratingCount": "{{APP_RATING_COUNT}}" 
      }
    }
    </script>
</head>
<body>
    <article class="app-container">
        <header>
            <img src="../{{APP_ICON_URL}}" alt="{{APP_NAME}} icon" width="120" height="120" loading="eager">
            <h1>{{APP_NAME}}</h1>
            <span class="badge">{{APP_CATEGORY_ARABIC}}</span>
        </header>
        <section class="meta-info">
            <ul>
                <li><strong>المطور:</strong> {{APP_DEVELOPER}}</li>
                <li><strong>الإصدار:</strong> {{APP_VERSION}}</li>
                <li><strong>الحجم:</strong> {{APP_SIZE}}</li>
                <li><strong>متطلبات التشغيل:</strong> أندرويد {{APP_MIN_ANDROID}}</li>
                <li><strong>التقييم:</strong> ⭐ {{APP_RATING_VALUE}} ({{APP_RATING_COUNT}} مقيم)</li>
            </ul>
        </section>
        <hr>
        <section class="download-section">
            <a href="{{APP_DOWNLOAD_URL}}" class="btn-download" rel="nofollow">تحميل مباشر (APK)</a>
        </section>
        <hr>
        <section class="description">
            <h2>حول {{APP_NAME}}</h2>
            <div>{{APP_LONG_DESCRIPTION}}</div>
        </section>
    </article>
</body>
</html>"""
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as tf:
        tf.write(default_template)
    print(f"[ℹ️] تم إنشاء قالب HTML افتراضي مدعم بالـ 14 متغيراً في: {TEMPLATE_FILE}")




# ==================== [ خريطة ترجمة التصنيفات إلى العربية ] ====================
GENRE_ARABIC_MAP = {
    "GAME_ACTION": "ألعاب أكشن", "GAME_ADVENTURE": "ألعاب مغامرات", "GAME_ARCADE": "ألعاب أركيد",
    "GAME_BOARD": "ألعاب لوحية", "GAME_CARD": "ألعاب ورق", "GAME_CASINO": "ألعاب كازينو",
    "GAME_CASUAL": "ألعاب خفيفة", "GAME_EDUCATIONAL": "ألعاب تعليمية", "GAME_MUSIC": "ألعاب موسيقية",
    "GAME_PUZZLE": "ألعاب ألغاز", "GAME_RACING": "ألعاب سباق", "GAME_ROLE_PLAYING": "ألعاب تقمص أدوار",
    "GAME_SIMULATION": "ألعاب محاكاة", "GAME_SPORTS": "ألعاب رياضية", "GAME_STRATEGY": "ألعاب استراتيجية",
    "GAME_TRIVIA": "ألعاب أسئلة", "GAME_WORD": "ألعاب كلمات", "ART_AND_DESIGN": "فن وتصميم",
    "AUTO_AND_VEHICLES": "سيارات ومركبات", "BEAUTY": "جمال", "BOOKS_AND_REFERENCE": "كتب ومراجع",
    "BUSINESS": "أعمال", "COMICS": "قصص مصورة", "COMMUNICATION": "اتصالات", "DATING": "تعارف",
    "EDUCATION": "تعليم", "ENTERTAINMENT": "ترفيه", "EVENTS": "فعاليات", "FINANCE": "شؤون مالية",
    "FOOD_AND_DRINK": "طعام وشراب", "HEALTH_AND_FITNESS": "صحة ولياقة بدنية", "HOUSE_AND_HOME": "منزل وديكور",
    "LIBRARIES_AND_DEMO": "مكتبات وعروض", "LIFESTYLE": "أسلوب حياة", "MAPS_AND_NAVIGATION": "خرائط وملاحة",
    "MEDICAL": "طب والصحة", "MUSIC_AND_AUDIO": "موسيقى وصوتيات", "NEWS_AND_MAGAZINES": "أخبار ومجلات",
    "PARENTING": "شؤون الأسرة", "PERSONALIZATION": "تخصيص", "PHOTOGRAPHY": "تصوير فوتوغرافي",
    "PRODUCTIVITY": "إنتاجية", "SHOPPING": "تسوّق", "SOCIAL": "تواصل اجتماعي", "SPORTS": "رياضة",
    "TOOLS": "أدوات", "TRAVEL_AND_LOCAL": "سفر ومعلومات محلية", "VIDEO_PLAYERS": "مشغلات فيديو ومحررات",
    "WEATHER": "طقس"
}


def translate_category_to_arabic(genre_id, app_type):
    if genre_id in GENRE_ARABIC_MAP:
        return GENRE_ARABIC_MAP[genre_id]
    return "ألعاب أندرويد" if app_type == "لعبة" else "تطبيقات أندرويد"




# ==================== [ الوظائف المساعدة والذكاء الاصطناعي ] ====================


def get_huge_popular_pool():
    keywords = ["game", "app", "editor", "tool", "player", "new"]
    term = random.choice(keywords)
    results = search(term, lang="en", country="us", n_hits=30)
    clean_packages = [item['appId'] for item in results]
            
    backup_pool = [
        "com.kiloo.subwaysurf", "com.king.candycrushsaga", "com.tencent.ig", "com.dts.freefireth", 
        "com.roblox.client", "com.mojang.minecraftpe", "com.konami.pesam", "com.yallatech.yallaludo",
        "com.zuuks.truck.simulator.europe", "com.supercell.hayday", "com.ea.gp.nfsmobile", "net.onestate.sandbox",
        "com.CarXTech.highways", "com.bandainamcoent.opand", "com.activision.callofduty.warzone", "jp.konami.duellinks",
        "com.alfrasan.wasla", "com.skgames.trafficrider", "com.easybrain.sudoku.android", "com.outfit7.mytalkingtomfree",
        "com.whatsapp", "com.instagram.android", "com.facebook.katana", "org.telegram.messenger", 
        "com.snapchat.android", "com.tiktok.android", "com.capcut.android"
    ]
    
    for bp in backup_pool:
        if bp not in clean_packages:
            clean_packages.append(bp)
            
    random.shuffle(clean_packages)
    return clean_packages




def sanitize_name_for_url(name):
    clean = re.sub(r'[^\w\s-]', '', str(name)).strip().lower()
    return re.sub(r'[\s]+', '-', clean)




def is_already_published(clean_title, app_type):
    safe_name = sanitize_name_for_url(clean_title)
    target_folder = GAMES_DIR if app_type == "لعبة" else APPS_DIR
    expected_filepath = os.path.join(target_folder, f"{safe_name}.html")
    return os.path.exists(expected_filepath)




def ask_local_ai_to_rewrite(original_description, app_title, app_type):
    print(f"[🤖] جاري صياغة الوصف لـ {app_title} بأسلوب السيو العربي...")
    if app_type == "لعبة":
        keywords_prompt = """- "تحميل لعبة للاندرويد مجانا"\n- "تحميل لعبة للهاتف مجانا"\n- "تحميل لعبة للموبايل مجانا" """
    else:
        keywords_prompt = """- "تحميل تطبيق للاندرويد مجانا"\n- "تحميل تطبيق للهاتف مجانا"\n- "تحميل تطبيق للموبايل مجانا" """


    prompt_message = f"""Act as an expert Arabic SEO copywriter for an APK downloading website.
Your task is to rewrite the following description into high-quality, exciting, and persuasive Arabic.
Start with an action hook and distribute these keywords naturally across the content:
{keywords_prompt}


Your response must return the data exactly in this JSON format:
{{
  "arabic_description": "الوصف العربي هنا"
}}
Original description: {original_description}"""
    
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt_message}],
        )
        if response:
            clean_res = response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_res)
            return data.get("arabic_description", original_description)
    except:
        return original_description




def get_app_data_by_id(package_id):
    try:
        result = app(package_id, lang='en', country='us')
        title = result.get('title', '')
        
        app_genre = str(result.get('genre', '')).upper()
        app_genre_id = str(result.get('genreId', '')).upper()
        
        if "GAME" in app_genre or "GAME" in app_genre_id:
            app_type = "لعبة"
        else:
            app_type = "تطبيق"


        if is_already_published(title, app_type):
            print(f"[⏭️] مكرر محلياً: تخطي فوري للملف '{title}'...")
            return "DUPLICATE"
            
        direct_download_url = f"https://d.apkpure.com/b/APK/{package_id}?version=latest"
        original_desc = result.get('description', '')
        arabic_description = ask_local_ai_to_rewrite(original_desc, title, app_type)
        
        # ترجمة الفئة للعربية
        category_arabic = translate_category_to_arabic(app_genre_id, app_type)
        
        # استخراج البيانات بدقة لتغذية الـ 14 متغيراً
        file_size = result.get('size') or 'متغير حسب الجهاز'
        min_android = result.get('androidVersionText') or result.get('androidVersion') or '4.4 وأحدث'
        version_num = result.get('version') or 'Latest'
        developer_name = result.get('developer') or 'غير معروف'
        rating_val = round(float(result.get('score', 4.5)), 1)
        rating_cnt = result.get('ratings') or result.get('reviews') or '1000+'
        
        return {
            "clean_title": title,          
            "description": str(arabic_description), 
            "app_type": app_type,
            "app_icon_url": result.get('icon'),
            "app_developer": str(developer_name),
            "app_category": str(result.get('genre', 'Application')),
            "app_category_arabic": category_arabic,
            "app_version": str(version_num),
            "download_url": direct_download_url,
            "app_size": str(file_size),
            "min_android": str(min_android),
            "rating_value": str(rating_val),
            "rating_count": str(rating_cnt)
        }
    except Exception as e:
        print(f"[🔴] تعذر جلب بيانات الحزمة {package_id}: {e}")
        return None




# ==================== [ 3. معالجة الصور وحفظها محلياً بصيغة WebP ] ====================


def process_and_upload_image(image_url, base_filename, alt_text):
    try:
        res = requests.get(image_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if res.status_code != 200:
            return None


        img = Image.open(BytesIO(res.content)).convert("RGB")
        webp_filename = f"{base_filename}.webp"
        local_image_path = os.path.join(IMAGES_DIR, webp_filename)
        
        img.save(local_image_path, format="WEBP", quality=85)
        return f"{IMAGES_DIR}/{webp_filename}"
    except Exception as e:
        print(f"[⚠️] خطأ أثناء معالجة وحفظ الصورة محلياً {base_filename}: {e}")
        return None




# ==================== [ 4. توليد صفحات HTML الثابتة مع تعويض الـ 14 متغيراً ] ====================


def generate_static_page(game_data):
    if not game_data or game_data == "DUPLICATE":
        return False
        
    print(f"[+] جاري معالجة وحفظ أصول ({game_data['clean_title']})...")
    
    safe_gamename = sanitize_name_for_url(game_data['clean_title'])
    clean_gamename = game_data['clean_title'].replace('_', ' ')
    
    # 5. حفظ الأيقونة وجلب مسارها المحلي
    icon_relative_path = ""
    if game_data['app_icon_url']:
        icon_relative_path = process_and_upload_image(
            game_data['app_icon_url'], 
            f"{safe_gamename}_icon", 
            f"{clean_gamename} icon"
        ) or ""


    print("[+] جاري استبدال الـ 14 متغيراً وتوليد صفحة HTML الثابتة...")
    
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()


    # تحديد المجلد المستهدف (تطبيقات أو ألعاب) وبناء مسار الصفحة (6. APP_PAGE_URL)
    target_dir = GAMES_DIR if game_data['app_type'] == "لعبة" else APPS_DIR
    page_url = f"{target_dir}/{safe_gamename}.html"


    # 2. استخراج ملخص قصير (أول سطرين من الوصف) لـ APP_SHORT_DESCRIPTION
    desc_lines = [line.strip() for line in game_data['description'].split('\n') if line.strip()]
    short_desc = " ".join(desc_lines[:2])
    if len(short_desc) > 230:
        short_desc = short_desc[:227] + "..."


    # 14. تجهيز الوصف الكامل مع استبدال الأسطر بوسوم HTML
    long_desc_html = game_data['description'].replace('\n', '<br>')


    # ==================== [ قاموس البيانات الـ 14 المحددة ] ====================
    replacements = {
        "{{APP_NAME}}": game_data['clean_title'],                  # 1
        "{{APP_SHORT_DESCRIPTION}}": short_desc,                   # 2
        "{{APP_CATEGORY}}": game_data['app_category'],             # 3
        "{{APP_CATEGORY_ARABIC}}": game_data['app_category_arabic'], # 4
        "{{APP_ICON_URL}}": icon_relative_path,                    # 5
        "{{APP_PAGE_URL}}": page_url,                              # 6
        "{{APP_DEVELOPER}}": game_data['app_developer'],           # 7
        "{{APP_VERSION}}": game_data['app_version'],               # 8
        "{{APP_SIZE}}": game_data['app_size'],                     # 9
        "{{APP_MIN_ANDROID}}": game_data['min_android'],           # 10
        "{{APP_RATING_VALUE}}": game_data['rating_value'],         # 11
        "{{APP_RATING_COUNT}}": game_data['rating_count'],         # 12
        "{{APP_DOWNLOAD_URL}}": game_data['download_url'],         # 13
        "{{APP_LONG_DESCRIPTION}}": long_desc_html                 # 14
    }


    # تنفيذ الاستبدال الفعلي داخل النص
    for tag, value in replacements.items():
        html_content = html_content.replace(tag, str(value))


    final_file_path = os.path.join(target_dir, f"{safe_gamename}.html")


    try:
        with open(final_file_path, "w", encoding="utf-8") as out_file:
            out_file.write(html_content)
        print(f"[🟢] تم توليد الصفحة بنجاح: {final_file_path}")
        return True
    except Exception as e:
        print(f"[🔴] خطأ أثناء حفظ ملف HTML: {e}")
        return False




# ==================== [ 5. دالة الرفع التلقائي لـ GitHub ] ====================


def push_to_github():
    print("\n[📦] اكتمل الهدف اليومي! جاري بدء عملية الرفع التلقائي إلى مستودع GitHub...")
    try:
        subprocess.run(["git", "config", "--global", "user.email", GITHUB_EMAIL], check=True)
        subprocess.run(["git", "config", "--global", "user.name", GITHUB_USER], check=True)
        
        secure_remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
        
        print("[⏳] جاري إضافة الملفات التابعة لـ Git (git add .)...")
        subprocess.run(["git", "add", "."], check=True)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("[ℹ️] لا توجد ملفات جديدة أو معدلة لرفعها، المستودع محدث بالفعل.")
            return
            
        commit_message = f"Auto-update: Added new items and assets ({datetime.date.today()})"
        print(f"[⏳] جاري إنشاء الـ Commit: '{commit_message}'...")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        print("[🚀] جاري دفع البيانات إلى GitHub (git push)...")
        subprocess.run(["git", "push", secure_remote_url, "main", "--force"], check=True)
        
        print("[🎉] تم الرفع بنجاح! ستقوم Cloudflare Pages بالتقاط التحديث وبناء الموقع فوراً.")
        
    except subprocess.CalledProcessError as e:
        print(f"[🔴] فشل تنفيذ أمر Git: {e}")
    except Exception as e:
        print(f"[🔴] حدث خطأ غير متوقع أثناء عملية الرفع: {e}")




# ==================== [ التشغيل الرئيسي اللانهائي والمراقب ] ====================


if __name__ == "__main__":
    new_published_counter = 0
    already_checked_packages = set() 
    
    print("[🚀] بدء تشغيل المولد الثابت (Static Site Generator) مع النشر التلقائي...")
    
    while new_published_counter < TARGET_NEW_POSTS_COUNT:
        pool_packages = get_huge_popular_pool()
        print(f"[🔥] تم تجهيز خزان يحتوي على {len(pool_packages)} عنصر!")
        print("----------------------------------------------------------------")
        
        has_new_items_in_pool = False
        
        for package in pool_packages:
            if new_published_counter >= TARGET_NEW_POSTS_COUNT:
                break
                
            if package in already_checked_packages:
                continue
                
            already_checked_packages.add(package)
            has_new_items_in_pool = True
            
            print(f"\n[🔄] فحص الحزمة الحالية: {package}")
            game_data = get_app_data_by_id(package)
            
            if game_data and game_data != "DUPLICATE":
                success = generate_static_page(game_data)
                if success:
                    new_published_counter += 1
                    print(f"[📊] التقدم الحالي: ({new_published_counter}/{TARGET_NEW_POSTS_COUNT}) صفحة ثابتة تم إنشاؤها.")
                    
                    if new_published_counter < TARGET_NEW_POSTS_COUNT:
                        print("[💤] انتظار 5 ثوانٍ قبل معالجة العنصر التالي...")
                        time.sleep(5)
            elif game_data == "DUPLICATE":
                continue
        
        if not has_new_items_in_pool and new_published_counter < TARGET_NEW_POSTS_COUNT:
            print("[⚠️] تم فحص القائمة دون الوصول للهدف اليومي. جلب خزان جديد بعد 10 ثوانٍ...")
            time.sleep(10)


    push_to_github()
    print("\n[🏁] انتهت دورة العمل بنجاح تام! جميع الملفات في مكانها ومرفوعة على السحابة.")