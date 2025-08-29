import os
import zipfile
import tempfile
import shutil
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from github import Github, GithubException, InputGitTreeElement
import logging
import re
import aiohttp
import aiofiles


"""• أول فريق مصري متخصص في تطوير بايثون Python   
• القناة #Code الرسميـة الرائدة في تـعليم البرمجة عربيًا 
• جميع الحقوق و النشر محفوظة:  ©️ VEGA™ ₂₀₁₅  
• مطور ومُنشئ المحتوى:  
• @TopVeGa
• @DevVeGa
""""



API_ID = 1846213  
API_HASH = "c545c613b78f18a30744970910124d53"  
BOT_TOKEN = "8122672674:A*******"#توكن البوت هنا 
GITHUB_TOKEN = "ghp_*******"#توكن جيثاب هنا
user_data = {}


app = Client("github", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": None}
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["📤 رفع ملف مضغوط", "🗑 حذف ملفات"],
            ["📂 مستودعاتي", "ℹ️ المساعدة"]
        ],
        resize_keyboard=True
    )
    
    await message.reply_text(
        "مرحباً! 👋\nأنا بوت متقدم لرفع الملفات إلى GitHub.\n\n"
        "يمكنني:\n"
        "• رفع ملفات مضغوطة (ZIP, RAR) وتفكيكها تلقائياً\n"
        "• رفع دفعات من الملفات مرة واحدة\n"
        "• حذف الملفات من مستودعاتك\n"
        "• إدارة مستودعاتك بسهولة\n\n"
        "اختر أحد الخيارات من لوحة المفاتيح:",
        reply_markup=keyboard
    )

