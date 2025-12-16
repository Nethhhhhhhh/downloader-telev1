from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from handlers import keyboards

router = Router()

@router.callback_query(F.data == "language")
async def cb_language(callback: CallbackQuery):
    text = "<b>🌍 Select your language:</b>"
    await callback.message.edit_text(text, reply_markup=keyboards.language_menu())

@router.callback_query(F.data.startswith("lang_"))
async def cb_set_language(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    
    # Map code to name for confirmation message
    lang_names = {
        "en": "English",
        "km": "Khmer",
        "vi": "Vietnamese",
        "id": "Indonesian",
        "hi": "Hindi",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean"
    }
    
    lang_name = lang_names.get(lang_code, lang_code)
    
    text = (
        f"✅ <b>Language set to {lang_name}!</b>\n\n"
        "<i>Note: Actual translation logic is not yet implemented.</i>"
    )
    
    # Go back to main menu after short delay or just show main menu button
    # For now, let's just show the main menu again with the confirmation
    await callback.message.edit_text(text, reply_markup=keyboards.main_menu())
