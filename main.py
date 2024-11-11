import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import config

TOKEN = config.TOKEN_BOT
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Define registration states
class Registration(StatesGroup):
    choosing_role = State()
    programmer_name = State()
    programmer_age = State()
    programmer_university = State()
    custom_university = State()
    programmer_faculty = State()
    programmer_photo = State()
    programmer_specialty = State()
    choosing_language = State()
    github_link = State()
    resume_link = State()
    about_me = State()
    founder_name = State()
    founder_project = State()

# Languages by specialty
languages_by_specialty = {
    "front-разработка": ["JavaScript", "TypeScript", "HTML", "CSS", "React", "Vue.js"],
    "back-разработка": ["Python", "Java", "C#", "Node.js", "PHP", "Go", "Ruby"],
    "ML-разработка": ["Python", "R", "MATLAB", "Julia", "Scala"]
}

# Main menu with "Start" and "Registration" buttons
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Start")],
        [KeyboardButton(text="Registration")]
    ],
    resize_keyboard=True
)

# /start command
@dp.message(Command(commands=["start"]))
async def start_command(message: Message):
    await message.reply("Привет! Я твой бот и готов работать.", reply_markup=main_menu)

# Registration menu to choose role
@dp.message(lambda message: message.text == "Registration")
async def registration_from_menu(message: Message, state: FSMContext):
    role_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Программист")],
            [KeyboardButton(text="Фаундер")]
        ],
        resize_keyboard=True
    )
    await message.reply("Выберите вашу роль:", reply_markup=role_keyboard)
    await state.set_state(Registration.choosing_role)

# Role selection handling
@dp.message(Registration.choosing_role)
async def choose_role(message: Message, state: FSMContext):
    if message.text == "Программист":
        await message.reply("Вы выбрали Программист. Пожалуйста, введите ваше имя:")
        await state.set_state(Registration.programmer_name)
    elif message.text == "Фаундер":
        await message.reply("Вы выбрали Фаундер. Пожалуйста, введите ваше имя:")
        await state.set_state(Registration.founder_name)
    else:
        await message.reply("Пожалуйста, выберите одну из предложенных ролей: Программист или Фаундер.")

# Programmer registration: handle name
@dp.message(Registration.programmer_name)
async def process_programmer_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Пожалуйста, введите ваш возраст:")
    await state.set_state(Registration.programmer_age)

# Programmer registration: handle age
@dp.message(Registration.programmer_age)
async def process_programmer_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("Пожалуйста, введите числовое значение возраста.")
        return
    await state.update_data(age=int(message.text))
    
    # University selection keyboard
    university_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="НИУ ВШЭ")],
            [KeyboardButton(text="моего вуза нет в списке")]
        ],
        resize_keyboard=True
    )
    await message.reply("Пожалуйста, выберите ваш университет:", reply_markup=university_keyboard)
    await state.set_state(Registration.programmer_university)

# Programmer registration: handle university selection
@dp.message(Registration.programmer_university)
async def process_programmer_university(message: Message, state: FSMContext):
    if message.text == "НИУ ВШЭ":
        await state.update_data(university="НИУ ВШЭ")
        await message.reply("Пожалуйста, укажите ваш факультет:")
        await state.set_state(Registration.programmer_faculty)
    elif message.text == "моего вуза нет в списке":
        await message.reply(
            "Сейчас мы находимся в beta режиме, пока продукт доступен только для студентов НИУ ВШЭ, "
            "но скоро мы откроем доступ и для вашего вуза! Спасибо за понимание!"
        )
        await state.clear()  
    else:
        await message.reply("Пожалуйста, выберите один из предложенных вариантов.")

# Programmer registration: handle faculty
@dp.message(Registration.programmer_faculty)
async def process_programmer_faculty(message: Message, state: FSMContext):
    await state.update_data(faculty=message.text)
    await message.reply("Пожалуйста, отправьте ваше фото для профиля:")
    await state.set_state(Registration.programmer_photo)

