# Contributing to Music Monitor

Thank you for your interest in contributing! Here's how you can help:

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/music-monitor.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test thoroughly
6. Commit: `git commit -m "Add: description of your changes"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (without Docker)
python unified_monitor.py
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to classes and functions
- Comment complex logic

## Testing

Before submitting a PR:
- Test with Docker: `docker-compose up --build`
- Verify SMS notifications work
- Check logs for errors
- Test configuration changes

## Ideas for Contributions

- Add new monitoring sources (Spotify, Songkick, etc.)
- Implement additional notification channels (email, Discord, Slack)
- Create web dashboard
- Add location-based filtering
- Improve error handling
- Add unit tests
- Improve documentation

## Questions?

Open an issue for discussion before starting major changes.
