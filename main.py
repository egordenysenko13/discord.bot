import disnake as discord
from disnake.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True  # нужно для чтения текста команд
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

VERIFY_CHANNEL_ID = 1406674041410162799   # канал, куда заходят пользователи
CHECK_CHANNEL_ID = 1406675838778212513   # канал для проверки
ROLE_ID = 1406674677857910785            # роль, которую выдавать

# Словарь: message_id из CHECK_CHANNEL -> user_id
pending_checks = {}

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Если пользователь прислал картинку в канал верификации
    if message.channel.id == VERIFY_CHANNEL_ID and message.attachments:
        check_channel = bot.get_channel(CHECK_CHANNEL_ID)
        if check_channel:
            # Пересылаем вложения в канал проверки
            files = [await a.to_file() for a in message.attachments]
            forwarded = await check_channel.send(
                f"Скриншот от {message.author.mention}", 
                files=files
            )
            # сохраняем связь чтобы потом понять кого принять
            pending_checks[forwarded.id] = message.author.id

    await bot.process_commands(message)

@bot.command()
async def accept(ctx):
    """Одобрить заявку"""
    if ctx.message.reference:  # если команда в ответ на сообщение
        ref_id = ctx.message.reference.message_id
        if ref_id in pending_checks:
            user_id = pending_checks.pop(ref_id)
            guild = ctx.guild
            member = guild.get_member(user_id)
            if member:
                role = guild.get_role(ROLE_ID)
                if role:
                    await member.add_roles(role)
                    await ctx.send(f"{member.mention} одобрен ✅ и получил роль!")
                else:
                    await ctx.send("❌ Роль не найдена.")
            else:
                await ctx.send("❌ Пользователь не найден.")
        else:
            await ctx.send("❌ Неизвестная заявка.")

@bot.command()
async def refuse(ctx):
    """Отклонить заявку"""
    if ctx.message.reference:
        ref_id = ctx.message.reference.message_id
        if ref_id in pending_checks:
            user_id = pending_checks.pop(ref_id)
            member = ctx.guild.get_member(user_id)
            await ctx.send(f"❌ {member.mention} отклонен.")
        else:
            await ctx.send("❌ Неизвестная заявка.")

# ---- Запуск бота ----
TOKEN = os.getenv("DISCORD_TOKEN")  # токен хранится в переменной окружения
if TOKEN is None:
    raise ValueError("Не найден DISCORD_TOKEN в переменных окружения!")

bot.run(TOKEN)
