from aiogram import Bot, Dispatcher, executor, types
import sqlite3
from datetime import datetime
import pandas as pd
import os

BOT_TOKEN = "8188791546:AAFcMkHZMpQVonjLcXcz1CVMwCcjv4S0LVE"  # ضع توكن البوت هنا

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------- DATABASE ----------
conn = sqlite3.connect("products.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    photo_file_id TEXT NOT NULL,
    created_at TEXT
)
""")
conn.commit()

# ---------- USER STATES ----------
user_states = {}

# ---------- START ----------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "👋 أهلاً بك\n\n"
        "/add - إضافة منتج\n"
        "/bulk_add - إضافة منتجات متعددة عن طريق الصور (Documents)\n"
        "/stats - إحصائيات\n"
        "/search - البحث عن منتج\n"
        "/category - عرض المنتجات حسب الفئة\n"
        "/edit - تعديل منتج\n"
        "/delete - حذف منتج\n"
        "/edit_category - تعديل اسم فئة\n"
        "/delete_category - حذف فئة\n"
        "/export - تصدير المنتجات\n"
        "/cancel - إلغاء العملية الجارية"
    )

# ---------- ADD ----------
@dp.message_handler(commands=['add'])
async def add_product(message: types.Message):
    user_states[message.from_user.id] = {"step": "name", "data": {}}
    await message.answer("📝 اكتب اسم المنتج:\n\n❌ يمكنك إلغاء العملية في أي وقت: /cancel")

# ---------- BULK ADD ----------
@dp.message_handler(commands=['bulk_add'])
async def bulk_add_start(message: types.Message):
    user_states[message.from_user.id] = {"step": "bulk_category"}
    await message.answer("📁 أرسل الفئة لجميع الصور القادمة:\n\n❌ يمكنك إلغاء العملية في أي وقت: /cancel")

# ---------- SEARCH ----------
@dp.message_handler(commands=['search'])
async def search_product(message: types.Message):
    user_states[message.from_user.id] = {"step": "search"}
    await message.answer("🔍 اكتب اسم المنتج أو رقمه للبحث:\n\n❌ يمكنك إلغاء العملية في أي وقت: /cancel")

# ---------- CATEGORY ----------
@dp.message_handler(commands=['category'])
async def category_list(message: types.Message):
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cursor.fetchall()]
    if not categories:
        await message.answer("❌ لا توجد فئات بعد")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cat in categories:
        keyboard.add(types.KeyboardButton(cat))

    user_states[message.from_user.id] = {"step": "category_select"}
    await message.answer("🗂 اختر الفئة التي تريد عرض المنتجات فيها:", reply_markup=keyboard)

# ---------- EDIT CATEGORY ----------
@dp.message_handler(commands=['edit_category'])
async def edit_category(message: types.Message):
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cursor.fetchall()]
    if not categories:
        await message.answer("❌ لا توجد فئات لتعديلها")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cat in categories:
        keyboard.add(types.KeyboardButton(cat))

    user_states[message.from_user.id] = {"step": "edit_category_select"}
    await message.answer("✏️ اختر الفئة التي تريد تعديل اسمها:", reply_markup=keyboard)

# ---------- DELETE CATEGORY ----------
@dp.message_handler(commands=['delete_category'])
async def delete_category(message: types.Message):
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cursor.fetchall()]
    if not categories:
        await message.answer("❌ لا توجد فئات للحذف")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cat in categories:
        keyboard.add(types.KeyboardButton(cat))

    user_states[message.from_user.id] = {"step": "delete_category_select"}
    await message.answer("🗑 اختر الفئة التي تريد حذفها بالكامل:", reply_markup=keyboard)

# ---------- STATS ----------
@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    await message.answer(f"📊 عدد المنتجات: {count}")

# ---------- EDIT PRODUCT ----------
@dp.message_handler(commands=['edit'])
async def edit_product(message: types.Message):
    user_states[message.from_user.id] = {"step": "edit_ask_code", "data": {}}
    await message.answer("✏️ اكتب رقم المنتج الذي تريد تعديله:\n\n❌ يمكنك إلغاء العملية في أي وقت: /cancel")

# ---------- DELETE PRODUCT ----------
@dp.message_handler(commands=['delete'])
async def delete_product(message: types.Message):
    user_states[message.from_user.id] = {"step": "delete_ask_code"}
    await message.answer("🗑 اكتب رقم المنتج الذي تريد حذفه:\n\n❌ يمكنك إلغاء العملية في أي وقت: /cancel")

# ---------- EXPORT ----------
@dp.message_handler(commands=['export'])
async def export_data(message: types.Message):
    cursor.execute("SELECT name, code, category, photo_file_id, created_at FROM products")
    products = cursor.fetchall()
    if not products:
        await message.answer("❌ لا توجد منتجات لتصديرها")
        return

    df = pd.DataFrame(products, columns=["Name", "Code", "Category", "PhotoFileID", "CreatedAt"])
    csv_file = "products_export.csv"
    excel_file = "products_export.xlsx"

    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    df.to_excel(excel_file, index=False)

    await message.answer_document(open(csv_file, "rb"), caption="📄 ملف CSV للمنتجات")
    await message.answer_document(open(excel_file, "rb"), caption="📊 ملف Excel للمنتجات")

    os.remove(csv_file)
    os.remove(excel_file)

# ---------- CANCEL ----------
@dp.message_handler(commands=['cancel'])
async def cancel_process(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        await message.answer("❌ تم إلغاء العملية الحالية")
    else:
        await message.answer("ℹ️ لا توجد عملية جارية")
    await message.answer(
        "📋 الأوامر المتاحة:\n"
        "/add - إضافة منتج\n"
        "/bulk_add - إضافة منتجات متعددة عن طريق الصور\n"
        "/stats - إحصائيات\n"
        "/search - البحث عن منتج\n"
        "/category - عرض المنتجات حسب الفئة\n"
        "/edit - تعديل منتج\n"
        "/delete - حذف منتج\n"
        "/edit_category - تعديل اسم فئة\n"
        "/delete_category - حذف فئة\n"
        "/export - تصدير المنتجات\n"
        "/cancel - إلغاء العملية الجارية"
    )

# ---------- HANDLE USER INPUT ----------
@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_user_steps(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return
    state = user_states[user_id]
    step = state.get("step")

    # ---------------- ADD PRODUCT ----------------
    if step in ["name", "code", "category", "photo"]:
        if step == "name":
            if not message.text:
                await message.answer("❌ اكتب اسم المنتج كنص")
                return
            state["data"]["name"] = message.text
            state["step"] = "code"
            await message.answer("🔢 اكتب رقم المنتج:")

        elif step == "code":
            if not message.text:
                await message.answer("❌ اكتب رقم المنتج كنص")
                return
            cursor.execute("SELECT id FROM products WHERE code=?", (message.text,))
            if cursor.fetchone():
                await message.answer("❌ هذا الرقم مستخدم مسبقًا، اكتب رقمًا آخر")
                return
            state["data"]["code"] = message.text
            state["step"] = "category"
            await message.answer("🗂 اكتب فئة المنتج:")

        elif step == "category":
            if not message.text:
                await message.answer("❌ اكتب الفئة كنص")
                return
            state["data"]["category"] = message.text
            state["step"] = "photo"
            await message.answer("📸 أرسل صورة المنتج:")

        elif step == "photo":
            if not message.photo:
                await message.answer("❌ الرجاء إرسال صورة فقط")
                return
            photo_file_id = message.photo[-1].file_id
            cursor.execute(
                "INSERT INTO products (name, code, category, photo_file_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (state["data"]["name"], state["data"]["code"], state["data"]["category"], photo_file_id, datetime.now().isoformat())
            )
            conn.commit()
            del user_states[user_id]
            await message.answer_photo(photo_file_id, caption=f"✅ تم حفظ المنتج بنجاح\n🏷 الاسم: {state['data']['name']}\n🔢 الرقم: {state['data']['code']}\n🗂 الفئة: {state['data']['category']}")

    # ---------------- BULK ADD ----------------
    elif step == "bulk_category":
        if not message.text:
            await message.answer("❌ الرجاء إدخال اسم الفئة كنص")
            return
        state["category"] = message.text
        state["step"] = "bulk_images"
        await message.answer(f"📸 الآن أرسل الصور كـ Documents (يمكنك إرسال عدة صور مرة واحدة).\n❌ سيتم حفظ جميع الصور في الفئة: {state['category']}\n❌ يمكنك إلغاء العملية في أي وقت: /cancel")

    elif step == "bulk_images":
        if not message.document or not message.document.mime_type.startswith("image/"):
            await message.answer("❌ الرجاء إرسال الصور كملفات (Documents) فقط لكي يتم حفظ الاسم تلقائيًا.")
            return
        inserted = 0
        skipped = 0
        category = state["category"]
        if isinstance(message.document, list):
            documents = message.document
        else:
            documents = [message.document]
        for doc in documents:
            file_id = doc.file_id
            filename = doc.file_name
            code = filename.split(".")[0]
            try:
                cursor.execute(
                    "INSERT INTO products (name, code, category, photo_file_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    (code, code, category, file_id, datetime.now().isoformat())
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
        conn.commit()
        await message.answer(f"✅ تم إضافة {inserted} منتج/صورة في الفئة: {category}\n⚠️ تم تخطي {skipped} منتج بسبب التكرار")

    # ---------------- SEARCH ----------------
    elif step == "search":
        query = message.text
        if not query:
            await message.answer("❌ الرجاء إدخال نص للبحث")
            return
        cursor.execute("SELECT name, code, category, photo_file_id FROM products WHERE name=? OR code=?", (query, query))
        result = cursor.fetchone()
        if result:
            name, code, category, photo_file_id = result
            await message.answer_photo(photo_file_id, caption=f"🏷 الاسم: {name}\n🔢 الرقم: {code}\n🗂 الفئة: {category}")
        else:
            await message.answer("❌ لم يتم العثور على المنتج")
        del user_states[user_id]

    # ---------------- CATEGORY SELECTION ----------------
    elif step == "category_select":
        category_query = message.text
        await message.answer("✅ تم اختيار الفئة", reply_markup=types.ReplyKeyboardRemove())
        cursor.execute("SELECT name, code, photo_file_id FROM products WHERE category=?", (category_query,))
        results = cursor.fetchall()
        if results:
            for name, code, photo_file_id in results:
                await message.answer_photo(photo_file_id, caption=f"🏷 الاسم: {name}\n🔢 الرقم: {code}\n🗂 الفئة: {category_query}")
        else:
            await message.answer("❌ لا توجد منتجات في هذه الفئة")
        del user_states[user_id]

    # ---------------- EDIT CATEGORY ----------------
    elif step == "edit_category_select":
        selected_category = message.text
        await message.answer(f"📝 اكتب الاسم الجديد للفئة: {selected_category}", reply_markup=types.ReplyKeyboardRemove())
        state["step"] = "edit_category_new_name"
        state["old_category_name"] = selected_category

    elif step == "edit_category_new_name":
        new_name = message.text.strip()
        old_name = state["old_category_name"]
        if not new_name:
            await message.answer("❌ لا يمكن أن يكون الاسم فارغًا")
            return
        cursor.execute("UPDATE products SET category=? WHERE category=?", (new_name, old_name))
        conn.commit()
        await message.answer(f"✅ تم تغيير اسم الفئة '{old_name}' إلى '{new_name}'")
        del user_states[user_id]

    # ---------------- DELETE CATEGORY ----------------
    elif step == "delete_category_select":
        category_to_delete = message.text
        await message.answer(f"⚠️ هل أنت متأكد من حذف جميع المنتجات في الفئة: {category_to_delete}? اكتب 'نعم' للتأكيد أو /cancel للإلغاء")
        state["step"] = "delete_category_confirm"
        state["category_to_delete"] = category_to_delete

    elif step == "delete_category_confirm":
        if message.text.strip() == "نعم":
            category_to_delete = state["category_to_delete"]
            cursor.execute("DELETE FROM products WHERE category=?", (category_to_delete,))
            conn.commit()
            await message.answer(f"✅ تم حذف جميع المنتجات في الفئة: {category_to_delete}", reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer("❌ تم إلغاء الحذف", reply_markup=types.ReplyKeyboardRemove())
        del user_states[user_id]

    # ---------------- PRODUCT EDIT/DELETE (existing code) ----------------
    # (Keep all the previous product edit/delete handlers here)
    # ...

# ---------- RUN ----------
if __name__ == "__main__":
    print("🤖 Bot is running with SQLite...")
    executor.start_polling(dp)
