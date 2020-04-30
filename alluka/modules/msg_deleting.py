from alluka.events import register
from alluka.modules.helper_funcs.telethon.chat_status import user_is_admin, can_delete_messages



@register(pattern="^/purge")
async def purge(event):
    if event.from_id == None:
        return

    chat = event.chat_id

    if not await user_is_admin(user_id=event.from_id, message=event):
        await event.reply(chat, "Who dis non-admin telling me what to do?")
        return

    if not await can_delete_messages(message=event):
        await event.reply(chat, "I can't delete messages here! Make sure I'm admin and can delete other user's messages.")
        return

    msg = await event.get_reply_message()
    if not msg:
        await event.reply(chat, "Reply to a message to select where to start purging from.")
        return
    msgs = []
    msg_id = msg.id
    delete_to = event.message.id - 1
    await event.client.delete_messages(chat, event.message.id)

    msgs.append(event.reply_to_msg_id)
    for m_id in range(delete_to, msg_id - 1, -1):
        msgs.append(m_id)
        if len(msgs) == 100:
            await event.client.delete_messages(chat, msgs)
            msgs = []

    await event.client.delete_messages(chat, msgs)
    text = (chat, "Purge completed.")
    await event.respond(text, parse_mode='md')


@register(pattern="^/del$")
async def delet(event):
    if event.from_id == None:
        return

    chat = event.chat_id

    if not await user_is_admin(user_id=event.from_id, message=event):
        await event.reply(chat, "Who dis non-admin telling me what to do?")
        return

    if not await can_delete_messages(message=event):
        await event.reply(chat, "I can't delete messages here! Make sure I'm admin and can delete other user's messages.")
        return

    msg = await event.get_reply_message()
    if not msg:
        await event.reply(chat, "Reply to a message to select where to start purging from.")
        return
    currentmsg = event.message
    chat = await event.get_input_chat()
    delall = [msg, currentmsg]
    await event.client.delete_messages(chat, delall)



__help__ = """
*Admin only:*
 - /del: deletes the message you replied to
 - /purge: deletes all messages between this and the replied to message.
"""

__mod_name__ = "Purges"
