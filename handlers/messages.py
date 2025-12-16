from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.downloader import downloader, MediaType
from handlers import keyboards
import os
import logging
import asyncio


router = Router()

class SpotifySearch(StatesGroup):
    waiting_for_query = State()

async def cleanup_later(files, delay=300):
    """
    Deletes files after a delay (default 5 minutes).
    """
    await asyncio.sleep(delay)
    for path in files:
        downloader.cleanup(path)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "<b>📥 My options:</b>\n\n"

        "⬜ <b>Instagram:</b> reels, posts & stories\n"

        "⬜ <b>Pinterest:</b> videos & stories\n"

        "⬜ <b>Tiktok:</b> videos, photos & audio\n"

        "⬜ <b>Twitter (X):</b> videos & voice\n"

        "⬜ <b>Vk:</b> videos & clips\n"
    
        "⬜ <b>Reddit:</b> videos & gifs\n"

        "⬜ <b>Twitch:</b> clips\n"

        "⬜ <b>Vimeo</b>\n"

        "⬜ <b>Ok:</b> video\n"

        "⬜ <b>Tumblr:</b> videos & audio\n"

        "⬜ <b>Dailymotion:</b> videos\n"

        "⬜ <b>Likee:</b> videos\n"

        "⬜ <b>Soundcloud</b>\n"

        "⬜ <b>Apple Music</b>\n"

        "⬜ <b>Spotify</b>\n\n"

        "⭐ <b>Subscription:</b> not active"
    )
    await message.answer(text, reply_markup=keyboards.main_menu())

@router.callback_query(F.data == "platforms")
async def cb_platforms(callback: CallbackQuery):
    text = (
        "<b>Supported Platforms:</b>\n\n"
        "🎥 <b>Video:</b>\n"
        "▫️ YouTube, Instagram, TikTok\n"
        "▫️ Twitter (X), Pinterest, Reddit\n"
        "▫️ Facebook, Twitch, Vimeo, VK, OK\n"
        "▫️ Dailymotion, Likee, Tumblr\n\n"
        "🎵 <b>Music:</b>\n"
        "▫️ Spotify, Apple Music, Soundcloud\n\n"
        "<i>Send any link to start downloading!</i>"
    )
    await callback.message.edit_text(text, reply_markup=keyboards.platforms_menu())

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    text = (
        "<b>📥 My options:</b>\n\n"

        "⬜ <b>Instagram:</b> reels, posts & stories\n"

        "⬜ <b>Pinterest:</b> videos & stories\n"

        "⬜ <b>Tiktok:</b> videos, photos & audio\n"

        "⬜ <b>Twitter (X):</b> videos & voice\n"

        "⬜ <b>Vk:</b> videos & clips\n"

        "⬜ <b>Reddit:</b> videos & gifs\n"

        "⬜ <b>Twitch:</b> clips\n"

        "⬜ <b>Vimeo</b>\n"

        "⬜ <b>Ok:</b> video\n"

        "⬜ <b>Tumblr:</b> videos & audio\n"

        "⬜ <b>Dailymotion:</b> videos\n"

        "⬜ <b>Likee:</b> videos\n"

        "⬜ <b>Soundcloud</b>\n"

        "⬜ <b>Apple Music</b>\n"

        "⬜ <b>Spotify</b>\n\n"

        "⭐ <b>Subscription:</b> not active"
    )
    await callback.message.edit_text(text, reply_markup=keyboards.main_menu())


    
