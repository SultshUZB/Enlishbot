import os
import random
import sqlite3
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokenini environment'dan olish
BOT_TOKEN = os.environ.get('8538557025:AAHxyGoWwPnjnMIXzwngx8_CZQMBz9yM0Eg')

# Database setup - Railway uchun
def get_db_connection():
    return sqlite3.connect('vocab_bot.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            chat_id INTEGER,
            username TEXT,
            first_name TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    
    # Test natijalari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            unit_number INTEGER,
            score INTEGER,
            total_questions INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Faol testlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_tests (
            chat_id INTEGER PRIMARY KEY,
            unit_number INTEGER,
            question_index INTEGER,
            start_time DATETIME,
            questions_data TEXT
        )
    ''')
    
    # User javoblari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_answers (
            user_id INTEGER,
            chat_id INTEGER,
            question_index INTEGER,
            answer TEXT,
            is_correct BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, chat_id, question_index)
        )
    ''')
    
    conn.commit()
    conn.close()

# Lug'at ma'lumotlari - BARCHA 30 UNIT
VOCABULARY = {
    1: {
        'afraid': 'qo\'rqmoq', 'agree': 'rozi bo\'lmoq', 'angry': 'jahldor', 
        'arrive': 'yetib kelmoq', 'attack': 'hujum qilmoq', 'bottom': 'tagi osti',
        'clever': 'aqilli', 'cruel': 'shafqatsiz', 'finally': 'nihoyat', 
        'hide': 'yashirmoq', 'hunt': 'ovlamoq', 'lot': 'ko\'p', 'middle': 'o\'rta',
        'moment': 'lahza', 'pleased': 'mamnun', 'promise': 'va\'da bermoq',
        'reply': 'javob bermoq', 'safe': 'xavfsiz', 'trick': 'hiyla', 'well': 'yaxshi'
    },
    2: {
        'adventure': 'sarguzasht', 'approach': 'yaqinlashmoq', 'carefully': 'ehtiyotkorlik bilan',
        'chemical': 'kimyoviy', 'create': 'yaratmoq', 'evil': 'yovuzlik',
        'experiment': 'tajriba', 'kill': 'o\'ldirmoq', 'laboratory': 'laboratoriya',
        'laugh': 'kulmoq', 'loud': 'baland ovozda', 'nervous': 'asabiy',
        'noise': 'shovqin', 'project': 'loyiha', 'scare': 'qo\'rqitmoq',
        'secret': 'sir', 'shout': 'baqirmoq', 'smell': 'hid', 'terrible': 'qo\'rqinchli',
        'worse': 'yomonroq'
    },
    3: {
        'alien': 'begona', 'among': 'orasida', 'chart': 'grafik/jadval',
        'cloud': 'bulut', 'comprehend': 'tushunmoq', 'describe': 'ta\'riflamoq',
        'ever': 'qachon bo\'lsa ham', 'fail': 'muvaffaqiyatsizlikka uchramoq',
        'friendly': 'do\'stona', 'grade': 'baho', 'instead': 'o\'rniga',
        'library': 'kutubxona', 'planet': 'sayyora', 'report': 'hisobot',
        'several': 'bir necha', 'solve': 'hal qilmoq', 'suddenly': 'to\'satdan',
        'suppose': 'faraz qilmoq', 'universe': 'olam', 'view': 'ko\'rinish'
    },
    4: {
        'appropriate': 'muvofiq', 'avoid': 'oldini olmoq', 'behave': 'o\'zini tutmoq',
        'calm': 'sokin', 'concern': 'tashvishlanmoq', 'content': 'mamnun',
        'expect': 'kutmoq', 'frequently': 'tez-tez', 'habit': 'odat',
        'instruct': 'ko\'rsatma bermoq', 'issue': 'masala', 'none': 'hech biri',
        'patient': 'sabrli', 'positive': 'ijobiy', 'punish': 'jazolamoq',
        'represent': 'vakillik qilmoq', 'shake': 'silkitmoq', 'spread': 'tarqalmoq',
        'stroll': 'sayr qilmoq', 'village': 'qishloq'
    },
    5: {
        'aware': 'xabardor', 'badly': 'yomon', 'belong': 'tegishli bo\'lmoq',
        'continue': 'davom etmoq', 'error': 'xato', 'experience': 'tajriba',
        'field': 'maydon', 'hurt': 'jarohat qilmoq', 'judgment': 'hukm/baho',
        'likely': 'ehtimol', 'normal': 'oddiy', 'rare': 'noyob',
        'relax': 'rohatlanmoq', 'request': 'so\'ramoq', 'reside': 'yashamoq',
        'result': 'natija', 'roll': 'dumalamoq', 'since': 'chunki',
        'visible': 'ko\'rinadigan', 'wild': 'yovvoyi'
    },
    6: {
        'advantage': 'afzallik', 'cause': 'sabab', 'choice': 'tanlov',
        'community': 'jamoa', 'dead': 'o\'lik', 'distance': 'masofa',
        'escape': 'qochmoq', 'face': 'yuz', 'follow': 'amal qilmoq',
        'fright': 'qo\'rquv', 'ghost': 'arvoh', 'individual': 'shaxs',
        'pet': 'uy hayvoni', 'reach': 'erishmoq', 'return': 'qaytmoq',
        'survive': 'omon qolmoq', 'upset': 'xafa', 'voice': 'ovoz',
        'weather': 'ob-havo', 'wise': 'dono'
    },
    7: {
        'allow': 'rusat bermoq', 'announce': 'e\'lon qilmoq', 'beside': 'yonida',
        'challenge': 'qiyinchilik', 'claim': 'da\'vo qilmoq', 'condition': 'holat',
        'contribute': 'hissa qo\'shmoq', 'difference': 'farq', 'divide': 'bo\'lmoq',
        'expert': 'mutaxassis', 'famous': 'mashhur', 'force': 'kuch',
        'harm': 'zarar', 'lay': 'yotqizmoq', 'peace': 'tinchlik',
        'prince': 'shahzoda', 'protect': 'himoya qilmoq', 'sense': 'his',
        'sudden': 'to\'satdan', 'therefore': 'shuning uchun'
    },
    8: {
        'accept': 'qabul qilmoq', 'arrange': 'tartibga solmoq', 'attend': 'qatnashmoq',
        'balance': 'muvozanat', 'contrast': 'farq', 'encourage': 'rag\'batlantirmoq',
        'familiar': 'tanish', 'grab': 'changallamoq', 'hang': 'osib qo\'ymoq',
        'huge': 'katta', 'necessary': 'zarur', 'pattern': 'naqsh, tartib',
        'propose': 'taklif qilmoq', 'purpose': 'maqsad', 'release': 'ozod qilmoq',
        'require': 'talab qilmoq', 'single': 'yakka', 'success': 'muvaffaqiyat',
        'tear': 'ko\'z yoshi, yirtmoq', 'theory': 'nazariya'
    },
    9: {
        'against': 'qarshi', 'beach': 'sohil', 'damage': 'zarar',
        'discover': 'kashf qilmoq', 'emotion': 'hissiyot', 'fix': 'tuzatmoq',
        'frank': 'samimiy', 'identify': 'aniqlamoq', 'island': 'orol',
        'ocean': 'okean', 'perhaps': 'balki', 'pleasant': 'yoqimli',
        'prevent': 'oldini olmoq', 'rock': 'tosh', 'save': 'asramoq',
        'step': 'qadam', 'still': 'hali ham', 'taste': 'ta\'m, tatib ko\'rmoq',
        'throw': 'otmoq', 'wave': 'to\'lqin'
    },
    10: {
        'benefit': 'foyda', 'certain': 'aniq', 'chance': 'imkoniyat',
        'effect': 'ta\'sir', 'essential': 'muhim', 'far': 'uzoq',
        'focus': 'diqqat markazi', 'function': 'vazifa', 'grass': 'o\'t',
        'guard': 'qo\'riqchi', 'image': 'rasm', 'immediate': 'darhol',
        'primary': 'asosiy', 'proud': 'mag\'rur', 'remain': 'qolmoq',
        'rest': 'dam olmoq', 'separate': 'alohida', 'site': 'joy',
        'tail': 'dum', 'trouble': 'muammo'
    },
    11: {
        'anymore': 'endi qaytib', 'asleep': 'uyquda', 'berry': 'meva',
        'collect': 'to\'plamoq', 'compete': 'raqobatlashmoq', 'conversation': 'suhbat',
        'creature': 'jonzot', 'decision': 'qaror', 'either': 'yoki',
        'forest': 'o\'rmon', 'ground': 'yer', 'introduce': 'tanishtirmoq',
        'marry': 'turmush qurmoq', 'prepare': 'tayyorlamoq', 'sail': 'suzmoq',
        'serious': 'jiddiy', 'spend': 'sarflamoq', 'strange': 'g\'alati',
        'truth': 'haqiqat', 'wake': 'uyg\'otmoq'
    },
    12: {
        'alone': 'yolg\'iz', 'apartment': 'xonadon', 'article': 'maqola',
        'artist': 'rassom', 'attitude': 'munosabat', 'compare': 'solishtirmoq',
        'judge': 'hukm qilmoq', 'magazine': 'jurnal', 'material': 'material',
        'meal': 'ovqat', 'method': 'usul', 'neighbor': 'qo\'shni',
        'professional': 'professional', 'profit': 'foyda', 'quality': 'sifat',
        'shape': 'shakl', 'space': 'bo\'shliq', 'stair': 'zina',
        'symbol': 'belgi', 'thin': 'ingichka'
    },
    13: {
        'blood': 'qon', 'burn': 'kuymoq', 'cell': 'hujayra, panjara',
        'contain': 'o\'z ichiga olmoq', 'correct': 'to\'g\'ri', 'crop': 'ekin',
        'demand': 'talab', 'equal': 'teng', 'feed': 'boqmoq', 'hole': 'teshik',
        'increase': 'o\'smoq', 'lord': 'lord', 'owe': 'qarzdor',
        'position': 'o\'rin', 'raise': 'oshirmoq', 'responsible': 'mas\'ul',
        'sight': 'ko\'rish', 'spot': 'dog\', joy', 'structure': 'tuzilish',
        'whole': 'butun'
    },
    14: {
        'coach': 'murabbiy', 'control': 'boshqaruv', 'description': 'tavsif',
        'direct': 'to\'g\'ridan-to\'g\'ri', 'exam': 'imtihon', 'example': 'misol',
        'limit': 'chegara', 'local': 'mahalliy', 'magical': 'sehrli',
        'mail': 'pochta', 'novel': 'roman', 'outline': 'reja', 'poet': 'shoir',
        'print': 'bosib chiqarmoq', 'scene': 'sahna', 'sheet': 'varaq',
        'silly': 'ahmoqona', 'store': 'do\'kon, saqlamoq', 'suffer': 'azoblanmoq',
        'technology': 'texnologiya'
    },
    15: {
        'across': 'kesib', 'breathe': 'nafas olmoq', 'characteristic': 'xususiyat',
        'consume': 'iste\'mol qilmoq', 'excite': 'hayajonlantirmoq', 'extreme': 'haddan tashqari',
        'fear': 'qo\'rquv', 'fortunate': 'baxtli', 'happen': 'sodir bo\'lmoq',
        'length': 'uzunlik', 'mistake': 'xato', 'observe': 'kuzatmoq',
        'opportunity': 'imkoniyat', 'prize': 'sovrin', 'race': 'irq, poyga',
        'realize': 'tushunmoq', 'respond': 'javob bermoq', 'risk': 'xavf',
        'wonder': 'hayron bo\'lmoq', 'yet': 'hali'
    },
    16: {
        'academy': 'akademiya', 'ancient': 'qadimiy', 'board': 'taxta',
        'century': 'asr', 'clue': 'ko\'rsatma, ma\'lumot', 'concert': 'konsert',
        'county': 'graflik', 'dictionary': 'lug\'at', 'exist': 'mavjud',
        'flat': 'tekis', 'gentleman': 'janob', 'hidden': 'yashirin',
        'maybe': 'balki', 'officer': 'ofitser', 'original': 'original',
        'pound': 'funt, og\'irmoq', 'process': 'jarayon', 'publish': 'nashr etmoq',
        'theater': 'teatr', 'wealth': 'boylik'
    },
    17: {
        'appreciate': 'qadrlamoq', 'available': 'mavjud', 'beat': 'urmoq',
        'bright': 'yorqin', 'celebrate': 'nishonlamoq', 'determine': 'aniqlamoq',
        'disappear': 'yo\'qolmoq', 'else': 'yana boshqa', 'fair': 'adolatli',
        'flow': 'oqim', 'forward': 'oldinga', 'hill': 'tepalik',
        'level': 'daraja', 'lone': 'yolg\'iz', 'puddle': 'ko\'lmak',
        'response': 'javob', 'season': 'mavsum', 'solution': 'yechim',
        'waste': 'chiqindi', 'whether': 'yoki'
    },
    18: {
        'argue': 'bahslashmoq', 'communicate': 'muloqot qilmoq', 'crowd': 'olomon',
        'depend': 'qaram bo\'lmoq', 'dish': 'ovqat', 'empty': 'bo\'sh',
        'exact': 'aniq', 'fresh': 'yangil', 'gather': 'to\'plamoq',
        'indicate': 'ko\'rsatmoq', 'item': 'buyum', 'offer': 'taklif qilmoq',
        'price': 'narx', 'product': 'mahsulot', 'property': 'mulki',
        'purchase': 'sotib olmoq', 'recommend': 'tavsiya qilmoq', 'select': 'tanlamoq',
        'tool': 'asbob', 'treat': 'davolamoq, munosibatda bo\'lmoq'
    },
    19: {
        'alive': 'tirik', 'bone': 'suyak', 'bother': 'bezovta qilmoq',
        'captain': 'kapitan', 'conclusion': 'xulosa', 'doubt': 'shubha',
        'explore': 'kashf qilmoq', 'foreign': 'xorijiy', 'glad': 'mamnun',
        'however': 'biroq', 'injustice': 'adolatsizlik', 'international': 'xalqaro',
        'lawyer': 'yurist', 'mention': 'eslatmoq', 'policy': 'siyosat',
        'social': 'ijtimoiy', 'speech': 'nutq', 'staff': 'xodimlar',
        'toward': 'tomonga', 'wood': 'yog\'och'
    },
    20: {
        'achieve': 'erishmoq', 'advise': 'maslahat bermoq', 'already': 'allaqachon',
        'basic': 'asosiy', 'bit': 'bo\'lak', 'consider': 'o\'ylab ko\'rmoq',
        'destroy': 'yo\'q qilmoq', 'entertain': 'ko\'ngil ochmoq', 'extra': 'qo\'shimcha',
        'goal': 'maqsad', 'lie': 'yolg\'on gapirmoq', 'meat': 'go\'sht',
        'opinion': 'fikr', 'real': 'haqiqiy', 'reflect': 'aks ettirmoq',
        'regard': 'deb bilmoq', 'serve': 'xizmat qilmoq', 'vegetable': 'sabzavot',
        'war': 'urush', 'worth': 'qimmat'
    },
    21: {
        'appear': 'paydo bo\'lmoq', 'base': 'asos', 'brain': 'miya',
        'career': 'martaba', 'clerk': 'xizmatchi', 'effort': 'harakat',
        'enter': 'kirishmoq', 'excellent': 'ajoyib', 'hero': 'qahramon',
        'hurry': 'shoshilmoq', 'inform': 'axborot bermoq', 'later': 'keyinroq',
        'leave': 'tashlab ketmoq', 'locate': 'topmoq', 'nurse': 'hamshira',
        'operation': 'operatsiya', 'pain': 'og\'riq', 'refuse': 'rad qilmoq',
        'though': 'garchi', 'various': 'turli'
    },
    22: {
        'actual': 'haqiqiy', 'amaze': 'hayratlanmoq', 'charge': 'zaryadlash',
        'comfort': 'qulaylik', 'contact': 'aloqa qilmoq', 'customer': 'mijoz',
        'deliver': 'yetkazib bermoq', 'earn': 'ishlab topmoq', 'gate': 'darvoza',
        'include': 'qo\'shib qo\'ymoq', 'manage': 'boshqarmoq', 'mystery': 'sir',
        'occur': 'uchramoq', 'opposite': 'qarama-qarshi', 'plate': 'likopcha',
        'receive': 'qabul qilmoq', 'reward': 'sovrin', 'set': 'qo\'ymoq, o\'rnatmoq',
        'steal': 'o\'g\'irlamoq', 'thief': 'o\'g\'ri'
    },
    23: {
        'advance': 'oldinga siljimoq', 'athlete': 'sportchi', 'average': 'o\'rtacha',
        'behavior': 'xatti-harakat', 'behind': 'orqasida', 'course': 'yo\'nalish, kurs',
        'lower': 'pasaytirmoq', 'match': 'o\'yin', 'member': 'azo',
        'mental': 'aqliy', 'passenger': 'yo\'lovchi', 'personality': 'shaxsiyat',
        'poem': 'she\'r', 'pole': 'qutb, asos', 'remove': 'olib tashlash',
        'safety': 'xavfsizlik', 'shoot': 'otmoq', 'sound': 'ovoz',
        'swim': 'suzmoq', 'web': 'o\'rgimchak to\'ri'
    },
    24: {
        'block': 'blok', 'cheer': 'hayqiriq', 'complex': 'murakkab',
        'critic': 'tanqidchi', 'event': 'voqea', 'exercise': 'mashq qilmoq',
        'fit': 'mos kelmoq', 'friendship': 'do\'stlik', 'guide': 'yo\'l ko\'rsatmoq',
        'lack': 'kamchilik', 'passage': 'yo\'lak', 'perform': 'ijro etmoq',
        'pressure': 'bosim', 'probable': 'ehtimol', 'public': 'jamoatchilik',
        'strike': 'urmoq', 'support': 'qo\'llab-quvvatlamoq', 'task': 'vazifa',
        'term': 'muddat', 'unite': 'birlashtirmoq'
    },
    25: {
        'associate': 'bog\'lamoq', 'environment': 'atrof-muhit', 'factory': 'zavod',
        'feature': 'xususiyat', 'instance': 'misol', 'involve': 'mashg\'ul bo\'lmoq',
        'medicine': 'dori', 'mix': 'aralashtirmoq', 'organize': 'tashkil qilmoq',
        'period': 'davr', 'populate': 'yashamoq', 'produce': 'ishlab chiqarmoq',
        'range': 'bir qator tur', 'recognize': 'tanimoq', 'regular': 'muntazam',
        'sign': 'belgi', 'tip': 'uch', 'tradition': 'an\'ana',
        'trash': 'axlat', 'wide': 'keng'
    },
    26: {
        'advice': 'maslahat', 'along': 'davomida', 'attention': 'diqqat',
        'attract': 'jalb qilmoq', 'climb': 'ko\'tarilmoq', 'drop': 'tushmoq',
        'final': 'oxirgi', 'further': 'uzoqroq', 'imply': 'shama qilmoq',
        'maintain': 'saqlamoq', 'neither': 'na', 'otherwise': 'aks holda',
        'physical': 'jismoniy', 'prove': 'isbotlamoq', 'react': 'javob bermoq',
        'ride': 'minmoq', 'situated': 'joylashgan', 'society': 'jamiyat',
        'standard': 'standart', 'suggest': 'taklif qilmoq'
    },
    27: {
        'actually': 'aslida', 'bite': 'tishlamoq', 'coast': 'qirg\'oq',
        'deal': 'kelishuv', 'desert': 'cho\'l', 'earthquake': 'zilzila',
        'effective': 'samarali', 'examine': 'o\'rganmoq', 'false': 'noto\'g\'ri',
        'gift': 'sovg\'a', 'hunger': 'ochlik', 'imagine': 'tasavvur qilmoq',
        'journey': 'sayohat', 'puzzle': 'jumboq', 'quite': 'biroq',
        'rather': 'maqul ko\'rmoq', 'specific': 'o\'ziga xos', 'tour': 'sayohat',
        'trip': 'safar', 'value': 'qadr, qiymat'
    },
    28: {
        'band': 'musiqiy guruh', 'barely': 'zo\'rg\'a', 'boring': 'zerikarli',
        'cancel': 'bekor qilmoq', 'driveway': 'yo\'lak', 'garbage': 'axlat',
        'instrument': 'asbob', 'list': 'ro\'yxat', 'magic': 'sehr',
        'message': 'xabar', 'notice': 'payqamoq', 'own': 'ega bo\'lmoq',
        'predict': 'taxmin qilmoq', 'professor': 'professor', 'rush': 'shoshilmoq',
        'schedule': 'jadval', 'share': 'ulashmoq', 'stage': 'bosqich',
        'storm': 'bo\'ron', 'within': 'ichida'
    },
    29: {
        'advertise': 'reklama qilmoq', 'assign': 'tayinlamoq', 'audience': 'tomoshabin',
        'breakfast': 'nonushta', 'competition': 'musobaqa', 'cool': 'salqin, ajoyib',
        'gain': 'erishmoq', 'importance': 'ahamiyat', 'knowledge': 'bilim',
        'major': 'katta', 'mean': 'anglatmoq', 'prefer': 'afzal ko\'rmoq',
        'president': 'prezident', 'progress': 'taraqqiyot', 'respect': 'hurmat',
        'rich': 'boy', 'skill': 'qobiliyat', 'somehow': 'qandaydir yo\'l bilan',
        'strength': 'kuch-quvvat', 'vote': 'ovoz bermoq'
    },
    30: {
        'above': 'yuqorida', 'ahead': 'oldinda', 'amount': 'miqdor',
        'belief': 'e\'tiqod', 'center': 'markaz', 'common': 'umumiy',
        'cost': 'xarajat', 'demonstrate': 'namoyish qilmoq', 'different': 'turli',
        'evidence': 'dalil', 'honesty': 'halollik', 'idiom': 'ibora',
        'independent': 'mustaqil', 'inside': 'ichida', 'master': 'usta',
        'memory': 'xotira', 'proper': 'to\'g\'ri', 'scan': 'ko\'zdan kechirmoq',
        'section': 'bo\'lim', 'surface': 'sirt'
    }
}

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # User ma'lumotlarini saqlash
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, chat_id, username, first_name)
        VALUES (?, ?, ?, ?)
    ''', (user.id, chat_id, user.username, user.first_name))
    conn.commit()
    conn.close()
    
    welcome_text = """
😁 Salom! Men @SULTSH_YT tomonidan yaratilgan Lug'at Bot man.
Menda 30 ta unit (bo'lim) bor!
Meni guruhga qo'shing va admin qiling — shunda testlar ishlaydi 🚀

**Foydalanish:**
/unit1 - Unit 1 testini boshlash
/unit2 - Unit 2 testini boshlash
...
/unit30 - Unit 30 testini boshlash
    """
    await update.message.reply_text(welcome_text)

# Unit testni boshlash
async def start_unit_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    
    # Faqat guruh adminlari test boshlashi mumkin
    if chat.type in ['group', 'supergroup']:
        try:
            member = await chat.get_member(user.id)
            if member.status not in ['creator', 'administrator']:
                await update.message.reply_text("❌ Faqat guruh adminlari test boshlay oladi!")
                return
        except Exception as e:
            logger.error(f"Admin tekshirishda xato: {e}")
            await update.message.reply_text("❌ Admin huquqlarini tekshirishda xato!")
            return
    
    # Unit raqamini tekshirish
    if not context.args or not context.args[0].replace('/unit', '').isdigit():
        await update.message.reply_text("❌ Iltimos, unit raqamini kiriting. Masalan: /unit7")
        return
    
    unit_number = int(context.args[0].replace('/unit', ''))
    
    if unit_number not in VOCABULARY:
        await update.message.reply_text("❌ Bunday unit mavjud emas! Iltimos, 1-30 oralig'idagi unitlardan foydalaning.")
        return
    
    # Avvalgi testni tozalash
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM active_tests WHERE chat_id = ?', (chat.id,))
    cursor.execute('DELETE FROM user_answers WHERE chat_id = ?', (chat.id,))
    conn.commit()
    conn.close()
    
    # Testni boshlash tugmasi
    keyboard = [
        [InlineKeyboardButton("🚀 Boshlash", callback_data=f"start_test_{unit_number}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f'🎲 "4000 Essential English Words — Unit {unit_number}" testiga tayyorlaning!\n'
        f'🖊 20 ta savol\n'
        f'⏱ Har bir savol uchun 10 soniya\n',
        reply_markup=reply_markup
    )

# Testni boshlash
async def begin_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    unit_number = int(query.data.replace('start_test_', ''))
    chat_id = query.message.chat_id
    
    # Test savollarini tayyorlash
    questions = generate_questions(unit_number)
    
    # Test ma'lumotlarini saqlash
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO active_tests (chat_id, unit_number, question_index, start_time, questions_data)
        VALUES (?, ?, ?, ?, ?)
    ''', (chat_id, unit_number, 0, datetime.now(), str(questions)))
    conn.commit()
    conn.close()
    
    # Birinchi savolni yuborish
    await send_question(chat_id, context, 0)

