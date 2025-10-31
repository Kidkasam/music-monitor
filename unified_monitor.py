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
from typing import Dict, List, Optional
import aiofiles

class MonitorBase:
    """Base class for all monitors"""
    def __init__(self, name: str, twilio_client: Optional[Client], twilio_from: str, twilio_to: str):
        self.name = name
        self.twilio_client = twilio_client
        self.twilio_from = twilio_from
        self.twilio_to = twilio_to
        self.log_file = f"/app/logs/{name}_monitor.log"
        self.state_file = f"/app/data/{name}_state.json"
        self.previous_state = None
    
    async def initialize(self):
        self.previous_state = await self.load_state()
        
    async def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{self.name}] {message}"
        print(log_message, flush=True)
        try:
            async with aiofiles.open(self.log_file, "a") as f:
                await f.write(log_message + "\n")
        except Exception as e:
            print(f"Error writing to log: {e}")
    
    async def send_sms(self, message: str) -> bool:
        if not self.twilio_client:
            return False
        try:
            msg = await asyncio.to_thread(
                self.twilio_client.messages.create,
                body=message,
                from_=self.twilio_from,
                to=self.twilio_to
            )
            await self.log(f"📱 SMS sent (SID: {msg.sid})")
            return True
        except Exception as e:
            await self.log(f"❌ Failed to send SMS: {str(e)}")
            return False
    
    async def load_state(self) -> Dict:
        if os.path.exists(self.state_file):
            try:
                async with aiofiles.open(self.state_file, "r") as f:
                    content = await f.read()
                    return json.loads(content)
            except:
                return {}
        return {}
    
    async def save_state(self, state: Dict):
        try:
            async with aiofiles.open(self.state_file, "w") as f:
                await f.write(json.dumps(state, indent=2))
        except Exception as e:
            await self.log(f"Error saving state: {e}")
    
    async def check(self) -> Optional[Dict]:
        """Override this in subclasses"""
        raise NotImplementedError
    
    def format_alert(self, data: Dict) -> str:
        """Override this in subclasses"""
        raise NotImplementedError


class TaylorSwiftCountdownMonitor(MonitorBase):
    """Monitor Taylor Swift store for countdowns"""
    def __init__(self, twilio_client, twilio_from, twilio_to):
        super().__init__("taylor_swift", twilio_client, twilio_from, twilio_to)
        self.url = "https://store.taylorswift.com"
    
    async def check(self) -> Optional[Dict]:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            countdowns_found = []
            
            # Strategy 1: Countdown classes/IDs
            countdown_elements = soup.find_all(class_=re.compile(r'countdown|timer|clock', re.I))
            countdown_elements += soup.find_all(id=re.compile(r'countdown|timer|clock', re.I))
            
            # Strategy 2: Countdown text
            countdown_text = soup.find_all(string=re.compile(r'countdown|coming soon|launching|drops in', re.I))
            
            # Strategy 3: Data attributes
            countdown_data = soup.find_all(attrs={'data-countdown': True})
            countdown_data += soup.find_all(attrs={'data-timer': True})
            
            for elem in countdown_elements:
                countdowns_found.append({
                    'type': 'element',
                    'text': elem.get_text(strip=True)[:200]
                })
            
            for text in countdown_text:
                countdowns_found.append({
                    'type': 'text',
                    'text': str(text)[:200]
                })
            
            return {'countdowns': countdowns_found, 'count': len(countdowns_found)}
            
        except Exception as e:
            await self.log(f"Error checking: {str(e)}")
            return None
    
    def format_alert(self, data: Dict) -> str:
        count = data['count']
        countdowns = data['countdowns']
        
        message = f"🚨 NEW Taylor Swift countdown!\n\n"
        message += f"Found {count} countdown(s) on store.taylorswift.com\n\n"
        
        if countdowns:
            preview_texts = [cd.get('text', '')[:100] for cd in countdowns[:2] if cd.get('text')]
            if preview_texts:
                message += "Preview:\n" + "\n".join(preview_texts)
        
        return message


