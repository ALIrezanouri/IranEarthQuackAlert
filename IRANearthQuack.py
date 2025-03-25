import requests
import xml.etree.ElementTree as ET
import asyncio
from telegram import Bot
import convert_numbers
import time


# Configuration
TELEGRAM_TOKEN = '8029051594:AAGvKFxAuE7PXmkzz4W9thA-iQJN7q0lg5I'
CHAT_ID = '@zelzeleshod'  # Ensure this is correct and the bot is an admin
FEED_URL = 'http://irsc.ut.ac.ir/events_list_fa.xml'

# Initialize the bot
bot = Bot(token=TELEGRAM_TOKEN)
def convert_persian_to_decimal(persian_lat_long):
    # Map Persian numerals to their Arabic counterparts
    persian_to_arabic = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    
    # Convert Persian numerals
    for persian, arabic in persian_to_arabic.items():
        persian_lat_long = persian_lat_long.replace(persian, arabic)
    
    return persian_lat_long


async def fetch_earthquake_data():
    try:
        response = requests.get(FEED_URL)
        response.raise_for_status()  # Raise an error for bad responses
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

async def parse_earthquake_data(xml_data):
    earthquakes = []
    for item in xml_data.findall('item'):
        earthquake = {}

        # Fetch relevant data
        id_elem = item.find('id')
        date_elem = item.find('date')
        mag_elem = item.find('mag')
        reg1_elem = item.find('reg1')
        reg2_elem = item.find('reg2')
        reg3_elem = item.find('reg3')
        dep_elem = item.find('dep')
        lat_elem = item.find('lat')
        long_elem = item.find('long')

        # Populate the earthquake dictionary
        earthquake['id'] = id_elem.text if id_elem is not None else "Unknown"
        earthquake['date'] = date_elem.text if date_elem is not None else "Unknown"
        earthquake['magnitude'] = mag_elem.text if mag_elem is not None else "Unknown"
        earthquake['location'] = (
            f"{reg1_elem.text}, {reg2_elem.text}, {reg3_elem.text}"
            if reg1_elem is not None and reg2_elem is not None and reg3_elem is not None else "Unknown"
        )
        earthquake['depth'] = dep_elem.text if dep_elem is not None else "Unknown"

        # Convert latitude and longitude from Persian numerals to decimal
        if lat_elem is not None and long_elem is not None:
            lat_decimal = convert_persian_to_decimal(lat_elem.text.strip())
            long_decimal = convert_persian_to_decimal(long_elem.text.strip())
            # Construct the Google Maps URL
            earthquake['google_maps'] = f"https://www.google.com/maps?q={lat_decimal},{long_decimal}"

        # Add to the list only if the ID is known
        if earthquake['id'] != "Unknown":
            earthquakes.append(earthquake)
    
    return earthquakes
    

async def send_alerts(earthquakes):
    
    
    for eq in earthquakes:
        message = (
            f"⚠️⚠️هشدار زلزله ⚠️⚠️\n\n"
            f"شماره پیگیری: {eq['id']}\n\n"
            f"⏰زمان⏰: {eq['date']}\n\n"
            f"🔥شدت به ریشتر🔥: {eq['magnitude']}\n\n"
            f"📍📍مکان📍📍: {eq['location']}\n\n"
            f"عمق: {eq['depth']} km\n\n"
                  
#           f"https://www.google.com/maps?q=" + convert_numbers.persian_to_english(str(eq['lat']).replace(" N","")) +"," +convert_numbers.persian_to_english(str(eq['long']).replace(" E",""))
        )
        print(message)
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"Sent message: {message}")
        except Exception as e:
            print(f"Failed to send message: {e}",TimeoutError)

async def main():
    last_earthquake_id = None
    while True:
        xml_data = await fetch_earthquake_data()
        if xml_data is not None:
            earthquakes = await parse_earthquake_data(xml_data)
            if earthquakes:
                latest_id = earthquakes[0]['id']
                if last_earthquake_id != latest_id:
                    await send_alerts(earthquakes)
                    last_earthquake_id = latest_id
        await asyncio.sleep(60)  # Wait for 10 seconds before fetching again

if __name__ == "__main__":
    asyncio.run(main())