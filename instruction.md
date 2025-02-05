# Project Overview
Gpt telegram bot which  works with text, images and voice for input/output and supports threads and streaming mode

# Core functionalities
## 0. Bot should be deployed on railway.app and should work in polling mode
## 1. Bot should support openai streaming mode
## 2. Bot can be added into telegram groups
## 3. Bot should support threads (user id's and can store user message history)
## 4. There should be a settings panel, so one can edit 
the following parameters for text model:
-- base url of openai compatible model
-- model itself (either chose from the short list of 4 most popular openai models or enter manually the name of the model)
-- temperature (from 0 to 1, of possible use progress bar or something like this)
-- max tokens (from 150 till infinity)

## 5. There should be a settings panel, so one can edit 
the following parameters for images model:
### base url of openai compatible image model
### model itself (either chose from the short list of most popular llm image models or enter manually the name of the model)
### all Key Parameters and Features of the image model
### handlers for each image setting (base_url, model, size, quality, style, hdr)
### get_image_settings and update_image_settings methods

## 6. There should be a settings panel, so one can edit 
parameters for voice model

## 7. There should be an option to clear message history for a user
## 8. validation for user inputs
## 9. confirmation dialogs for critical settings changes
## 10. Implement settings export/import functionality
## 11. Implement creating new images based on image and text input combined
## 12. Implement all needed logging and debugging into the code base, so it could be easily turned off after the project is perfectly running in production and turned back on when it is necessairy to troubleshoot possible issues
## 13. Create a compehensible README.md file in Russian for this project


# Documentation
## Example of OpenAI python streaming request
```
from openai import OpenAI

client = OpenAI()

stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say this is a test"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```


# Project file structure
/gpt-telegram-bot
│
├── main.py
├── bot.py
├── settings.py
├── handlers.py
├── utils.py
├── requirements.txt
├── railway.json
├── Procfile
└── README.md