class BandsintownMonitor(MonitorBase):
    """Monitor Bandsintown for artist tour dates"""
    def __init__(self, artists: List[str], twilio_client, twilio_from, twilio_to):
        super().__init__("bandsintown", twilio_client, twilio_from, twilio_to)
        self.artists = artists
        self.app_id = "unified_monitor"
        self.base_url = "https://rest.bandsintown.com/artists"
    
    async def check(self) -> Optional[Dict]:
        try:
            all_new_events = []
            
            async with aiohttp.ClientSession() as session:
                for artist in self.artists:
                    from urllib.parse import quote
                    artist_encoded = quote(artist)
                    url = f"{self.base_url}/{artist_encoded}/events/?app_id={self.app_id}"
                    
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            events = await response.json()
                            
                            artist_state = self.previous_state.get(artist, {})
                            previous_event_ids = set(artist_state.get('event_ids', []))
                            
                            new_events = []
                            current_event_ids = []
                            
                            for event in events:
                                event_id = event.get('id')
                                current_event_ids.append(event_id)
                                
                                if event_id not in previous_event_ids:
                                    new_events.append({
                                        'artist': artist,
                                        'venue': event.get('venue', {}).get('name', 'Unknown'),
                                        'location': event.get('venue', {}).get('location', 'Unknown'),
                                        'datetime': event.get('datetime', 'Unknown'),
                                        'url': event.get('url', '')
                                    })
                            
                            if new_events:
                                all_new_events.extend(new_events)
                            
                            self.previous_state[artist] = {
                                'event_ids': current_event_ids,
                                'last_check': datetime.now().isoformat()
                            }
                    
                    await asyncio.sleep(0.5)
            
            if all_new_events:
                await self.save_state(self.previous_state)
                return {'new_events': all_new_events, 'count': len(all_new_events)}
            
            return None
            
        except Exception as e:
            await self.log(f"Error checking: {str(e)}")
            return None
    
    def format_alert(self, data: Dict) -> str:
        events = data['new_events']
        count = data['count']
        
        message = f"🎵 NEW CONCERT ALERT!\n\n"
        message += f"{count} new show(s) announced:\n\n"
        
        for event in events[:3]:  # First 3 events
            date_str = event['datetime'].split('T')[0] if 'T' in event['datetime'] else event['datetime']
            message += f"🎤 {event['artist']}\n"
            message += f"📍 {event['venue']}, {event['location']}\n"
            message += f"📅 {date_str}\n\n"
        
        if count > 3:
            message += f"...and {count - 3} more!"
        
        return message


