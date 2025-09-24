import os
import json
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

# ================= CONFIG ===================
TOKEN = os.getenv("8303795354:AAG5F3-J1-nju9w8g6TlxTzufVRIuVhXjUA")  # Defina no Render como variável de ambiente
ADMIN_USER_IDS = [8185983122]    # coloque aqui seu ID do Telegram
MERCADO_PAGO_TOKEN = os.getenv("MP_TOKEN")  # token do Mercado Pago
PACKS_FILE = "packs.json"

# ============================================
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# -------------------- FUNÇÕES PACKS --------------------
def load_packs():
    if not os.path.exists(PACKS_FILE):
        return {"fotos": [], "videos": []}
    with open(PACKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_packs(data):
    with open(PACKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -------------------- START --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📸 Packs de Fotos", callback_data="fotos")],
        [InlineKeyboardButton("🎥 Packs de Vídeos", callback_data="videos")],
        [InlineKeyboardButton("💎 Recarregar com PIX", callback_data="comprar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(
        photo="https://i.imgur.com/xyz.png",  # coloque sua imagem Imgur
        caption="🔥 <b>Bem-vindo(a) à Red Room +18 Store</b>\n\n"
                "📸 Fotos exclusivas\n🎥 Vídeos quentes\n💎 Packs premium\n\n"
                "👉 Escolha uma opção abaixo:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# -------------------- MENU --------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_packs()

    if query.data == "fotos":
        if not data["fotos"]:
            await query.edit_message_caption("🚫 Nenhum pack de fotos disponível.")
            return
        msg = "🔥 <b>Packs de Fotos disponíveis:</b>\n\n"
        for p in data["fotos"]:
            msg += f"📦 {p['nome']} - R$ {p['preco']}\n🔗 {p['link']}\n\n"
        await query.edit_message_caption(caption=msg, parse_mode="HTML")

    elif query.data == "videos":
        if not data["videos"]:
            await query.edit_message_caption("🚫 Nenhum pack de vídeos disponível.")
            return
        msg = "🎥 <b>Packs de Vídeos disponíveis:</b>\n\n"
        for p in data["videos"]:
            msg += f"📦 {p['nome']} - R$ {p['preco']}\n🔗 {p['link']}\n\n"
        await query.edit_message_caption(caption=msg, parse_mode="HTML")

    elif query.data == "comprar":
        await query.edit_message_caption(
            caption="💰 Para comprar créditos use o comando /pix.\n\n"
                    "Você receberá um QR Code/Chave PIX para pagamento automático.",
            parse_mode="HTML"
        )

# -------------------- ADD PACK --------------------
async def addpack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⚠️ Apenas o admin pode adicionar packs.")
        return

    if len(context.args) < 4:
        await update.message.reply_text(
            "Use: /addpack <foto|video> <nome> <preço> <link>\n\n"
            "Exemplo:\n"
            "/addpack foto Pack_Gatas 20 https://imgur.com/xyz"
        )
        return

    tipo = context.args[0].lower()
    nome = context.args[1]
    preco = float(context.args[2])
    link = context.args[3]

    if tipo not in ["foto", "video"]:
        await update.message.reply_text("Tipo inválido. Use <foto|video>.")
        return

    data = load_packs()
    pack_info = {"nome": nome, "preco": preco, "link": link}
    if tipo == "foto":
        data["fotos"].append(pack_info)
    else:
        data["videos"].append(pack_info)

    save_packs(data)
    await update.message.reply_text(f"✅ Pack '{nome}' adicionado com sucesso!")

# -------------------- PIX --------------------
async def pix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {"Authorization": f"Bearer {MERCADO_PAGO_TOKEN}"}
    data = {
        "transaction_amount": 10,
        "description": "Créditos Red Room +18",
        "payment_method_id": "pix",
        "payer": {"email": "comprador@email.com"}
    }
    r = requests.post(url, headers=headers, json=data).json()

    if "point_of_interaction" in r:
        qr = r["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        copia_cola = r["point_of_interaction"]["transaction_data"]["qr_code"]
        await update.message.reply_text(
            f"💳 <b>Pague via PIX:</b>\n\n"
            f"<code>{copia_cola}</code>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("⚠️ Erro ao gerar PIX. Verifique sua API Key.")

# -------------------- MAIN --------------------
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pix", pix))
    application.add_handler(CommandHandler("addpack", addpack))
    application.add_handler(CallbackQueryHandler(menu_handler))

    # Inicializa bot em background
    application.run_polling()

# -------------------- FLASK WEBHOOK --------------------
@app.route("/mp", methods=["POST"])
def mp_webhook():
    data = request.json
    logging.info(f"Webhook recebido: {data}")
    return "ok", 200

if __name__ == "__main__":
    main()
