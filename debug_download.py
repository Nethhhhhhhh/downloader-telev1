import asyncio
import logging
from services.downloader import downloader

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_download():
    url = input("Enter video URL: ").strip()
    if not url:
        # Default to a safe test URL if none provided
        url = "https://www.tiktok.com/@tiktok/video/7106634589417688366" 
    
    print(f"Testing download for: {url}")
    try:
        media_list = await downloader.download_media(url)
        print("Download successful!")
        for m in media_list:
            print(f"- {m['type']}: {m['path']} (Group ID: {m.get('group_id')})")
            
            # Test cleanup
            # downloader.cleanup(m['path'])
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error caught: {e}")

if __name__ == "__main__":
    asyncio.run(test_download())