class TicketmasterMonitor(MonitorBase):
    """Monitor Ticketmaster for artist events"""
    def __init__(self, artists: List[str], api_key: str, twilio_client, twilio_from, twilio_to):
        super().__init__("ticketmaster", twilio_client, twilio_from, twilio_to)
        self.artists = artists
        self.api_key = api_key
        self.base_url = "https://app.ticketmaster.com/discovery/v2/events.json"
    
    async def check(self) -> Optional[Dict]:
        try:
            all_new_events = []
            
            async with aiohttp.ClientSession() as session:
                for artist in self.artists:
                    params = {
                        'apikey': self.api_key,
                        'keyword': artist,
                        'classificationName': 'Music',
                        'size': 20
                    }
                    
                    async with session.get(self.base_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            data = await response.json()
                            events = data.get('_embedded', {}).get('events', [])
                            
                            artist_state = self.previous_state.get(artist, {})
                            previous_event_ids = set(artist_state.get('event_ids', []))
                            
                            new_events = []
                            current_event_ids = []
                            
                            for event in events:
                                event_id = event.get('id')
                                current_event_ids.append(event_id)
                                
                                if event_id not in previous_event_ids:
                                    venue = event.get('_embedded', {}).get('venues', [{}])[0]
                                    new_events.append({
                                        'artist': artist,
                                        'name': event.get('name', 'Unknown Event'),
                                        'venue': venue.get('name', 'Unknown'),
                                        'location': f"{venue.get('city', {}).get('name', '')}, {venue.get('state', {}).get('stateCode', '')}",
                                        'date': event.get('dates', {}).get('start', {}).get('localDate', 'Unknown'),
                                        'url': event.get('url', '')
                                    })
                            
                            if new_events:
                                all_new_events.extend(new_events)
                            
                            self.previous_state[artist] = {
                                'event_ids': current_event_ids,
                                'last_check': datetime.now().isoformat()
                            }
                    
                    await asyncio.sleep(0.5)
            
            if all_new_events:
                await self.save_state(self.previous_state)
                return {'new_events': all_new_events, 'count': len(all_new_events)}
            
            return None
            
        except Exception as e:
            await self.log(f"Error checking: {str(e)}")
            return None
    
    def format_alert(self, data: Dict) -> str:
        events = data['new_events']
        count = data['count']
        
        message = f"🎟️ NEW TICKETMASTER EVENT!\n\n"
        message += f"{count} new event(s) found:\n\n"
        
        for event in events[:3]:
            message += f"🎤 {event['name']}\n"
            message += f"📍 {event['venue']}, {event['location']}\n"
            message += f"📅 {event['date']}\n\n"
        
        if count > 3:
            message += f"...and {count - 3} more!"
        
        return message


class UnifiedMonitorSystem:
    """Main monitoring system that coordinates all monitors"""
    def __init__(self):
        # Twilio setup
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
            print("✅ Twilio SMS notifications enabled")
        else:
            self.twilio_client = None
            self.twilio_from = ""
            self.twilio_to = ""
            print("⚠️  Twilio not configured - SMS notifications disabled")
        
        # Ensure directories
        Path("/app/logs").mkdir(parents=True, exist_ok=True)
        Path("/app/data").mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize monitors
        self.monitors = []
        
        # Taylor Swift countdown monitor
        if self.config.get('taylor_swift_enabled', True):
            self.monitors.append(
                TaylorSwiftCountdownMonitor(self.twilio_client, self.twilio_from, self.twilio_to)
            )
        
        # Bandsintown monitor
        if self.config.get('bandsintown_enabled', True) and self.config.get('bandsintown_artists'):
            self.monitors.append(
                BandsintownMonitor(
                    self.config['bandsintown_artists'],
                    self.twilio_client,
                    self.twilio_from,
                    self.twilio_to
                )
            )
        
        # Ticketmaster monitor
        if self.config.get('ticketmaster_enabled', False) and os.getenv('SECRET_TICKETMASTER_API_KEY'):
            self.monitors.append(
                TicketmasterMonitor(
                    self.config.get('ticketmaster_artists', []),
                    os.getenv('SECRET_TICKETMASTER_API_KEY'),
                    self.twilio_client,
                    self.twilio_from,
                    self.twilio_to
                )
            )
        
        self.check_interval = self.config.get('check_interval', 300)
    
    async def initialize_monitors(self):
        for monitor in self.monitors:
            await monitor.initialize()
    
    def load_config(self) -> Dict:
        config_file = "/app/config/config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'taylor_swift_enabled': True,
            'bandsintown_enabled': True,
            'bandsintown_artists': ['Taylor Swift', 'The 1975', 'Arctic Monkeys'],
            'ticketmaster_enabled': False,
            'ticketmaster_artists': [],
            'check_interval': 300
        }
    
    async def run(self):
        print("🎵 Unified Music Monitor System Starting")
        print(f"📊 Active monitors: {len(self.monitors)}")
        for monitor in self.monitors:
            print(f"   - {monitor.name}")
        print(f"⏱️  Check interval: {self.check_interval} seconds")
        print("")
        
        await self.initialize_monitors()
        
        if self.twilio_enabled:
            monitor_names = ", ".join([m.name.replace('_', ' ').title() for m in self.monitors])
            startup_msg = f"🎵 Music monitor started!\n\nActive monitors:\n{monitor_names}\n\nYou'll be notified of new events."
            if self.monitors:
                await self.monitors[0].send_sms(startup_msg)
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                print(f"\n{'='*60}")
                print(f"Check #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                for monitor in self.monitors:
                    try:
                        await monitor.log(f"Running check...")
                        result = await monitor.check()
                        
                        if result:
                            await monitor.log(f"✨ New data detected!")
                            alert_message = monitor.format_alert(result)
                            await monitor.send_sms(alert_message)
                        else:
                            await monitor.log("No new data")
                    
                    except Exception as e:
                        await monitor.log(f"❌ Check failed: {str(e)}")
                
                print(f"\n💤 Sleeping {self.check_interval}s until next check...")
                await asyncio.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped by user")
            if self.twilio_enabled and self.monitors:
                await self.monitors[0].send_sms("🛑 Music monitor stopped")
        
        except Exception as e:
            print(f"\n❌ Fatal error: {str(e)}")
            if self.twilio_enabled and self.monitors:
                await self.monitors[0].send_sms(f"❌ Music monitor error: {str(e)}")
            raise


if __name__ == "__main__":
    monitor = UnifiedMonitorSystem()
    asyncio.run(monitor.run())
