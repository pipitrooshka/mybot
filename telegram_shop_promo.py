from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import json
import os

# ========== НАЛАШТУВАННЯ ==========
TOKEN = '8397736954:AAF-c6OKcT2ftYAZIopBIA9h7XjkYjyO1U4'
ADMIN_ID = 747946982  # Ваш Telegram ID

# Стани для ConversationHandler
PRODUCT_NAME, PRODUCT_PRICE, PRODUCT_DESC, PRODUCT_IMAGE = range(4)
EDIT_FIELD, EDIT_VALUE = range(4, 6)
EDIT_PROMO = 6

# Файли для збереження
PRODUCTS_FILE = 'products.json'
PROMO_FILE = 'promo.json'

# ========== ТОВАРИ ==========
def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for pid, p in data.items():
            if 'hidden' not in p:
                p['hidden'] = False
        return data
    return {}

def save_products():
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(PRODUCTS, f, ensure_ascii=False, indent=2)

# ========== АКЦІЇ ==========
def load_promo():
    if os.path.exists(PROMO_FILE):
        with open(PROMO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'text': '🎉 ДІЮЧІ АКЦІЇ:\n\n'
                '🔥 Знижка 20% на всі рідини!\n'
                '🎁 При замовленні від €50 - подарунок!\n'
                '⚡️ Безкоштовна доставка від €30\n\n'
    }

def save_promo():
    with open(PROMO_FILE, 'w', encoding='utf-8') as f:
        json.dump(PROMO, f, ensure_ascii=False, indent=2)

PRODUCTS = load_products()
PROMO = load_promo()

# Кошики користувачів
user_carts = {}

# ========== КОМАНДИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("🛍 Каталог товарів", callback_data='catalog')],
        [InlineKeyboardButton("🛒 Мій кошик", callback_data='cart')],
        [InlineKeyboardButton("🎉 Діючі акції", callback_data='promo')],
        [InlineKeyboardButton("📢 Наш канал", url='https://t.me/cloud_sk1')],
        [InlineKeyboardButton("ℹ️ Про нас", callback_data='about')]
    ]
    
    # Додаємо кнопку адмін-панелі тільки для адміністратора
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Адмін-панель", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '👋 Вітаємо в нашому магазині!\n\n'
        'Оберіть дію:',
        reply_markup=reply_markup
    )

# ========== АДМІН-ПАНЕЛЬ ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Перевірка прав адміністратора
    if user_id != ADMIN_ID:
        await query.answer("❌ У вас немає доступу до адмін-панелі!")
        return
    
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Додати товар", callback_data='admin_add')],
        [InlineKeyboardButton("✏️ Редагувати товар", callback_data='admin_edit_list')],
        [InlineKeyboardButton("🗑 Видалити товар", callback_data='admin_delete_list')],
        [InlineKeyboardButton("� Керувати видимістю", callback_data='admin_visibility')],
        [InlineKeyboardButton("� Список товарів", callback_data='admin_list')],
        [InlineKeyboardButton("🎉 Змінити текст акцій", callback_data='admin_edit_promo')],
        [InlineKeyboardButton("🔙 Головне меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        '⚙️ АДМІН-ПАНЕЛЬ\n\n'
        f'Всього товарів: {len(PRODUCTS)}\n\n'
        'Виберіть дію:',
        reply_markup=reply_markup
    )

# ========== АКЦІЇ (КОРИСТУВАЧ) ==========
async def show_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Головне меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        PROMO['text'],
        reply_markup=reply_markup
    )

# ========== РЕДАГУВАННЯ АКЦІЙ (АДМІН) ==========
async def admin_edit_promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        '🎉 РЕДАГУВАННЯ АКЦІЙ\n\n'
        f'Поточний текст:\n{PROMO["text"]}\n\n'
        '📝 Надішліть новий текст акцій:\n\n'
        'Або /cancel для скасування'
    )
    
    return EDIT_PROMO