"""
• أول فريق مصري متخصص في تطوير بايثون Python   
• القناة #Code الرسميـة الرائدة في تـعليم البرمجة عربيًا 
• جميع الحقوق و النشر محفوظة:  ©️ VEGA™ ₂₀₁₅  
• مطور ومُنشئ المحتوى:  
• @TopVeGa
• @DevVeGa
""""
@app.on_message(filters.text & ~filters.command)
async def handle_text_messages(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "📤 رفع ملف مضغوط":
        await start_upload_process(client, message)
    elif text == "🗑 حذف ملفات":
        await start_delete_process(client, message)
    elif text == "📂 مستودعاتي":
        await list_repositories(client, message)
    elif text == "ℹ️ المساعدة":
        await show_help(client, message)
    elif user_id in user_data:
        await handle_user_steps(client, message, user_id, text)

async def start_upload_process(client: Client, message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "github_username", "files": []}
    
    await message.reply_text(
        "لنبدأ عملية الرفع! 🚀\n\nأولاً، أرسل لي اسم المستخدم في GitHub:"
    )

async def start_delete_process(client: Client, message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "delete_repo"}
    
    await message.reply_text(
        "أرسل لي اسم المستودع الذي تريد حذف ملفات منه:"
    )

async def list_repositories(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        g = Github(GITHUB_TOKEN)
        user = g.get_user()
        repos = user.get_repos()
        
        if repos.totalCount == 0:
            await message.reply_text("ليس لديك أي مستودعات بعد.")
            return
        
        repo_list = "مستودعاتك على GitHub:\n\n"
        for repo in repos[:10]: 
            repo_list += f"• {repo.name} - {repo.html_url}\n"
        
        if repos.totalCount > 10:
            repo_list += f"\nو {repos.totalCount - 10} مستودعات أخرى..."
        
        await message.reply_text(repo_list)
        
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        await message.reply_text("حدث خطأ أثناء جلب المستودعات. يرجى المحاولة لاحقاً.")

async def show_help(client: Client, message: Message):
    help_text = """
🎯 **كيفية استخدام البوت:**

1. **لرفع ملف مضغوط:**
   - اضغط على "📤 رفع ملف مضغوط"
   - أرسل اسم مستخدم GitHub الخاص بك
   - أرسل اسم المستودع (سيتم إنشاؤه إذا لم يكن موجوداً)
   - أرسل الملف المضغوط (ZIP, RAR)

2. **لحذف ملفات:**
   - اضغط على "🗑 حذف ملفات"
   - أرسل اسم المستودع
   - أرسل أسماء الملفات التي تريد حذفها (مفصولة بمسافات)

3. **لعرض مستودعاتك:**
   - اضغط على "📂 مستودعاتي"

📁 **الملفات المدعومة:**
ZIP, RAR

⚡ **ميزات متقدمة:**
- رفع دفعات من الملفات
- حفظ حالة الرفع واستئنافها
    """
    
    await message.reply_text(help_text, parse_mode=enums.ParseMode.MARKDOWN)

async def handle_user_steps(client: Client, message: Message, user_id: int, text: str):
    step = user_data[user_id].get("step")
    
    if step == "github_username":
        user_data[user_id]["github_username"] = text
        user_data[user_id]["step"] = "repo_name"
        
        await message.reply_text(
            "جيد! 👍\nالآن أرسل لي اسم المستودع (Repository) الذي تريد الرفع إليه:"
        )
    
    elif step == "repo_name":
        user_data[user_id]["repo_name"] = text
        user_data[user_id]["step"] = "waiting_files"
        
        await message.reply_text(
            "ممتاز! 😊\nالآن أرسل لي الملف المضغوط الذي تريد تفكيكه ورفعه.\n\n"
            "عندما تنتهي من إرسال الملف، سأبدأ المعالجة تلقائياً."
        )
    
    elif step == "delete_repo":
        user_data[user_id]["repo_to_delete"] = text
        user_data[user_id]["step"] = "delete_files"
        
        await message.reply_text(
            "حسناً. الآن أرسل أسماء الملفات التي تريد حذفها (مفصولة بمسافات):\n\n"
            "مثال: file1.txt folder/file2.py image.jpg"
        )
    
    elif step == "delete_files":
        repo_name = user_data[user_id]["repo_to_delete"]
        files_to_delete = text.split()
        
        try:
            await message.reply_text("جاري حذف الملفات... ⏳")
            
            g = Github(GITHUB_TOKEN)
            user = g.get_user()
            repo = user.get_repo(repo_name)
            
            deleted_files = []
            not_found_files = []
            
            for file_path in files_to_delete:
                try:
                    contents = repo.get_contents(file_path)
                    if isinstance(contents, list):
                        for content in contents:
                            repo.delete_file(content.path, f"Delete {content.path}", content.sha)
                            deleted_files.append(content.path)
                    else:
                        repo.delete_file(contents.path, f"Delete {file_path}", contents.sha)
                        deleted_files.append(file_path)
                except GithubException as e:
                    if e.status == 404:
                        not_found_files.append(file_path)
                    else:
                        logger.error(f"Error deleting file {file_path}: {e}")
                        not_found_files.append(file_path)
            
        
            result_message = "نتيجة الحذف:\n\n"
            if deleted_files:
                result_message += f"✅ الملفات المحذوفة: {', '.join(deleted_files)}\n"
            if not_found_files:
                result_message += f"❌ الملفات غير الموجودة: {', '.join(not_found_files)}\n"
            
            await message.reply_text(result_message)
            
        except Exception as e:
            logger.error(f"Error deleting files: {e}")
            await message.reply_text(f"حدث خطأ أثناء حذف الملفات: {str(e)}")
        
        finally:
            if user_id in user_data:
                del user_data[user_id]
                
@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or user_data[user_id].get("step") != "waiting_files":
        return
    supported_extensions = ('.zip', '.rar')
    file_name = message.document.file_name.lower()
    
    if not any(file_name.endswith(ext) for ext in supported_extensions):
        await message.reply_text(
            "يرجى إرسال ملف مضغوط مدعوم فقط (ZIP, RAR)."
        )
        return
    await message.reply_text(f"جاري تنزيل {message.document.file_name}... ⏬")
    download_path = await message.download()
    user_data[user_id]["files"].append({
        "name": message.document.file_name,
        "path": download_path
    })
    
    await message.reply_text(
        f"تم استلام {message.document.file_name}.\n"
        "جاري البدء في المعالجة والرفع..."
    )
    await process_uploaded_files(client, message, user_id)

async def extract_archive(file_path, extract_to):
    """دالة لتفكيك الملفات المضغوطة"""
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    else:
     
        await message.reply_text("نوع الملف غير مدعوم بشكل كامل. يرجى استخدام ZIP.")
        raise Exception("نوع الملف غير مدعوم")

async def process_uploaded_files(client: Client, message: Message, user_id: int):
    if user_id not in user_data or not user_data[user_id].get("files"):
        await message.reply_text("لم يتم العثور على ملفات للمعالجة.")
        return
        
    files = user_data[user_id]["files"]
    github_username = user_data[user_id]["github_username"]
    repo_name = user_data[user_id]["repo_name"]
    
    try:
        await message.reply_text("جاري الاتصال بـ GitHub... 🔗")
        g = Github(GITHUB_TOKEN)
        user = g.get_user()
        token_user = user.login
        if github_username != token_user:
            await message.reply_text(f"⚠️ اسم المستخدم ({github_username}) لا يتطابق مع حساب التوكن ({token_user}). سيتم استخدام حساب التوكن.")
        try:
            repo = user.get_repo(repo_name)
            await message.reply_text(f"تم العثور على المستودع: {repo_name}")
        except GithubException:
            repo = user.create_repo(repo_name, private=False)
            await message.reply_text(f"تم إنشاء مستودع جديد: {repo_name}")
  
        for file_info in files:
            file_path = file_info["path"]
            file_name = file_info["name"]
            
            await message.reply_text(f"جاري معالجة {file_name}... 📦")
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
             
                    if file_name.endswith('.zip'):
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                        await message.reply_text(f"تم تفكيك {file_name} بنجاح.")
                    else:
                    
                        await message.reply_text("نوع الملف RAR غير مدعوم بالكامل. يرجى استخدام ZIP.")
                        continue
                    
               
                    uploaded_count = 0
                    updated_count = 0
                    
                    for root, dirs, files_in_dir in os.walk(temp_dir):
                        for file in files_in_dir:
                            file_path_in_dir = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path_in_dir, temp_dir)
                            
                       
                            async with aiofiles.open(file_path_in_dir, 'rb') as f:
                                content = await f.read()
                            
                      
                            try:
                                content_str = content.decode('utf-8')
                                is_binary = False
                            except UnicodeDecodeError:
                                content_str = content
                                is_binary = True
                            
                            try:
                                if is_binary:
                                
                                    await message.reply_text(f"⚠️ الملف {relative_path} ثنائي وقد لا يتم رفعه بشكل صحيح.")
                                    continue
                                
                             
                                repo.create_file(relative_path, f"Add {relative_path} from {file_name}", content_str)
                                uploaded_count += 1
                            except GithubException as e:
                                if e.status == 422:
                                    try:
                                        
                                        contents = repo.get_contents(relative_path)
                                        repo.update_file(relative_path, f"Update {relative_path} from {file_name}", content_str, contents.sha)
                                        updated_count += 1
                                    except Exception as update_error:
                                        logger.error(f"Error updating file {relative_path}: {update_error}")
                                        await message.reply_text(f"❌ خطأ في تحديث الملف {relative_path}")
                                else:
                                    raise e
                    
                    await message.reply_text(
                        f"✅ تم معالجة {file_name} بنجاح!\n"
                        f"تم رفع {uploaded_count} ملف وتحديث {updated_count} ملف."
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing {file_name}: {e}")
                    await message.reply_text(f"❌ حدث خطأ أثناء معالجة {file_name}: {str(e)}")
        
        repo_url = repo.html_url
        await message.reply_text(
            f"🎉 تم الانتهاء من جميع الملفات بنجاح! ✅\n\n"
            f"يمكنك الوصول إلى ملفاتك من هنا:\n{repo_url}"
        )
        
    except Exception as e:
        logger.error(f"Error in upload process: {e}")
        await message.reply_text(f"حدث خطأ أثناء المعالجة: {str(e)}")
    
    finally:
      
        if user_id in user_data:
            for file_info in user_data[user_id].get("files", []):
                if os.path.exists(file_info["path"]):
                    os.remove(file_info["path"])
            del user_data[user_id]

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    await show_help(client, message)


@app.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
    
        for file_info in user_data[user_id].get("files", []):
            if os.path.exists(file_info["path"]):
                os.remove(file_info["path"])
        del user_data[user_id]
        await message.reply_text("تم إلغاء العملية الحالية.")
    else:
        await message.reply_text("لا توجد عملية جارية لإلغائها.")
"""
• أول فريق مصري متخصص في تطوير بايثون Python   
• القناة #Code الرسميـة الرائدة في تـعليم البرمجة عربيًا 
• جميع الحقوق و النشر محفوظة:  ©️ VEGA™ ₂₀₁₅  
• مطور ومُنشئ المحتوى:  
• @TopVeGa
• @DevVeGa
"""        
if __name__ == "__main__":
    print("البوت يعمل...")
    app.run()