@router.callback_query(F.data == "find_music_spotify")
async def cb_find_music_spotify(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎵 <b>Send me the song name or link to search on Spotify:</b>")
    await state.set_state(SpotifySearch.waiting_for_query)
    await callback.answer()

@router.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    url = message.text.strip()
    
    current_state = await state.get_state()
    is_search = False
    
    if current_state == SpotifySearch.waiting_for_query:
        is_search = True
        # format as ytsearch if not a link
        if not url.startswith(("http://", "https://")):
             url = f"ytsearch1:{url}"
        await state.clear()
    
    if not is_search and not url.startswith(("http://", "https://")):
        await message.answer("⚠️ Please send a valid URL starting with <code>http://</code> or <code>https://</code>")
        return

    status_msg = await message.answer("⏳ <b>Processing...</b>")

    # Animation Loop
    stop_animation = False
    
    async def run_animation():
        frames = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
        idx = 0
        while not stop_animation:
            try:
                if idx % 2 == 0:
                     msg_text = "🔎 <b>Searching...</b>" if is_search else "<b>Downloading...</b>"
                     await status_msg.edit_text(f"{frames[idx % len(frames)]} {msg_text}\n<i>Fetching content...</i>")
                idx += 1
                await asyncio.sleep(0.5)
            except Exception:
                break

    animation_task = asyncio.create_task(run_animation())

    try:
        # Force audio if it was a search query
        media_list = await downloader.download_media(url, force_audio=is_search)
        
        stop_animation = True
        animation_task.cancel() # Ensure it stops
        
        if not media_list:
            await status_msg.edit_text("❌ <b>Failed:</b> Could not download media.\nCheck the link or try again.")
            return

        await status_msg.edit_text("📤 <b>Uploading...</b>")

        # Sort media: Videos first, then Images, then Audio
        # Or just group them. Telegram MediaGroup allows mixing photos and videos.
        # Audio must be sent separately.
        
        album_builder = []
        audios = []
        files_to_cleanup = []

        for media in media_list:
            files_to_cleanup.append(media['path'])
            media_file = FSInputFile(media['path'])
            
            if media['type'] == MediaType.AUDIO:
                audios.append(media)
            elif media['type'] in [MediaType.VIDEO, MediaType.IMAGE]:
                # Prepare for album
                if media['type'] == MediaType.VIDEO:
                    video_thumb = FSInputFile(media['thumb']) if media.get('thumb') and os.path.exists(media['thumb']) else None
                    album_builder.append(
                        types.InputMediaVideo(
                            media=media_file,
                            caption=media['title'] if len(album_builder) == 0 else None,
                            duration=media.get('duration'),
                            width=media.get('width'),
                            height=media.get('height'),
                            thumbnail=video_thumb
                        )
                    )
                else:
                    album_builder.append(
                        types.InputMediaPhoto(
                            media=media_file,
                            caption=media['title'] if len(album_builder) == 0 else None
                        )
                    )

        # Send Album (Videos/Photos)
        # If there is only one item and it's a VIDEO, send it individually to attach buttons.
        # If it's a group, we can't attach buttons to the media group easily in the same way.
        if len(album_builder) == 1 and isinstance(album_builder[0], types.InputMediaVideo):
             single_video = album_builder[0]
             caption = (single_video.caption or "") + "\nVia @DownloaderMikitabot"
             
             # Re-construct args for answer_video because InputMediaVideo object attributes are strict
             # We need to access the underlying values
             
             # Locate the original media dict to get the raw thumb path again or reuse the InputFile?
             # accessing private attributes of FSInputFile is messy. 
             # Better to find the media item again or store it.
             # Since it's index 0...
             target_media = [m for m in media_list if m['type'] == MediaType.VIDEO][0]
             thumb_path = target_media.get('thumb')
             thumb_file = FSInputFile(thumb_path) if thumb_path and os.path.exists(thumb_path) else None

             await message.answer_video(
                 video=single_video.media,
                 caption=caption,
                 duration=single_video.duration,
                 width=single_video.width,
                 height=single_video.height,
                 thumbnail=thumb_file,

                 reply_markup=keyboards.download_success_menu(file_id=target_media.get('group_id')),
                 request_timeout=300
             )
        elif album_builder:
            # For albums, we just append Via... to the first caption if present
            if album_builder[0].caption:
                album_builder[0].caption += "\nVia @DownloaderMikitabot"
            else:
                 album_builder[0].caption = "Via @DownloaderMikitabot"
            
            # Telegram limit is 10 items per album
            chunks = [album_builder[i:i + 10] for i in range(0, len(album_builder), 10)]
            for chunk in chunks:
                await message.answer_media_group(media=chunk, request_timeout=300)
            
            # Send buttons separately for albums
            # Use group_id from first item if available
            group_id =  album_builder[0].caption.split('\nVia')[0] if album_builder else None # Hacky way if we lost it? No, get it from original media list
            # Actually for albums we probably don't want to convert all individual videos easily this way without more complex UI
            # Just enable for single videos for now as per req?
            # Or just pass the ID of the first one?
            # Let's check media_list.
            # Convert button only makes sense for single video mostly.
            
            await message.answer("✅ <b>Download Complete!</b>", reply_markup=keyboards.download_success_menu())

        # Send Audios
        for audio in audios:
            media_file = FSInputFile(audio['path'])
            caption = f"🎵 <b>{audio['title']}</b>\nVia @DownloaderMikitabot"
            await message.answer_audio(
                media_file, 
                caption=caption,
                duration=audio.get('duration'),
                thumbnail=FSInputFile(audio['thumb']) if audio.get('thumb') and os.path.exists(audio['thumb']) else None,
                reply_markup=keyboards.download_success_menu(),
                request_timeout=300
            )



        # Cleanup
        asyncio.create_task(cleanup_later(files_to_cleanup))
            
        await status_msg.delete()

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f"Handler error: {error_trace}")
        
        stop_animation = True
        animation_task.cancel()
        
        error_msg = str(e)
        if "ffmpeg" in error_msg.lower():
            await status_msg.edit_text("❌ <b>Error:</b> FFmpeg is missing on the server.\nPlease install it and restart the bot.")
        elif "[Errno 22]" in error_msg or "Invalid argument" in error_msg:
             # Detailed debug for this specific error
             await status_msg.edit_text(f"❌ <b>Error:</b> System Error (Invalid Argument).\n\nDetails:\n<pre>{error_trace[-1000:]}</pre>")
        else:
            # Show traceback for other errors too, to be safe during debugging
             await status_msg.edit_text(f"❌ <b>Error:</b> {error_msg}\n\nDebug:\n<pre>{error_trace[-500:]}</pre>")



