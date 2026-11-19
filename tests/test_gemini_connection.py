
import os
from dotenv import load_dotenv
from google import genai

MODEL_NAME = "gemini-3.8-flash"


def test_gemini_connection():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return

    try:
        print("\n========== GEMINI INTERACTIONS API TEST ==========")
        print("Model:", MODEL_NAME)
        print("Connecting to Gemini...")

        client = genai.Client(
        api_key=api_key,
        http_options={"timeout": 30000}
        ) 

        interaction = client.interactions.create(
            model=MODEL_NAME,
            input="Reply with exactly this sentence: Gemini connection successful.",
            timeout=30
        )

        response = interaction.output_text

        if not response:
            print("ERROR: Gemini returned an empty response.")
            return

        print("\nGemini response:")
        print(response)
        print("\nSUCCESS: Gemini Interactions API is working.")

    except Exception as error:
        print("\nERROR: Gemini connection failed.")
        print("Error type:", type(error).__name__)
        print("Details:", str(error))


if __name__ == "__main__":
    test_gemini_connection()
