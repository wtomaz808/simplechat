import openai
import pandas as pd
import os
import re
import tempfile
import matplotlib.pyplot as plt

# Load your DataFrame
df = pd.read_csv('your_data.csv')

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def answer_question(df, question):
    # Convert DataFrame to a string (you may limit the rows for brevity)
    df_string = df.head().to_string()

    # Construct the prompt
    prompt = f"""
You are a Python expert working with pandas DataFrames. Given the following DataFrame:

{df_string}

Write Python code to answer the following question:

\"\"\"{question}\"\"\"

Ensure the code is safe and does not modify the DataFrame in unintended ways. If the question involves plotting or generating a chart, save the figure to a temporary directory.

Only provide the code necessary to answer the question. Do not include explanations.
"""

    # Call OpenAI API to generate code
    response = openai.Completion.create(
        engine='code-davinci-002',  # Use an appropriate code model
        prompt=prompt,
        max_tokens=200,
        temperature=0,
        stop=None
    )

    code = response.choices[0].text.strip()

    # Clean up the code (optional)
    code = re.sub(r'```python|```', '', code)

    # Prepare a local namespace for code execution
    local_vars = {'df': df.copy(), 'plt': plt}

    # Safely execute the generated code
    try:
        exec(code, {}, local_vars)
        # Retrieve 'result' or any other variable defined in the code
        result = local_vars.get('result')
        
        # Handle plots
        if 'plt' in code:
            temp_dir = tempfile.gettempdir()
            plot_path = os.path.join(temp_dir, 'plot.png')
            plt.savefig(plot_path)
            plt.close()
            print(f"Plot saved to {plot_path}")
        
        return result if result is not None else "Code executed successfully."
    except Exception as e:
        return f"An error occurred while executing the code: {e}"

# Example usage
question = "What is the average age of the participants grouped by gender?"
result = answer_question(df, question)
print(result)
