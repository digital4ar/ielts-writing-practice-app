from flask import Flask, render_template, request
import openai
import os
from dotenv import load_dotenv
import json
import random

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Load prompts from JSON
with open("prompts.json", "r") as f:
    prompt_data = json.load(f)
    prompts_list = prompt_data["prompts"]

app = Flask(__name__)

def word_count(text):
    return len(text.strip().split())

def get_gpt_feedback(prompt_text, user_writing, task_number, task_type):
    system_prompt = f"""
You are an experienced IELTS Writing Examiner. Evaluate the following Task {task_number} ({task_type}) response.
Provide detailed feedback including Band Score, Strengths, Weaknesses, and Improvement Tips.
Also, provide a full model answer based on the given prompt.

User Prompt: {prompt_text}
User Writing: {user_writing}

Return your response in exactly this format:

Band Score: [score]
Strengths:
- [point 1]
- [point 2]
Weaknesses:
- [point 1]
- [point 2]
Improvement Tips:
- [tip 1]
- [tip 2]
Model Answer:
[full model answer here]

📚 Useful Resources:
📘 [British Council Writing Tips](https://learnenglish.britishcouncil.org/skills/writing)   
📝 [IDP IELTS Writing Guide](https://www.ieltsidpindia.com/information/prepare-for-ielts/ielts-writing)   
🎯 [IELTS Liz - Task 2 Practice](https://ieltsliz.com/ielts-writing-task-2/)   
🧠 [IELTS Mastery Hub](https://www.sparkskytech.com/shop/learning-education/ielts-mastery-hub)   
📺 [My IELTS Writing YouTube Playlist](https://www.youtube.com/playlist?list=PLaSmN7qMfXNQH1rV-Ksj7xEnKTOgxTRfo)
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_writing}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error getting feedback: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    writing = ""
    task_type = "Academic"
    task_number = "1"
    prompt_text = ""

    if request.method == "POST":
        writing = request.form.get("writing", "")
        task_type = request.form.get("task_type", "Academic")
        task_number = request.form.get("task_number", "1")
        prompt_select = request.form.get("prompt_select", "")
        prompt_text = prompt_select or request.form.get("prompt_text", "")

        # Word count validation 
        min_words = 250 if task_number == "2" else 150
        if word_count(writing) < min_words:
            result = f"⚠️ Please write at least {min_words} words for Task {task_number}."
        else:
            result = get_gpt_feedback(prompt_text, writing, task_number, task_type)

    return render_template("index.html",
                           writing=writing,
                           task_type=task_type,
                           task_number=task_number,
                           prompt_text=prompt_text,
                           result=result,
                           prompts=prompts_list)