# Savol yuborish
async def send_question(chat_id: int, context: ContextTypes.DEFAULT_TYPE, question_index: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT questions_data FROM active_tests WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    
    if not result:
        return
    
    questions = eval(result[0])
    conn.close()
    
    if question_index >= len(questions):
        await finish_test(chat_id, context)
        return
    
    question_data = questions[question_index]
    english_word = question_data['english']
    options = question_data['options']
    
    # Variantlar tugmalari
    keyboard = []
    for option in options:
        keyboard.append([InlineKeyboardButton(option, callback_data=f"answer_{question_index}_{option}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❓ {english_word} so'zining ma'nosini toping:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Savol yuborishda xato: {e}")
        return
    
    # Keyingi savol uchun 10 soniya kutish
    context.job_queue.run_once(
        send_next_question, 
        10, 
        data={'chat_id': chat_id, 'question_index': question_index},
        name=f"next_question_{chat_id}_{question_index}"
    )

# Keyingi savolga o'tish
async def send_next_question(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data['chat_id']
    current_index = job_data['question_index']
    
    # Joriy savol indeksini yangilash
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE active_tests SET question_index = ? WHERE chat_id = ?', (current_index + 1, chat_id))
    conn.commit()
    conn.close()
    
    # Keyingi savolni yuborish
    await send_question(chat_id, context, current_index + 1)

# Javob qayta ishlash
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update