import sqlite3
from datetime import datetime, timedelta
import re
from calendar import monthrange

class ExpenseBot:
    def __init__(self):
        self.conn = sqlite3.connect('expenses.db')
        self.setup_database()
        self.categories = [
            'food', 'transport', 'shopping', 'bills', 
            'entertainment', 'health', 'other'
        ]
        self.currency = 'USD'
        self.currency_symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£',
            'JPY': '¥', 'INR': '₹'
        }

    def setup_database(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                description TEXT,
                category TEXT,
                date TIMESTAMP,
                currency TEXT
            )
        ''')
        self.conn.commit()

    def process_message(self, message):
        if message.startswith('set currency'):
            return self.set_currency(message.split()[-1].upper())
        
        if message in ['categories', 'show categories']:
            return "Available categories: " + ", ".join(self.categories)
            
        if message.startswith('report'):
            return self.generate_report(message)

        # Try to extract amount, description and optional category
        pattern = r'(\d+\.?\d*)\s*(.*?)(?:\s+#(\w+))?$'
        match = re.match(pattern, message.strip())
        
        if not match:
            return (
                f"Please send amount and description, optionally with category:\n"
                f"Examples:\n"
                f"25.50 groceries #food\n"
                f"10 lunch\n"
                f"Commands:\n"
                f"- 'total' - see total expenses\n"
                f"- 'categories' - list categories\n"
                f"- 'set currency USD/EUR/GBP/JPY/INR'\n"
                f"- 'report month/year' - get spending report\n"
                f"- 'report 7days' - last 7 days report"
            )
            
        amount = float(match.group(1))
        description = match.group(2).strip() or "unspecified"
        category = match.group(3) or "other"
        
        if category not in self.categories:
            return f"Invalid category. Available categories: {', '.join(self.categories)}"

        # Save to database
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO expenses (amount, description, category, date, currency) VALUES (?, ?, ?, ?, ?)',
            (amount, description, category, datetime.now(), self.currency)
        )
        self.conn.commit()
        
        symbol = self.currency_symbols.get(self.currency, self.currency)
        return f"✅ Recorded: {symbol}{amount:.2f} for {description} (#{category})"

    def set_currency(self, new_currency):
        if new_currency in self.currency_symbols:
            self.currency = new_currency
            return f"Currency set to {new_currency}"
        return f"Invalid currency. Supported currencies: {', '.join(self.currency_symbols.keys())}"

    def get_total_expenses(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT SUM(amount), currency FROM expenses GROUP BY currency')
        totals = cursor.fetchall()
        
        if not totals:
            return "No expenses recorded"
            
        result = []
        for total, currency in totals:
            symbol = self.currency_symbols.get(currency, currency)
            result.append(f"{symbol}{total:.2f}")
        
        return "Total expenses: " + ", ".join(result)

    def generate_report(self, command):
        parts = command.split()
        
        if len(parts) < 2:
            return "Please specify report type: month, year, or 7days"
            
        report_type = parts[1].lower()
        
        if report_type == '7days':
            start_date = datetime.now() - timedelta(days=7)
            title = "Last 7 days"
        elif report_type == 'month':
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            title = f"Month of {start_date.strftime('%B %Y')}"
        elif report_type == 'year':
            start_date = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0)
            title = f"Year {start_date.year}"
        else:
            return "Invalid report type. Use: month, year, or 7days"

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT category, SUM(amount), currency
            FROM expenses 
            WHERE date >= ?
            GROUP BY category, currency
            ORDER BY SUM(amount) DESC
        ''', (start_date,))
        
        results = cursor.fetchall()
        
        if not results:
            return f"No expenses found for {title}"
            
        report = [f"📊 Expense Report - {title}"]
        
        for category, amount, currency in results:
            symbol = self.currency_symbols.get(currency, currency)
            report.append(f"#{category}: {symbol}{amount:.2f}")
            
        return "\n".join(report) 