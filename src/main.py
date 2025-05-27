import base64
import pathlib
import chainlit as cl
import litellm
import mimetypes
import os
import json
from difflib import SequenceMatcher
from collections import defaultdict

def is_image_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith('image/')

def load_faqs():
    try:
        with open('faqs.json', 'r', encoding='utf-8') as f:
            return json.load(f)['faqs']
    except Exception as e:
        print(f"Error loading FAQs: {str(e)}")
        return []

def normalize_text(text):
    # Remove common variations and normalize the text
    text = text.lower()
    text = text.replace('چطور', 'چیست')
    text = text.replace('چگونه', 'چیست')
    text = text.replace('رو', '')
    text = text.replace('به من', '')
    text = text.replace('بگو', '')
    text = text.replace('بگید', '')
    text = text.replace('؟', '')
    text = text.replace('?', '')
    text = text.replace('!', '')
    text = text.replace('،', '')
    text = text.replace(',', '')
    return text.strip()

def get_context_from_history(messages, max_history=3):
    """Extract relevant context from chat history"""
    context = []
    category_counts = defaultdict(int)
    tag_counts = defaultdict(int)
    
    # Look at last few messages for context
    for msg in reversed(messages[-max_history:]):
        if msg["role"] == "user":
            context.append(msg["content"])
        elif msg["role"] == "system" and "Category:" in msg["content"]:
            # Extract category and tags from previous system messages
            lines = msg["content"].split('\n')
            for line in lines:
                if line.startswith("Category:"):
                    category = line.split(":")[1].strip()
                    category_counts[category] += 1
                elif line.startswith("Tags:"):
                    tags = line.split(":")[1].strip().split(", ")
                    for tag in tags:
                        tag_counts[tag] += 1
    
    # Get the most frequent category and tags
    most_frequent_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
    most_frequent_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    most_frequent_tags = [tag for tag, _ in most_frequent_tags]
    
    return {
        "text": " ".join(context),
        "category": most_frequent_category,
        "tags": most_frequent_tags
    }

def find_best_match(question, faqs, chat_history=None, threshold=0.5):
    best_match = None
    best_score = 0
    
    normalized_question = normalize_text(question)
    
    # If we have chat history, use it to provide context
    if chat_history:
        context = get_context_from_history(chat_history)
        normalized_context = normalize_text(context["text"])
        # Combine question with context for better matching
        combined_text = f"{normalized_context} {normalized_question}"
    else:
        combined_text = normalized_question
        context = {"category": None, "tags": []}
    
    # First try exact question match
    for faq in faqs:
        normalized_faq = normalize_text(faq['question'])
        score = SequenceMatcher(None, combined_text, normalized_faq).ratio()
        
        # Boost score if category matches
        if context["category"] and faq["category"] == context["category"]:
            score *= 1.2
        
        # Boost score for matching tags
        matching_tags = set(faq["tags"]) & set(context["tags"])
        if matching_tags:
            score *= (1 + 0.1 * len(matching_tags))
        
        if score > best_score and score > threshold:
            best_score = score
            best_match = faq
    
    # If no good match found, try matching with tags
    if not best_match or best_score < 0.7:
        question_words = set(combined_text.split())
        for faq in faqs:
            tag_matches = sum(1 for tag in faq['tags'] if tag in question_words)
            if tag_matches > 0:
                score = tag_matches / len(faq['tags'])
                
                # Boost score if category matches
                if context["category"] and faq["category"] == context["category"]:
                    score *= 1.2
                
                if score > best_score:
                    best_score = score
                    best_match = faq
    
    return best_match

@cl.on_chat_start
def start_chat():
    system_message = {
        "role": "system",
        "content": "شما دستیار هوشمند ارون هستید. به زبان فارسی فکر می‌کنید و پاسخ می‌دهید. پاسخ‌های خود را به صورت طبیعی و بدون معرفی خود ارائه دهید، مگر اینکه کاربر مستقیماً از شما بخواهد که خود را معرفی کنید. از گفتن عباراتی مانند 'دستیار هوشمند ارون پاسخ داد' خودداری کنید. هرگز از کلمه 'think' یا 'فکر' در پاسخ‌های خود استفاده نکنید."
    }

    cl.user_session.set("message_history", [system_message])
    cl.user_session.set("faqs", load_faqs())

@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message("")
    await msg.send()

    system_message = {
        "role": "system",
        "content": "شما دستیار هوشمند ارون هستید. به زبان فارسی فکر می‌کنید و پاسخ می‌دهید. پاسخ‌های خود را به صورت طبیعی و بدون معرفی خود ارائه دهید، مگر اینکه کاربر مستقیماً از شما بخواهد که خود را معرفی کنید. از گفتن عباراتی مانند 'دستیار هوشمند ارون پاسخ داد' خودداری کنید. هرگز از کلمه 'think' یا 'فکر' در پاسخ‌های خود استفاده نکنید."
    }

    messages = cl.user_session.get("message_history")
    faqs = cl.user_session.get("faqs")

    # Check if the message matches any FAQ, using chat history for context
    faq_match = find_best_match(message.content, faqs, messages)
    if faq_match:
        # Return the exact FAQ answer
        await msg.stream_token(faq_match['answer'])
        await msg.update()
        return

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
        model="ollama/" + os.getenv("OLLAMA_MODEL", "gemma"),
        messages=messages,
        api_base="http://ollama:11434",
        stream=True
    )

    async for chunk in response:
        if chunk:
            content = chunk.choices[0].delta.content
            if content and not content.startswith("<think>"):
                await msg.stream_token(content)
    messages.append({"role": "assistant", "content": msg.content})
    await msg.update()
