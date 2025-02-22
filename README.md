# Business AI Bot

## Overview
Business AI Bot helps small businesses automatically respond to customer inquiries using FAQs stored in a Google Sheet. The AI agent can:
- Read FAQs from a Google Sheets document
- Match customer queries to the most relevant FAQ
- Provide intelligent responses
- Identify potential lead opportunities

## Data Source
The Business AI Bot uses a public Google Sheet as its knowledge base:
- **Sheet URL**: [Small Business FAQ Sheet](https://docs.google.com/spreadsheets/d/106defDbrpHum7-Yrdk9P_rnRwjm3LLRV3k4NAarloik/)
- **Sheet Name**: FAQs

### Accessing the Sheet
1. The sheet is publicly viewable
2. You can customize the FAQs by editing the Google Sheet
3. Columns should follow the structure:
   - Question
   - Answer
   - Keywords
   - Lead_Potential

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Run the Business AI Bot: `python small_business_chatbot.py`

## FAQ Sheet Structure
Your Google Sheet should have columns:
- Question: The customer inquiry
- Answer: The corresponding response
- Keywords: Comma-separated keywords to help match queries
- Lead_Potential: 'Yes' or 'No' to indicate potential sales opportunity

## Running the Business AI Bot
```bash
python small_business_chatbot.py
```

## Customization
Modify the `generate_response()` method to add more sophisticated matching or response generation techniques.
