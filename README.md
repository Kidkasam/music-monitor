# 🎵 Music Monitor System

A unified monitoring system that tracks Taylor Swift store countdowns and concert announcements for your favorite artists, with instant SMS notifications via Twilio.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)

## ✨ Features

- 🎤 **Taylor Swift Store Monitor** - Never miss a countdown or surprise drop
- 🎸 **Concert Tracking** - Monitor tour dates for unlimited artists via Bandsintown API
- 🎟️ **Ticketmaster Integration** - Optional Ticketmaster API support
- 📱 **SMS Notifications** - Get texted instantly when new events are announced
- 🐳 **Docker-Based** - Runs reliably 24/7 on Raspberry Pi
- ⚙️ **Easy Configuration** - Simple JSON config for managing artists
- 🔄 **Auto-Restart** - Survives crashes and reboots
- 💾 **State Persistence** - Tracks what you've been notified about

## 📸 Example Alerts

**Concert Announcement:**
```
🎵 NEW CONCERT ALERT!

2 new show(s) announced:

🎤 The 1975
📍 Madison Square Garden, New York, NY
📅 2025-11-15

🎤 Arctic Monkeys
📍 The Forum, Los Angeles, CA
📅 2025-12-01
```

**Taylor Swift Countdown:**
```
🚨 NEW Taylor Swift countdown!

Found 3 countdown(s) on store.taylorswift.com

Preview:
Coming Soon - New Album Drop
Countdown: 3 Days
```

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi 3+ (or any Linux system with Docker)
- Twilio account ([free trial available](https://www.twilio.com/try-twilio))
- Optional: Ticketmaster API key ([free](https://developer.ticketmaster.com/))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/music-monitor.git
   cd music-monitor
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Add your credentials:
   ```bash
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   YOUR_PHONE_NUMBER=+1234567890
   ```

3. **Configure your artists:**
   ```bash
   nano config/config.json
   ```
   
   Example:
   ```json
   {
     "taylor_swift_enabled": true,
     "bandsintown_enabled": true,
     "bandsintown_artists": [
       "Taylor Swift",
       "The 1975",
       "Arctic Monkeys"
     ],
     "check_interval": 300
   }
   ```

4. **Start the monitor:**
   ```bash
   docker-compose up -d
   ```

That's it! You'll receive an SMS confirmation that monitoring has started.

## 🛠️ Management

Use the included management script:

```bash
./manage.sh start        # Start the monitor
./manage.sh stop         # Stop the monitor
./manage.sh restart      # Restart (after config changes)
./manage.sh status       # Check status and recent activity
./manage.sh logs         # View logs
./manage.sh config       # Edit configuration
./manage.sh artists      # List monitored artists
./manage.sh update       # Update to latest version
```

## 📋 Configuration Options

Edit `config/config.json`:

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `taylor_swift_enabled` | boolean | Monitor Taylor Swift store | `true` |
| `bandsintown_enabled` | boolean | Monitor Bandsintown for concerts | `true` |
| `bandsintown_artists` | array | List of artist names to track | `[]` |
| `ticketmaster_enabled` | boolean | Use Ticketmaster API | `false` |
| `ticketmaster_artists` | array | Artists to track via Ticketmaster | `[]` |
| `check_interval` | number | Seconds between checks | `300` |

## 🍓 Raspberry Pi Setup

For complete Raspberry Pi setup instructions, see [RASPBERRY_PI_SETUP.md](docs/RASPBERRY_PI_SETUP.md)

**TL;DR:**
1. Flash Raspberry Pi OS to microSD
2. Run `./setup-raspberry-pi.sh` to install Docker
3. Copy files and configure as above
4. Run `docker-compose up -d`

## 🏗️ Architecture

The system uses a modular monitor architecture:

```
UnifiedMonitorSystem
├── TaylorSwiftCountdownMonitor
│   └── Scrapes store.taylorswift.com for countdowns
├── BandsintownMonitor
│   └── Polls Bandsintown API for concert announcements
└── TicketmasterMonitor (optional)
    └── Polls Ticketmaster Discovery API for events
```

Each monitor:
- Runs independently with error isolation
- Maintains its own state file
- Sends SMS alerts via Twilio
- Logs to separate files for debugging

## 📊 API Information

### Bandsintown API
- **Cost:** Free, no API key required
- **Rate Limits:** Generous for personal use
- **Coverage:** 500,000+ artists worldwide
- **Documentation:** https://artists.bandsintown.com/support/public-api

### Ticketmaster Discovery API
- **Cost:** Free tier available
- **Rate Limits:** 5,000 requests/day (free tier)
- **API Key:** Required (get at developer.ticketmaster.com)
- **Documentation:** https://developer.ticketmaster.com/

### Twilio SMS
- **Cost:** ~$0.0075 per SMS
- **Free Trial:** $15 credit (plenty for testing)
- **Note:** Free accounts can only send to verified numbers

## 💰 Cost Estimate

**One-time (Hardware):**
- Raspberry Pi 4 (4GB): $55
- Power supply: $8
- MicroSD card: $8
- Case: $10
- **Total: ~$81**

**Monthly:**
- Twilio SMS: $0.15-$0.38 (20-50 alerts/month)
- Electricity: ~$0.50
- **Total: <$1/month**

## 🔧 Troubleshooting

### Monitor not starting
```bash
docker-compose logs
docker-compose up -d --build
```

### No SMS notifications
1. Check `.env` has correct Twilio credentials
2. Verify phone number is verified (free accounts)
3. Check logs: `./manage.sh logs | grep -i twilio`

### No concert alerts
1. Verify artist names: `./manage.sh artists`
2. Check artist has events on Bandsintown.com
3. View monitor logs: `tail logs/bandsintown_monitor.log`

### Adding more artists
```bash
./manage.sh config
# Add artist names to bandsintown_artists array
./manage.sh restart
```

## 📁 Project Structure

```
music-monitor/
├── unified_monitor.py      # Main monitoring system
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
├── manage.sh              # Management script
├── setup-raspberry-pi.sh  # Pi setup automation
├── config/
│   └── config.json        # Configuration file
├── logs/                  # Monitor logs (gitignored)
├── data/                  # State persistence (gitignored)
└── README.md             # This file
```

## 🤝 Contributing

Contributions are welcome! Here are some ideas:

- Add more monitoring sources (Spotify, Songkick, etc.)
- Implement email notifications
- Add Discord/Slack webhook support
- Create web dashboard for viewing alerts
- Add filtering by location/venue
- Improve artist name matching

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- [Bandsintown](https://www.bandsintown.com/) for their excellent API
- [Ticketmaster](https://developer.ticketmaster.com/) for event data
- [Twilio](https://www.twilio.com/) for SMS notifications
- Taylor Swift for being awesome 🎵

## ⚠️ Disclaimer

This project is for personal use only. Please respect API rate limits and terms of service for all integrated services. The author is not responsible for any misuse or violations of third-party terms of service.

## 📧 Support

If you encounter issues:
1. Check the [troubleshooting section](#-troubleshooting)
2. Review logs: `./manage.sh logs`
3. Open an issue on GitHub

---

**Made with ❤️ for music fans who never want to miss a show**
