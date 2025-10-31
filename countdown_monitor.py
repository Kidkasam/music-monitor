#!/usr/bin/env python3
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import json
from datetime import datetime
import re
import os
from pathlib import Path
from twilio.rest import Client
import aiofiles

class TaylorSwiftCountdownMonitor:
    def __init__(self):
        self.url = "https://store.taylorswift.com"
        self.check_interval = 60  # Check every 60 seconds
        self.log_file = "/app/logs/countdown_monitor.log"
        self.state_file = "/app/data/countdown_state.json"
        
        # Twilio configuration
        self.twilio_enabled = all([
            os.getenv('SECRET_TWILIO_ACCOUNT_SID'),
            os.getenv('SECRET_TWILIO_AUTH_TOKEN'),
            os.getenv('SECRET_TWILIO_PHONE_NUMBER'),
            os.getenv('SECRET_YOUR_PHONE_NUMBER')
        ])
        
        if self.twilio_enabled:
            self.twilio_client = Client(
                os.getenv('SECRET_TWILIO_ACCOUNT_SID'),
                os.getenv('SECRET_TWILIO_AUTH_TOKEN')
            )
            self.twilio_from = os.getenv('SECRET_TWILIO_PHONE_NUMBER')
            self.twilio_to = os.getenv('SECRET_YOUR_PHONE_NUMBER')
            self.log("✅ Twilio SMS notifications enabled")
        else:
            self.log("⚠️  Twilio not configured - SMS notifications disabled")
        
        Path("/app/logs").mkdir(parents=True, exist_ok=True)
        Path("/app/data").mkdir(parents=True, exist_ok=True)
        
        self.previous_countdowns = None
    
    async def initialize(self):
        self.previous_countdowns = await self.load_state()
    
    async def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message, flush=True)
        try:
            async with aiofiles.open(self.log_file, "a") as f:
                await f.write(log_message + "\n")
        except Exception as e:
            print(f"Error writing to log: {e}")
    
    async def send_sms(self, message):
        if not self.twilio_enabled:
            return False
        
        try:
            msg = await asyncio.to_thread(
                self.twilio_client.messages.create,
                body=message,
                from_=self.twilio_from,
                to=self.twilio_to
            )
            await self.log(f"📱 SMS sent successfully (SID: {msg.sid})")
            return True
        except Exception as e:
            await self.log(f"❌ Failed to send SMS: {str(e)}")
            return False
    
    async def load_state(self):
        if os.path.exists(self.state_file):
            try:
                async with aiofiles.open(self.state_file, "r") as f:
                    content = await f.read()
                    return json.loads(content)
            except:
                return {}
        return {}
    
    async def save_state(self, countdowns):
        try:
            async with aiofiles.open(self.state_file, "w") as f:
                await f.write(json.dumps(countdowns, indent=2))
        except Exception as e:
            await self.log(f"Error saving state: {e}")
    
    async def check_for_countdown(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            await self.log(f"Checking {self.url}...")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for countdown indicators
            countdowns_found = []
            
            # Strategy 1: Look for countdown-related classes/IDs
            countdown_elements = soup.find_all(class_=re.compile(r'countdown|timer|clock', re.I))
            countdown_elements += soup.find_all(id=re.compile(r'countdown|timer|clock', re.I))
            
            # Strategy 2: Look for countdown-related text
            countdown_text = soup.find_all(string=re.compile(r'countdown|coming soon|launching|drops in', re.I))
            
            # Strategy 3: Look for time-related data attributes
            countdown_data = soup.find_all(attrs={'data-countdown': True})
            countdown_data += soup.find_all(attrs={'data-timer': True})
            countdown_data += soup.find_all(attrs={'data-launch-date': True})
            
            # Strategy 4: Look for common countdown JavaScript patterns
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and any(term in script.string.lower() for term in ['countdown', 'timer', 'setinterval', 'launch']):
                    if re.search(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}', script.string):
                        countdowns_found.append({
                            'type': 'script',
                            'content': script.string[:500]
                        })
            
            # Process found elements
            for elem in countdown_elements:
                countdowns_found.append({
                    'type': 'element_class',
                    'tag': elem.name,
                    'class': elem.get('class'),
                    'id': elem.get('id'),
                    'text': elem.get_text(strip=True)[:200]
                })
            
            for text in countdown_text:
                parent = text.parent
                countdowns_found.append({
                    'type': 'text_match',
                    'text': str(text)[:200],
                    'parent_tag': parent.name if parent else None
                })
            
            for elem in countdown_data:
                countdowns_found.append({
                    'type': 'data_attribute',
                    'tag': elem.name,
                    'attributes': {k: v for k, v in elem.attrs.items() if 'countdown' in k.lower() or 'timer' in k.lower() or 'launch' in k.lower()},
                    'text': elem.get_text(strip=True)[:200]
                })
            
            return countdowns_found
            
        except Exception as e:
            await self.log(f"Error checking website: {str(e)}")
            return None
    
    async def monitor(self):
        await self.log("🎵 Starting Taylor Swift Store Countdown Monitor")
        await self.log(f"📍 Monitoring: {self.url}")
        await self.log(f"⏱️  Check interval: {self.check_interval} seconds")
        
        if self.twilio_enabled:
            await self.send_sms("🎵 Taylor Swift countdown monitor started! You'll be notified when a new countdown appears on store.taylorswift.com")
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                countdowns = await self.check_for_countdown()
                
                if countdowns is not None:
                    if len(countdowns) > 0:
                        countdown_hash = json.dumps(countdowns, sort_keys=True)
                        
                        if countdown_hash != self.previous_countdowns.get('hash'):
                            await self.log(f"🎉 NEW COUNTDOWN DETECTED! Found {len(countdowns)} countdown element(s)")
                            
                            countdown_texts = []
                            for cd in countdowns[:3]:
                                if cd.get('text'):
                                    countdown_texts.append(cd['text'][:100])
                            
                            sms_message = f"🚨 NEW Taylor Swift countdown detected!\n\n"
                            sms_message += f"Found {len(countdowns)} countdown(s) on store.taylorswift.com\n\n"
                            if countdown_texts:
                                sms_message += "Preview:\n" + "\n".join(countdown_texts[:2])
                            
                            await self.send_sms(sms_message)
                            
                            self.previous_countdowns = {
                                'hash': countdown_hash,
                                'timestamp': datetime.now().isoformat(),
                                'count': len(countdowns)
                            }
                            await self.save_state(self.previous_countdowns)
                        else:
                            await self.log(f"✓ Countdown still active ({len(countdowns)} elements, no changes)")
                    else:
                        if self.previous_countdowns.get('hash'):
                            await self.log("📭 No countdown detected (countdown may have ended)")
                            await self.send_sms("ℹ️ Taylor Swift countdown has ended or been removed from store.taylorswift.com")
                            self.previous_countdowns = {}
                            await self.save_state(self.previous_countdowns)
                        else:
                            await self.log("📭 No countdown detected")
                
                await self.log(f"💤 Sleeping {self.check_interval}s (check #{check_count})")
                await asyncio.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            await self.log("🛑 Monitor stopped by user")
            if self.twilio_enabled:
                await self.send_sms("🛑 Taylor Swift countdown monitor stopped")
        except Exception as e:
            await self.log(f"❌ Monitor error: {str(e)}")
            if self.twilio_enabled:
                await self.send_sms(f"❌ Taylor Swift monitor encountered an error: {str(e)}")
            raise

if __name__ == "__main__":
    monitor = TaylorSwiftCountdownMonitor()
    asyncio.run(monitor.initialize())
    asyncio.run(monitor.monitor())
