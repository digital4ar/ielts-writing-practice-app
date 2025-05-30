from flask import Flask, render_template, request, send_file
import openai
import os
from dotenv import load_dotenv
import json
import csv
import datetime
from weasyprint import HTML
import tempfile

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Load prompts from JSON
with open("prompts.json", "r", encoding="utf-8") as f:
    prompt_data = json.load(f)
    prompts_list = prompt_data["prompts"]

app = Flask(__name__)

def word_count(text):
    return len(text.strip().split())

def get_gpt_feedback(prompt_text, user_writing, task_number, task_type):
    system_prompt = f"""
You are an experienced IELTS Writing Examiner. Evaluate the following Task {task_number} ({task_type}) response using official IELTS scoring criteria:
- Task Response / Achievement
- Coherence & Cohesion
- Lexical Resource
- Grammatical Range & Accuracy

Provide a realistic Band Score from 4.0 to 8.5 — do NOT limit yourself to 6.0–7.5.
If the writing is clearly below standard, feel free to give lower scores (e.g., 5.0 or 4.5).

Also provide:
- Strengths: What was done well?
- Weaknesses: Where improvements are needed
- Improvement Tips: Practical suggestions
- A full model answer that reflects high-scoring writing style and length

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
📺 [YouTube Playlist](https://www.youtube.com/@SparkSkyTech)   
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
def home():
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

        min_words = 250 if task_number == "2" else 150
        if word_count(writing) < min_words:
            result = f"⚠️ Please write at least {min_words} words for Task {task_number}."
        else:
            result = get_gpt_feedback(prompt_text, writing, task_number, task_type)

            # Save submission to CSV
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("submissions.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, task_type, task_number, prompt_text[:100], writing[:100]])

    return render_template(
        "index.html",
        writing=writing,
        task_type=task_type,
        task_number=task_number,
        prompt_text=prompt_text,
        result=result,
        prompts=prompts_list
    )

@app.route("/download", methods=["POST"])
def download():
    result = request.form.get("result", "")
    prompt_text = request.form.get("prompt_text", "")
    writing = request.form.get("writing", "")

    # Extract Band Score
    band_score = "Not available"
    if result.startswith("Band Score:"):
        band_score = result.splitlines()[0]

    html_content = f"""
    <html>
      <head>
        <style>
          body {{
            font-family: Arial, sans-serif;
            padding: 30px;
            background: #ffffff;
            color: #333;
          }}
          h1 {{
            color: #001f3f;
            border-bottom: 2px solid #001f3f;
            padding-bottom: 10px;
          }}
          pre {{
            white-space: pre-wrap;
            background: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #001f3f;
          }}
          .section {{
            margin-top: 20px;
          }}
        </style>
      </head>
      <body>
        <h1>IELTS Writing Feedback Report</h1>

        <div class="section">
          <h2>{band_score}</h2>
        </div>

        <div class="section">
          <h2>Prompt:</h2>
          <p>{prompt_text}</p>
        </div>

        <div class="section">
          <h2>Your Writing:</h2>
          <p>{writing}</p>
        </div>

        <div class="section">
          <h2>Feedback:</h2>
          <pre>{result}</pre>
        </div>

        <p><small>Generated by SparkSkyTech IELTS Writing App</small></p>
      </body>
    </html>
    """

    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, "ielts_feedback.pdf")

    HTML(string=html_content).write_pdf(pdf_path)

    return send_file(pdf_path, as_attachment=True, download_name="ielts_writing_feedback.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))