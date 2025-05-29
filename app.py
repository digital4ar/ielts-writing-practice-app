from flask import Flask, render_template, request
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        user_writing = request.form["writing"]
        task_type = request.form["task_type"]
        task_number = request.form["task_number"]
        prompt_text = request.form.get("prompt_text", "Describe the chart below.")

        # Call GPT for feedback
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an IELTS Writing Examiner."},
                    {"role": "user", "content": f"User Prompt: {prompt_text}\nUser Writing: {user_writing}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            result = response.choices[0].message.content.strip()
        except Exception as e:
            result = f"⚠️ Error getting feedback: {str(e)}"

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)