@router.callback_query(F.data.startswith("convert_mp3:"))
async def cb_convert_mp3(callback: CallbackQuery):
    try:
        data = callback.data.split(":")
        file_id = data[1]
        
        # Search for the video file with this ID in downloads
        # We need to find the file that starts with this UUID
        target_file = None
        for file in os.listdir(downloader.download_path):
            if file.startswith(file_id) and file.endswith(('.mp4', '.mkv', '.mov', '.webm')):
                target_file = os.path.join(downloader.download_path, file)
                break
        
        if not target_file or not os.path.exists(target_file):
            await callback.answer("❌ File expired or not found.", show_alert=True)
            return

        status_msg = await callback.message.answer("⏳ <b>Converting to MP3...</b>")
        
        try:
            mp3_path = await downloader.convert_video_to_mp3(target_file)
            
            audio_file = FSInputFile(mp3_path)
            await callback.message.answer_audio(
                audio_file,
                caption="🎵 <b>Converted to MP3</b>\nVia @DownloaderMikitabot"
            )
            
            await status_msg.delete()
            asyncio.create_task(cleanup_later([mp3_path]))
            
        except Exception as e:
            await status_msg.edit_text(f"❌ <b>Conversion Failed:</b> {str(e)}")
            
    except Exception as e:
        logging.error(f"Conversion error: {e}")
        await callback.answer("❌ An error occurred.", show_alert=True)

@router.callback_query(F.data == "coming_soon")
async def cb_coming_soon(callback: CallbackQuery):
    await callback.answer("🚧 This feature is coming soon!", show_alert=True)
