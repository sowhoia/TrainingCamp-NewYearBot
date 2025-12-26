# 🎄 NewYearBot

A Telegram bot for managing New Year promotions with wishes, tickets, and referral system.

## Features

- 🎫 **Ticket System**: Users earn tickets for participation
- 📝 **Wishes**: Users can leave New Year wishes
- 👥 **Referrals**: Invite friends to earn extra tickets
- 📊 **Admin Panel**: Manage users, export data, give tickets
- 🔄 **Auto-posting**: Scheduled wish broadcasts to chat

## Setup

### 1. Clone & Install

```bash
git clone <repository-url>
cd NewYearBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
CHAT_ID=your_chat_id
REQUIRED_CHANNEL=@YourChannel
REQUIRED_CHAT=@YourChat
```

### 3. Run

```bash
python main.py
```

## Architecture

```
NewYearBot/
├── apps/handlers/          # Telegram handlers
│   ├── admin/              # Admin panel (modular)
│   ├── common.py           # Main commands
│   ├── wishes.py           # Wish handling
│   └── tickets.py          # Ticket display
├── data/
│   ├── database.py         # Database facade
│   └── repositories/       # Repository pattern
├── utils/
│   ├── keyboards/          # Inline keyboards
│   ├── messages.py         # Centralized strings
│   ├── scheduler.py        # APScheduler jobs
│   └── subscription.py     # Subscription checks
├── config/config.py        # Configuration
├── assets/                 # Images
└── main.py                 # Entry point
```

## Admin Commands

- `/admin` — Open admin panel
- `/export` — Export participant data

## License

MIT