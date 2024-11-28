import json
import os

import requests
import tiktoken
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from the .env file
load_dotenv()


def count_tokens(prompt):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-instruct")
    tokens = encoding.encode(prompt)
    return len(tokens)


class ChatGPTController:
    api_key = os.getenv("OPENAI_API_KEY")

    def __init__(self):
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def get_product_info(self, search_query, base64_image):
        prompt = f"""
        Does this product name, {search_query}, match the amazon product image provided? If so, what is the price of the product on amazon?
        Respond in the following JSON format:
        {{
            "id": "Product ID",
            "price": "Price",
            "match": "Match Percentage Estimate"
        }}
        """

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        # Check if the response is valid
        if response.status_code != 200:
            print(f"Error: Received response with status code {response.status_code}")
            return None

        try:
            response_json = response.json()

            # Extracting the first choice and its message content
            if response_json.get('choices'):
                match_info = response_json['choices'][0]['message']['content']
                # Parse the JSON string to a dictionary
                match_info_dict = json.loads(match_info.strip('```json\n'))

                # Ensure the expected keys exist and are in the correct format
                if all(key in match_info_dict for key in ["id", "price", "match"]):
                    return match_info_dict
                else:
                    print("Error: Missing expected keys in the response JSON.")
                    return None

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing response JSON: {e}")
            return None