# Programmer registration: handle photo
@dp.message(Registration.programmer_photo, F.content_type == 'photo')
async def process_programmer_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id  
    await state.update_data(photo_id=photo_id)

    specialty_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="front-разработка")],
            [KeyboardButton(text="back-разработка")],
            [KeyboardButton(text="ML-разработка")],
            [KeyboardButton(text="Готово ✅")]
        ],
        resize_keyboard=True
    )
    await message.reply("Выберите одну или несколько специальностей (нажмите 'Готово ✅', когда закончите):", reply_markup=specialty_keyboard)
    await state.set_state(Registration.programmer_specialty)

# Programmer registration: handle specialty selection
@dp.message(Registration.programmer_specialty)
async def process_programmer_specialty(message: Message, state: FSMContext):
    data = await state.get_data()
    specialties = data.get("specialties", [])

    if message.text == "Готово ✅":
        await state.update_data(specialties=specialties)
        await prompt_for_languages(message, state, specialties)
    else:
        if message.text not in specialties:
            specialties.append(message.text)
            await state.update_data(specialties=specialties)
        await message.reply(f"Специальность '{message.text}' добавлена. Выберите еще или нажмите 'Готово ✅'.")

async def prompt_for_languages(message: Message, state: FSMContext, specialties):
    if specialties:
        specialty = specialties[0]
        languages_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=lang)] for lang in languages_by_specialty[specialty]] + [[KeyboardButton(text="Готово ✅")]],
            resize_keyboard=True
        )
        await message.reply(f"Выберите языки для направления '{specialty}' (нажмите 'Готово ✅', когда закончите):", reply_markup=languages_keyboard)
        await state.update_data(current_specialty=specialty)
        await state.set_state(Registration.choosing_language)

# Handle language selection
@dp.message(Registration.choosing_language)
async def process_choosing_language(message: Message, state: FSMContext):
    data = await state.get_data()
    current_specialty = data.get("current_specialty")
    languages = data.get("languages", {})

    if message.text == "Готово ✅":
        specialties = data.get("specialties", [])
        specialties.remove(current_specialty)
        await state.update_data(specialties=specialties, languages=languages)

        if specialties:
            await prompt_for_languages(message, state, specialties)
        else:
            await message.reply("Введите ссылку на GitHub или нажмите 'Пропустить'", reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True
            ))
            await state.set_state(Registration.github_link)
    else:
        languages.setdefault(current_specialty, []).append(message.text)
        await state.update_data(languages=languages)
        await message.reply(f"Язык '{message.text}' добавлен. Выберите еще или нажмите 'Готово ✅'.")

# Handle GitHub link
@dp.message(Registration.github_link)
async def process_github_link(message: Message, state: FSMContext):
    if message.text != "Пропустить":
        await state.update_data(github_link=message.text)
    await message.reply("Введите ссылку на резюме или нажмите 'Пропустить'", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True
    ))
    await state.set_state(Registration.resume_link)

# Handle resume link
@dp.message(Registration.resume_link)
async def process_resume_link(message: Message, state: FSMContext):
    if message.text != "Пропустить":
        await state.update_data(resume_link=message.text)
    await message.reply("Расскажите немного о себе или нажмите 'Пропустить'", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True
    ))
    await state.set_state(Registration.about_me)

# Handle "About Me" info and finish registration
@dp.message(Registration.about_me)
async def process_about_me(message: Message, state: FSMContext):
    if message.text != "Пропустить":
        await state.update_data(about_me=message.text)
    
    data = await state.get_data()
    name = data.get("name")
    age = data.get("age")
    university = data.get("university")
    faculty = data.get("faculty")
    photo_id = data.get("photo_id")
    github_link = data.get("github_link", "Не указано")
    resume_link = data.get("resume_link", "Не указано")
    about_me = data.get("about_me", "Не указано")
    selected_languages = "\n".join([f"{spec}: {', '.join(langs)}" for spec, langs in data.get("languages", {}).items()])

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_id,
        caption=(
            f"Регистрация завершена!\n"
            f"Вы - Программист.\n"
            f"Имя: {name}\nВозраст: {age}\nУниверситет: {university}\nФакультет: {faculty}\n"
            f"Специализации и языки:\n{selected_languages}\n\n"
            f"GitHub: {github_link}\nРезюме: {resume_link}\nО себе: {about_me}"
        ),
        reply_markup=main_menu
    )
    await state.clear()

# Main function to start the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
