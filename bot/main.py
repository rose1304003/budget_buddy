"""Telegram bot for Teacher Budget Buddy."""

import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000")

def format_money(amount: int) -> str:
    """Format amount in UZS."""
    return f"{amount:,} UZS"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
    welcome_text = f"""
👋 Welcome to **Teacher Budget Buddy**, {user.first_name}!

I help you track your income and expenses easily.

**Quick Commands:**
💰 /income 50000 Salary - Add income
💸 /expense 10000 Coffee - Add expense
📊 /balance - Check your balance
📈 /stats - View statistics
📝 /last - Last transactions
🏷️ /categories - Manage categories
❓ /help - Show all commands
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
📚 **Available Commands:**

**Quick Actions:**
💰 `/income <amount> <note>` - Add income
   Example: `/income 50000 Salary payment`

💸 `/expense <amount> <note>` - Add expense
   Example: `/expense 10000 Coffee and snacks`

**View Data:**
📊 `/balance` - Show current balance
📈 `/stats` - Weekly and monthly statistics
📝 `/last` - Show last 5 transactions
🏷️ `/categories` - List all categories

**Other:**
❓ `/help` - Show this help message
🔄 `/start` - Restart bot
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command."""
    user = update.effective_user
    
    try:
        response = requests.get(
            f"{API_URL}/api/stats",
            headers={"X-TG-User-ID": str(user.id)},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            balance_amount = data.get("balance", 0)
            
            emoji = "💰" if balance_amount >= 0 else "📉"
            
            message = f"""
{emoji} **Your Balance**

Current: **{format_money(balance_amount)}**

📊 This Week:
  Income: {format_money(data.get("week_income", 0))}
  Spent: {format_money(data.get("week_spent", 0))}

📈 This Month:
  Income: {format_money(data.get("month_income", 0))}
  Spent: {format_money(data.get("month_spent", 0))}
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not fetch balance. Please try again.")
    
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        await update.message.reply_text("❌ Error connecting to server.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    user = update.effective_user
    
    try:
        response = requests.get(
            f"{API_URL}/api/stats",
            headers={"X-TG-User-ID": str(user.id)},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            week_net = data.get("week_income", 0) - data.get("week_spent", 0)
            month_net = data.get("month_income", 0) - data.get("month_spent", 0)
            
            week_emoji = "📈" if week_net >= 0 else "📉"
            month_emoji = "📈" if month_net >= 0 else "📉"
            
            message = f"""
📊 **Your Statistics**

💰 **Overall Balance:** {format_money(data.get("balance", 0))}

📅 **This Week:**
  {week_emoji} Net: {format_money(week_net)}
  ✅ Income: {format_money(data.get("week_income", 0))}
  ❌ Spent: {format_money(data.get("week_spent", 0))}

📆 **This Month:**
  {month_emoji} Net: {format_money(month_net)}
  ✅ Income: {format_money(data.get("month_income", 0))}
  ❌ Spent: {format_money(data.get("month_spent", 0))}

💡 Use /last to see recent transactions
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not fetch statistics.")
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        await update.message.reply_text("❌ Error connecting to server.")

async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /income command."""
    user = update.effective_user
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/income <amount> <note>`\n"
            "Example: `/income 50000 Salary payment`",
            parse_mode='Markdown'
        )
        return
    
    try:
        amount = int(context.args[0])
        note = " ".join(context.args[1:]) if len(context.args) > 1 else "Income"
        
        response = requests.post(
            f"{API_URL}/api/transactions",
            json={
                "type": "income",
                "amount": amount,
                "note": note,
                "occurred_at": datetime.utcnow().isoformat()
            },
            headers={"X-TG-User-ID": str(user.id)},
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            await update.message.reply_text(
                f"✅ Income added!\n\n"
                f"💰 Amount: {format_money(amount)}\n"
                f"📝 Note: {note}\n\n"
                f"Use /balance to see your updated balance."
            )
        else:
            await update.message.reply_text("❌ Failed to add income. Please try again.")
    
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please use numbers only.")
    except Exception as e:
        logger.error(f"Error adding income: {e}")
        await update.message.reply_text("❌ Error adding income.")

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /expense command."""
    user = update.effective_user
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/expense <amount> <note>`\n"
            "Example: `/expense 10000 Coffee and snacks`",
            parse_mode='Markdown'
        )
        return
    
    try:
        amount = int(context.args[0])
        note = " ".join(context.args[1:]) if len(context.args) > 1 else "Expense"
        
        response = requests.post(
            f"{API_URL}/api/transactions",
            json={
                "type": "expense",
                "amount": amount,
                "note": note,
                "occurred_at": datetime.utcnow().isoformat()
            },
            headers={"X-TG-User-ID": str(user.id)},
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            await update.message.reply_text(
                f"✅ Expense added!\n\n"
                f"💸 Amount: {format_money(amount)}\n"
                f"📝 Note: {note}\n\n"
                f"Use /balance to see your updated balance."
            )
        else:
            await update.message.reply_text("❌ Failed to add expense. Please try again.")
    
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please use numbers only.")
    except Exception as e:
        logger.error(f"Error adding expense: {e}")
        await update.message.reply_text("❌ Error adding expense.")

async def last_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /last command."""
    user = update.effective_user
    
    try:
        response = requests.get(
            f"{API_URL}/api/transactions?limit=5",
            headers={"X-TG-User-ID": str(user.id)},
            timeout=5
        )
        
        if response.status_code == 200:
            transactions = response.json()
            
            if not transactions:
                await update.message.reply_text("📭 No transactions yet. Use /income or /expense to add one!")
                return
            
            message = "📝 **Last 5 Transactions:**\n\n"
            
            for tx in transactions:
                tx_type = tx.get("type", "")
                amount = tx.get("amount", 0)
                note = tx.get("note", "No note")
                date = tx.get("occurred_at", "")
                
                try:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_str = dt.strftime("%b %d, %H:%M")
                except:
                    date_str = "Unknown date"
                
                emoji = "💰" if tx_type == "income" else "💸"
                sign = "+" if tx_type == "income" else "-"
                
                message += f"{emoji} {sign}{format_money(amount)}\n"
                message += f"   {note}\n"
                message += f"   🕐 {date_str}\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not fetch transactions.")
    
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        await update.message.reply_text("❌ Error connecting to server.")

async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /categories command."""
    user = update.effective_user
    
    try:
        response = requests.get(
            f"{API_URL}/api/categories",
            headers={"X-TG-User-ID": str(user.id)},
            timeout=5
        )
        
        if response.status_code == 200:
            cats = response.json()
            
            if not cats:
                await update.message.reply_text("📭 No categories yet!")
                return
            
            income_cats = [c for c in cats if c.get("kind") == "income"]
            expense_cats = [c for c in cats if c.get("kind") == "expense"]
            
            message = "🏷️ **Your Categories:**\n\n"
            
            if income_cats:
                message += "💰 **Income:**\n"
                for cat in income_cats:
                    message += f"  • {cat.get('name')}\n"
                message += "\n"
            
            if expense_cats:
                message += "💸 **Expenses:**\n"
                for cat in expense_cats:
                    message += f"  • {cat.get('name')}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not fetch categories.")
    
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        await update.message.reply_text("❌ Error connecting to server.")

def main():
    """Start the bot."""
    logger.info("Starting bot...")
    logger.info(f"API URL: {API_URL}")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("income", add_income))
    application.add_handler(CommandHandler("expense", add_expense))
    application.add_handler(CommandHandler("last", last_transactions))
    application.add_handler(CommandHandler("categories", categories))
    
    logger.info("Bot running!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()