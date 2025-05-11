import base64
import pathlib
import chainlit as cl
import litellm
import mimetypes
import os

def is_image_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith('image/')

@cl.on_chat_start
def start_chat():
    system_message = {
        "role": "system",
        "content": "شما دستیار هوشمند ارون هستید. به زبان فارسی فکر می‌کنید و پاسخ می‌دهید. پاسخ‌های خود را به صورت طبیعی و بدون معرفی خود ارائه دهید، مگر اینکه کاربر مستقیماً از شما بخواهد که خود را معرفی کنید. از گفتن عباراتی مانند 'دستیار هوشمند ارون پاسخ داد' خودداری کنید."
    }

    cl.user_session.set("message_history", [system_message])


@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message("")
    await msg.send()

    system_message = {
        "role": "system",
        "content": "شما دستیار هوشمند ارون هستید. به زبان فارسی فکر می‌کنید و پاسخ می‌دهید. پاسخ‌های خود را به صورت طبیعی و بدون معرفی خود ارائه دهید، مگر اینکه کاربر مستقیماً از شما بخواهد که خود را معرفی کنید. از گفتن عباراتی مانند 'دستیار هوشمند ارون پاسخ داد' خودداری کنید."
    }

    messages = cl.user_session.get("message_history")

    if len(message.elements) > 0:
        for element in message.elements:
            file_path = pathlib.Path(element.path)
            if file_path.exists() and file_path.is_file():
                try:
                    if is_image_file(str(file_path)):
                        with open(file_path, 'rb') as f:
                            file_content = base64.b64encode(f.read()).decode('utf-8')
                            messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "image_url": {
                                            "url": f"data:image/{mimetypes.guess_type(str(file_path))[0]};base64,{file_content}"
                                        }
                                    }
                                ]
                            })
                    else:
                        file_content = file_path.read_text()
                        messages.append({"role": "user", "content": file_content})
                except Exception as e:
                    print(f"Error processing file {element.path}: {str(e)}")
            else:
                print(f"File {element.path} does not exist")

    messages.append({"role": "user", "content": message.content})
    response = await litellm.acompletion(
        model="ollama/" + os.getenv("OLLAMA_MODEL", "hf.co/modashtizade/DeepSeek-R1-Distill-Llama-8B-Persian:Q4_K_M"),
        messages=messages,
        api_base="http://ollama:11434",
        stream=True
    )

    async for chunk in response:
        if chunk:
            content = chunk.choices[0].delta.content
            if content:
                await msg.stream_token(content)
    messages.append({"role": "assistant", "content": msg.content})
    await msg.update()
