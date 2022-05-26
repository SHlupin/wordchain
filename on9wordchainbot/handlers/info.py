import asyncio
import time
from datetime import datetime

from aiogram import types
from aiogram.dispatcher.filters import ChatTypeFilter, CommandHelp, CommandStart
from aiogram.utils.deep_linking import get_start_link
from aiogram.utils.markdown import quote_html

from .. import GlobalState, bot, dp
from ..constants import GameState
from ..utils import inline_keyboard_from_button, send_private_only_message
from ..words import Words


@dp.message_handler(CommandStart("help"), ChatTypeFilter([types.ChatType.PRIVATE]))
@dp.message_handler(CommandHelp())
async def cmd_help(message: types.Message) -> None:
    if message.chat.id < 0:
        await message.reply(
            "Lütfen bu komutu özel olarak kullanın.",
            allow_sending_without_reply=True,
            reply_markup=inline_keyboard_from_button(
                types.InlineKeyboardButton("Help message", url=await get_start_link("help"))
            )
        )
        return

    await message.reply(
        (
            "/gameinfo - Oyun modu açıklamaları\n"
            "/troubleshoot - Sık karşılaşılan sorunları çözün\n"
            "/reqaddword - Sözcük eklenmesini iste\n"
            "/feedback - Bot sahibine geri bildirim gönder\n\n"
            "[Sen](tg://settings. "
            "botla ilgili sorunlarınız varsa *İngilizce / Türkçe* dilinde.\n"
            "Group: @mutsuz_panda\n"
            "Channel (durum güncellemeleri): @mutsuz_panda\n"
            "Source Code: [Meyitzade](https://t.me/mutsuz_panda)\n"
            "Tarafından tasarlanan destansı simge [Adri](tg://user?id=5360157654)"
        ),
        disable_web_page_preview=True,
        allow_sending_without_reply=True
    )


@dp.message_handler(commands="gameinfo")
@send_private_only_message
async def cmd_gameinfo(message: types.Message) -> None:
    await message.reply(
        (
            "/startclassic - Klasik oyun\n"
            "Oyuncular sırayla bir önceki kelimenin son harfiyle başlayan kelimeleri gönderir.\n\n"
            "Variants:\n"
            "/starthard - Zor mod oyunu\n"
            "/startchaos - Kaos oyunu (rastgele dönüş sırası)\n"
            "/startcfl - Seçilen ilk harf oyunu\n"
            "/startrfl - Rastgele ilk harf oyunu\n"
            "/startbl - Yasaklı harfler oyunu\n"
            "/startrl - Gerekli harf oyunu\n\n"
            "/startelim - Eleme oyunu\n"
            "Her oyuncunun puanı, toplam kelime uzunluğudur.. "
            "En düşük puan alan oyuncular her turdan sonra elenir.\n\n"
            "/startmelim - Karışık eleme oyunu\n"
            "Farklı modlara sahip  oyun @Emily_utagbot'de deneyin."
        ),
        allow_sending_without_reply=True
    )


@dp.message_handler(commands="troubleshoot")
@send_private_only_message
async def cmd_troubleshoot(message: types.Message) -> None:
    await message.reply(
        (
            "Bu adımlar, yönetici ayrıcalıklarına sahip olduğunuzu varsayar.. "
            "Bunu yapmazsanız, lütfen bunun yerine bir grup yöneticisinden kontrol etmesini isteyin.\n\n"
            "<b>Bot, <code>/start[mode]</code></b> işlevine yanıt vermiyorsa, şunları kontrol edin:\n"
            "1. Bot, grubunuzda yok / sessize alındı "
            "\u27a1\ufe0f Botu grubunuza ekleyin / Botun sesini açın\n"
            "2. Yavaş mod etkin \u27a1\ufe0f Yavaş modu devre dışı bırak\n"
            "3. Birisi son zamanlarda grubunuzdaki komutları spam olarak gönderdi "
            "\u27a1\ufe0f Grubunuzda botun hızı sınırlı, sabırla bekleyin\n"
            "4. Bot, <code>/ping</code>'e yanıt vermiyor "
            "\u27a1\ufe0f Bot büyük olasılıkla çevrimdışı, durum güncellemeleri için @mutsuz_panda kontrol edin\n\n"
            "<b>Bot grubunuza eklenemiyorsa</b>:\n"
            "1. Bir grupta en fazla 20 bot olabilir. Bu sınıra ulaşılıp ulaşılmadığını kontrol edin.\n\n"
            "Başka sorunlarla karşılaşırsanız, lütfen sahibim ile iletişime geçin. @mutsuz_panda"
        ),
        parse_mode=types.ParseMode.HTML,
        allow_sending_without_reply=True
    )


@dp.message_handler(commands="ping")
async def cmd_ping(message: types.Message) -> None:
    t = time.time()
    msg = await message.reply("Pong!", allow_sending_without_reply=True)
    await msg.edit_text(f"Pong! `{time.time() - t:.3f}s`")


@dp.message_handler(commands="chatid")
async def cmd_chatid(message: types.Message) -> None:
    await message.reply(f"`{message.chat.id}`", allow_sending_without_reply=True)


@dp.message_handler(commands="runinfo")
async def cmd_runinfo(message: types.Message) -> None:
    build_time_str = (
        "{0.day}/{0.month}/{0.year}".format(GlobalState.build_time)
        + " "
        + str(GlobalState.build_time.time())
        + " HKT"
    )
    uptime = datetime.now().replace(microsecond=0) - GlobalState.build_time
    await message.reply(
        (
            f"Build time: `{build_time_str}`\n"
            f"Uptime: `{uptime.days}.{str(uptime).rsplit(maxsplit=1)[-1]}`\n"
            f"Words in dictionary: `{Words.count}`\n"
            f"Total games: `{len(GlobalState.games)}`\n"
            f"Running games: `{len([g for g in GlobalState.games.values() if g.state == GameState.RUNNING])}`\n"
            f"Players: `{sum(len(g.players) for g in GlobalState.games.values())}`"
        ),
        allow_sending_without_reply=True
    )


@dp.message_handler(is_owner=True, commands="playinggroups")
async def cmd_playinggroups(message: types.Message) -> None:
    if not GlobalState.games:
        await message.reply("No groups are playing games.", allow_sending_without_reply=True)
        return

    groups = []

    async def append_group(group_id: int) -> None:
        try:
            group = await bot.get_chat(group_id)
            url = await group.get_url()
            # TODO: weakref exception is aiogram bug, wait fix
        except TypeError as e:
            if str(e) == "cannot create weak reference to 'NoneType' object":
                text = "???"
            else:
                text = f"(<code>{e.__class__.__name__}: {e}</code>)"
        except Exception as e:
            text = f"(<code>{e.__class__.__name__}: {e}</code>)"
        else:
            if url:
                text = f"<a href='{url}'>{quote_html(group.title)}</a>"
            else:
                text = f"<b>{group.title}</b>"

        if group_id not in GlobalState.games:  # In case the game ended during API calls
            return

        groups.append(
            text + (
                f" <code>{group_id}</code> "
                f"{len(GlobalState.games[group_id].players_in_game)}/{len(GlobalState.games[group_id].players)}P "
                f"{GlobalState.games[group_id].turns}W "
                f"{GlobalState.games[group_id].time_left}s"
            )
        )

    await asyncio.gather(*[append_group(gid) for gid in GlobalState.games])
    await message.reply(
        "\n".join(groups), parse_mode=types.ParseMode.HTML,
        disable_web_page_preview=True, allow_sending_without_reply=True
    )