async def admin_edit_promo_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    
    PROMO['text'] = new_text
    save_promo()
    
    keyboard = [
        [InlineKeyboardButton("🎉 Переглянути акції", callback_data='promo')],
        [InlineKeyboardButton("🔙 Адмін-панель", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '✅ Текст акцій успішно оновлено!\n\n'
        'Нова версія:\n' + new_text,
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

# ========== СПИСОК ТОВАРІВ (АДМІН) ==========
async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not PRODUCTS:
        text = '📋 Список товарів порожній'
    else:
        text = '📋 СПИСОК ТОВАРІВ:\n\n'
        for product_id, product in PRODUCTS.items():
            status = '⛔️ приховано' if product.get('hidden') else '✅ видно'
            text += f"ID: {product_id}\n"
            text += f"📦 {product['name']} ({status})\n"
            text += f"💰 €{product['price']}\n"
            text += f"───────────────\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад до адмін-панелі", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

# ========== ДОДАТИ ТОВАР ==========
async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        '➕ ДОДАВАННЯ НОВОГО ТОВАРУ\n\n'
        '📝 Крок 1/4: Введіть назву товару\n\n'
        'Або /cancel для скасування'
    )
    
    return PRODUCT_NAME

async def admin_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product'] = {'name': update.message.text}
    
    await update.message.reply_text(
        '💰 Крок 2/4: Введіть ціну товару (тільки число)\n\n'
        'Приклад: 150'
    )
    
    return PRODUCT_PRICE

async def admin_add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text)
        context.user_data['new_product']['price'] = price
        
        await update.message.reply_text(
            '📝 Крок 3/4: Введіть опис товару'
        )
        
        return PRODUCT_DESC
    except ValueError:
        await update.message.reply_text(
            '❌ Помилка! Введіть ціну числом.\n\n'
            'Приклад: 150'
        )
        return PRODUCT_PRICE

async def admin_add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['description'] = update.message.text
    
    await update.message.reply_text(
        '🖼 Крок 4/4: Надішліть посилання на зображення\n\n'
        'Приклад: https://example.com/image.jpg\n\n'
        'Або напишіть "skip" щоб пропустити'
    )
    
    return PRODUCT_IMAGE

async def admin_add_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_url = update.message.text
    
    if image_url.lower() != 'skip':
        context.user_data['new_product']['image'] = image_url
    else:
        context.user_data['new_product']['image'] = 'https://via.placeholder.com/800x600?text=No+Image'
    context.user_data['new_product']['hidden'] = False
    
    # Генеруємо новий ID
    new_id = str(max([int(k) for k in PRODUCTS.keys()]) + 1) if PRODUCTS else '1'
    
    # Додаємо товар
    PRODUCTS[new_id] = context.user_data['new_product']
    save_products()
    
    product = PRODUCTS[new_id]
    
    keyboard = [
        [InlineKeyboardButton("➕ Додати ще товар", callback_data='admin_add')],
        [InlineKeyboardButton("🔙 Адмін-панель", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f'✅ Товар успішно додано!\n\n'
        f'ID: {new_id}\n'
        f'📦 {product["name"]}\n'
        f'💰 €{product["price"]}\n'
        f'📝 {product["description"]}',
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

# ========== РЕДАГУВАТИ ТОВАР ==========
async def admin_visibility_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not PRODUCTS:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('❌ Немає товарів для керування видимістю', reply_markup=reply_markup)
        return
    keyboard = []
    for product_id, product in PRODUCTS.items():
        if product.get('hidden'):
            keyboard.append([InlineKeyboardButton(
                f"👁 Повернути: {product['name']}",
                callback_data=f'admin_unhide_{product_id}'
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                f"🙈 Приховати: {product['name']}",
                callback_data=f'admin_hide_{product_id}'
            )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('👁 КЕРУВАННЯ ВИДИМІСТЮ\n\nВиберіть дію для товару:', reply_markup=reply_markup)

async def admin_hide_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id = query.data.split('_')[2]
    if product_id in PRODUCTS:
        PRODUCTS[product_id]['hidden'] = True
        save_products()
        await query.answer("✅ Товар приховано")
    await admin_visibility_list(update, context)

async def admin_unhide_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id = query.data.split('_')[2]
    if product_id in PRODUCTS:
        PRODUCTS[product_id]['hidden'] = False
        save_products()
        await query.answer("✅ Товар повернуто")
    await admin_visibility_list(update, context)

async def admin_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.split('_')[2]
    product = PRODUCTS[product_id]
    
    context.user_data['editing_product_id'] = product_id
    
    keyboard = [
        [InlineKeyboardButton("📝 Назва", callback_data=f'edit_field_name_{product_id}')],
        [InlineKeyboardButton("💰 Ціна", callback_data=f'edit_field_price_{product_id}')],
        [InlineKeyboardButton("📄 Опис", callback_data=f'edit_field_description_{product_id}')],
        [InlineKeyboardButton("🖼 Зображення", callback_data=f'edit_field_image_{product_id}')],
        [InlineKeyboardButton(("👁 Повернути" if product.get('hidden') else "🙈 Приховати"), callback_data=(f"admin_unhide_{product_id}" if product.get('hidden') else f"admin_hide_{product_id}"))],
        [InlineKeyboardButton("🔙 Назад", callback_data='admin_edit_list')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f'✏️ РЕДАГУВАННЯ: {product["name"]}\n\n'
        f'📦 Назва: {product["name"]}\n'
        f'💰 Ціна: €{product["price"]}\n'
        f'📝 Опис: {product["description"]}\n'
        f'Статус: {"⛔️ приховано" if product.get('hidden') else "✅ видно"}\n\n'
        'Що бажаєте змінити?',
        reply_markup=reply_markup
    )

async def admin_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    field = data_parts[2]
    product_id = data_parts[3]
    
    context.user_data['editing_field'] = field
    context.user_data['editing_product_id'] = product_id
    
    field_names = {
        'name': 'назву',
        'price': 'ціну',
        'description': 'опис',
        'image': 'посилання на зображення'
    }
    
    await query.edit_message_text(
        f'✏️ Редагування поля: {field_names[field]}\n\n'
        f'Поточне значення: {PRODUCTS[product_id][field]}\n\n'
        f'Введіть нове значення:\n\n'
        'Або /cancel для скасування'
    )
    
    return EDIT_VALUE

async def admin_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data['editing_field']
    product_id = context.user_data['editing_product_id']
    new_value = update.message.text
    
    # Перевірка для ціни
    if field == 'price':
        try:
            new_value = float(new_value)
        except ValueError:
            await update.message.reply_text(
                '❌ Помилка! Ціна має бути числом.\n\n'
                'Спробуйте ще раз:'
            )
            return EDIT_VALUE
    
    # Оновлюємо товар
    PRODUCTS[product_id][field] = new_value
    save_products()
    
    product = PRODUCTS[product_id]
    
    keyboard = [
        [InlineKeyboardButton("✏️ Редагувати ще", callback_data=f'admin_edit_{product_id}')],
        [InlineKeyboardButton("🔙 Адмін-панель", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f'✅ Товар успішно оновлено!\n\n'
        f'📦 {product["name"]}\n'
        f'💰 €{product["price"]}\n'
        f'📝 {product["description"]}',
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

# ========== ВИДАЛИТИ ТОВАР ==========
async def admin_delete_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not PRODUCTS:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            '❌ Немає товарів для видалення',
            reply_markup=reply_markup
        )
        return
    
    keyboard = []
    for product_id, product in PRODUCTS.items():
        status = '⛔️' if product.get('hidden') else '✅'
        keyboard.append([InlineKeyboardButton(
            f"🗑 {product['name']} {status} (€{product['price']})",
            callback_data=f'admin_delete_{product_id}'
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        '🗑 ВИДАЛЕННЯ ТОВАРУ\n\n'
        '⚠️ Виберіть товар для видалення:',
        reply_markup=reply_markup
    )

async def admin_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    product_id = query.data.split('_')[2]
    product_name = PRODUCTS[product_id]['name']
    
    # Видаляємо товар
    del PRODUCTS[product_id]
    save_products()
    
    await query.answer(f"✅ {product_name} видалено!")
    
    keyboard = [
        [InlineKeyboardButton("🗑 Видалити ще", callback_data='admin_delete_list')],
        [InlineKeyboardButton("🔙 Адмін-панель", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f'✅ Товар "{product_name}" успішно видалено!\n\n'
        f'Залишилось товарів: {len(PRODUCTS)}',
        reply_markup=reply_markup
    )

# ========== СКАСУВАННЯ ==========
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔙 Адмін-панель", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '❌ Операцію скасовано',
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

# ========== КАТАЛОГ ==========
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not PRODUCTS:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            '❌ Каталог порожній\n\nТовари ще не додані',
            reply_markup=reply_markup
        )
        return
    
    keyboard = []
    for product_id, product in PRODUCTS.items():
        if product.get('hidden'):
            continue
        keyboard.append([InlineKeyboardButton(
            f"{product['name']} - €{product['price']}",
            callback_data=f'product_{product_id}'
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = '🛍 Наш каталог:\n\nВиберіть товар для перегляду:'
    
    try:
        # Якщо немає видимих товарів
        visible_buttons_count = len(keyboard) - 1
        if visible_buttons_count == 0:
            await query.edit_message_text(
                '❌ Каталог порожній\n\nТовари тимчасово недоступні',
                reply_markup=reply_markup
            )
            return
        await query.edit_message_text(text, reply_markup=reply_markup)
    except:
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=('❌ Каталог порожній\n\nТовари тимчасово недоступні' if (len(keyboard) - 1) == 0 else text),
            reply_markup=reply_markup
        )

# ========== ТОВАР ==========
async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.split('_')[1]
    
    if product_id not in PRODUCTS:
        await query.answer("❌ Товар не знайдено")
        return
    
    product = PRODUCTS[product_id]
    if product.get('hidden'):
        await query.answer("❌ Товар тимчасово недоступний")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Додати в кошик", callback_data=f'add_{product_id}')],
        [InlineKeyboardButton("🔙 Назад до каталогу", callback_data='catalog')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"{product['name']}\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Ціна: €{product['price']}"
    )
    
    try:
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=product['image'],
            caption=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Помилка завантаження фото: {e}")
        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"{text}\n\n⚠️ (Фото тимчасово недоступне)",
                reply_markup=reply_markup
            )
        except:
            await query.edit_message_text(text, reply_markup=reply_markup)

# ========== ДОДАТИ В КОШИНУ ==========
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    product_id = query.data.split('_')[1]
    if PRODUCTS.get(product_id, {}).get('hidden'):
        await query.answer("❌ Товар тимчасово недоступний")
        return
    await query.answer("✅ Товар додано в кошик!")
    if user_id not in user_carts:
        user_carts[user_id] = []
    user_carts[user_id].append(product_id)
    
    product = PRODUCTS[product_id]
    keyboard = [
        [InlineKeyboardButton("🛒 Перейти в кошик", callback_data='cart')],
        [InlineKeyboardButton("🔙 Продовжити покупки", callback_data='catalog')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"✅ {product['name']} додано в кошик!\n\n"
        f"Що бажаєте зробити далі?"
    )
    
    try:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=reply_markup
        )
    except:
        await query.edit_message_text(text, reply_markup=reply_markup)

# ========== КОРЗИНАААмі ==========
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        keyboard = [[InlineKeyboardButton("🛍 Перейти до каталогу", callback_data='catalog')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            '🛒 Ваш кошик порожній\n\n'
            'Додайте товари з каталогу!',
            reply_markup=reply_markup
        )
        return
    
    cart_items = {}
    for product_id in cart:
        if product_id in PRODUCTS:
            cart_items[product_id] = cart_items.get(product_id, 0) + 1
    
    text = '🛒 Ваш кошик:\n\n'
    total = 0
    
    for product_id, quantity in cart_items.items():
        product = PRODUCTS[product_id]
        subtotal = product['price'] * quantity
        total += subtotal
        text += f"{product['name']}\n"
        text += f"   {quantity} шт. × €{product['price']} = €{subtotal}\n\n"
    
    text += f"💰 Загалом: €{total}"
    
    keyboard = [
        [InlineKeyboardButton("✅ Оформити замовлення", callback_data='checkout')],
        [InlineKeyboardButton("✏️ Редагувати кошик", callback_data='edit_cart')],
        [InlineKeyboardButton("🗑 Очистити кошик", callback_data='clear_cart')],
        [InlineKeyboardButton("🔙 Продовжити покупки", callback_data='catalog')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

# ========== РЕДАГУВАТИ КОШИНУ ==========
async def edit_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='cart')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            '🛒 Кошик порожній!',
            reply_markup=reply_markup
        )
        return
    
    cart_items = {}
    for product_id in cart:
        if product_id in PRODUCTS:
            cart_items[product_id] = cart_items.get(product_id, 0) + 1
    
    text = '✏️ Редагування кошини:\n\nВиберіть товар для видалення:\n\n'
    
    keyboard = []
    for product_id, quantity in cart_items.items():
        product = PRODUCTS[product_id]
        keyboard.append([InlineKeyboardButton(
            f"❌ {product['name']} ({quantity} шт.)",
            callback_data=f'remove_{product_id}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад до кошини", callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

# ========== ВИДАЛИТИ ТОВАР ==========
async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    user_id = update.effective_user.id
    product_id = query.data.split('_')[1]
    
    if user_id in user_carts and product_id in user_carts[user_id]:
        user_carts[user_id].remove(product_id)
        product = PRODUCTS[product_id]
        await query.answer(f"✅ {product['name']} видалено")
    else:
        await query.answer("❌ Товар не знайдено")
    
    await edit_cart(update, context)

# ========== ОЧИСТИТИ КОШИНУ ==========
async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🗑 Кошик очищено")
    
    user_id = update.effective_user.id
    user_carts[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("🛍 Перейти до каталогу", callback_data='catalog')],
        [InlineKeyboardButton("🔙 Головне меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        '🗑 Кошик очищено!\n\n'
        'Бажаєте продовжити покупки?',
        reply_markup=reply_markup
    )

# ========== ОФОРМЛЕННЯ ЗАМОВЛЕННЯ ==========
async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user = update.effective_user
    cart = user_carts.get(user_id, [])
    
    if not cart:
        await query.edit_message_text("❌ Кошик порожній!")
        return
    
    if not user.username:
        keyboard = [
            [InlineKeyboardButton("📞 Зв'язатися з менеджером", url='https://t.me/vape_cloud_sk_admin')],
            [InlineKeyboardButton("🔙 Назад до кошини", callback_data='cart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ У вас відсутній username!\n\n"
            "Для оформлення замовлення нам потрібен ваш username (наприклад @yourname), "
            "щоб менеджер міг з вами зв'язатися.\n\n"
            "📱 Як встановити username:\n"
            "- Відкрийте Налаштування Telegram\n"
            "- Встановіть Username\n\n"
            "Або зв'яжіться з нашим менеджером напряму:",
            reply_markup=reply_markup
        )
        return
    
    cart_items = {}
    for product_id in cart:
        if product_id in PRODUCTS:
            cart_items[product_id] = cart_items.get(product_id, 0) + 1
    
    total = sum(PRODUCTS[pid]['price'] * qty for pid, qty in cart_items.items())
    
    client_text = (
        f"✅ Ваше замовлення прийнято!\n\n"
        f"Номер замовлення: #{user_id}{len(cart)}\n"
        f"Сума: €{total}\n\n"
        f"📞 Наш менеджер зв'яжеться з вами найближчим часом!\n\n"
        f"Дякуємо за замовлення! 🎉"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Головне меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(client_text, reply_markup=reply_markup)
    
    # Повідомлення адміністратору
    admin_text = (
        f"🔔 НОВЕ ЗАМОВЛЕННЯ!\n\n"
        f"👤 Клієнт: @{user.username or 'немає username'}\n"
        f"🆔 ID: {user_id}\n"
        f"📱 Ім'я: {user.first_name} {user.last_name or ''}\n\n"
        f"🛒 Замовлення:\n"
    )
    
    for product_id, quantity in cart_items.items():
        product = PRODUCTS[product_id]
        subtotal = product['price'] * quantity
        admin_text += f"• {product['name']}\n"
        admin_text += f"  {quantity} шт. × €{product['price']} = €{subtotal}\n\n"
    
    admin_text += f"💰 ЗАГАЛОМ: €{total}\n\n"
    admin_text += f"Номер замовлення: #{user_id}{len(cart)}"
    
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        print(f"Помилка відправки адміну: {e}")
    
    user_carts[user_id] = []

# ========== ПРО НАС ==========
async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Головне меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        'ℹ️ Про наш магазин\n\n'
        'Магазин cloud.sk з найкращим асортиментом в Жиліні!\n'
        '⏰ Працюємо 24/7\n'
        '🚚 Самовивіз в м.Жиліна та доставка по Словаччині!\n'
        '📞 Контакти @vape_cloud_sk_admin\n\n'
        'Бажаємо вдалих покупок! 😋',
        reply_markup=reply_markup
    )

# ========== НАЗАД ==========
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton("🛍 Каталог товарів", callback_data='catalog')],
        [InlineKeyboardButton("🛒 Мій кошик", callback_data='cart')],
        [InlineKeyboardButton("🎉 Діючі акції", callback_data='promo')],
        [InlineKeyboardButton("📢 Наш канал", url='https://t.me/cloud_sk1')],
        [InlineKeyboardButton("ℹ️ Про нас", callback_data='about')]
    ]
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Адмін-панель", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        '👋 Головне меню\n\n'
        'Оберіть дію:',
        reply_markup=reply_markup
    )

# ========== ОБРОБНИК CALLBACK ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    
    # Перевірка доступу до адмін-функцій
    if data.startswith('admin_') and user_id != ADMIN_ID:
        await query.answer("❌ У вас немає доступу!")
        return
    
    if data == 'catalog':
        await show_catalog(update, context)
    elif data == 'cart':
        await show_cart(update, context)
    elif data == 'promo':
        await show_promo(update, context)
    elif data == 'about':
        await show_about(update, context)
    elif data == 'back_to_menu':
        await back_to_menu(update, context)
    elif data == 'admin_panel':
        await admin_panel(update, context)
    elif data == 'admin_list':
        await admin_list_products(update, context)
    elif data == 'admin_visibility':
        await admin_visibility_list(update, context)
    elif data == 'admin_edit_list':
        await admin_edit_list(update, context)
    elif data == 'admin_delete_list':
        await admin_delete_list(update, context)
    elif data.startswith('admin_edit_') and not data.startswith('admin_edit_list') and not data.startswith('admin_edit_promo'):
        await admin_edit_product(update, context)
    elif data.startswith('edit_field_'):
        await admin_edit_field(update, context)
    elif data.startswith('admin_delete_') and not data.startswith('admin_delete_list'):
        await admin_delete_product(update, context)
    elif data.startswith('admin_hide_'):
        await admin_hide_product(update, context)
    elif data.startswith('admin_unhide_'):
        await admin_unhide_product(update, context)
    elif data.startswith('product_'):
        await show_product(update, context)
    elif data.startswith('add_'):
        await add_to_cart(update, context)
    elif data == 'edit_cart':
        await edit_cart(update, context)
    elif data.startswith('remove_'):
        await remove_from_cart(update, context)
    elif data == 'clear_cart':
        await clear_cart(update, context)
    elif data == 'checkout':
        await checkout(update, context)

# ========== ГОЛОВНА ФУНКЦІЯ ==========
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Conversation handler для додавання товару
    add_product_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_start, pattern='^admin_add$')],
        states={
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_name)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_price)],
            PRODUCT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_desc)],
            PRODUCT_IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_image)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Conversation handler для редагування товару
    edit_product_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_edit_field, pattern='^edit_field_')],
        states={
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_value)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Conversation handler для редагування акцій
    edit_promo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_edit_promo_start, pattern='^admin_edit_promo$')],
        states={
            EDIT_PROMO: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_promo_save)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_product_handler)
    app.add_handler(edit_product_handler)
    app.add_handler(edit_promo_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print('🤖 Бот запущено!')
    print(f'📊 Товарів в каталозі: {len(PRODUCTS)}')
    print(f'👤 Адмін ID: {ADMIN_ID}')
    app.run_polling()

if __name__ == '__main__':
    main()
