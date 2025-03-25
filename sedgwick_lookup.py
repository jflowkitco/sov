import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import re

st.title("Sedgwick County Property Info Lookup")
st.write("Enter a property address in Sedgwick County, KS to retrieve details.")

address_input = st.text_input("Property Address", "123 N Main St")

search_url = "https://ssc.sedgwickcounty.org/propertytax/"

# Replace with your OpenAI API key
openai.api_key = st.secrets["openai_api_key"] if "openai_api_key" in st.secrets else "YOUR_OPENAI_API_KEY"

# Mapping for common suffix abbreviations
suffix_map = {
    "street": "St",
    "st": "St",
    "avenue": "Ave",
    "ave": "Ave",
    "drive": "Dr",
    "dr": "Dr",
    "road": "Rd",
    "rd": "Rd",
    "lane": "Ln",
    "ln": "Ln",
    "court": "Ct",
    "ct": "Ct",
    "circle": "Cir",
    "cir": "Cir",
    "place": "Pl",
    "pl": "Pl",
    "terrace": "Ter",
    "ter": "Ter",
    "boulevard": "Blvd",
    "blvd": "Blvd",
    "parkway": "Pkwy",
    "pkwy": "Pkwy"
}

# Mapping for directions
direction_map = {
    "north": "N",
    "south": "S",
    "east": "E",
    "west": "W",
    "n": "N",
    "s": "S",
    "e": "E",
    "w": "W"
}

def clean_address(address):
    words = address.lower().split()
    cleaned = []
    for word in words:
        if word in direction_map:
            cleaned.append(direction_map[word])
        elif word in suffix_map:
            cleaned.append(suffix_map[word])
        else:
            cleaned.append(word.capitalize())
    return " ".join(cleaned)

def summarize_with_gpt(property_data):
    prompt = f"""
    Summarize the following Sedgwick County property information in a concise and friendly format. Highlight the most important facts like the year built, square footage, lot size, and value.

    {property_data}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who summarizes property details."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

if st.button("Search"):
    with st.spinner("Searching Sedgwick County records..."):
        try:
            cleaned_address = clean_address(address_input)

            session = requests.Session()
            res = session.get(search_url)
            soup = BeautifulSoup(res.text, 'html.parser')

            viewstate = soup.find('input', {'id': '__VIEWSTATE'})
            event_validation = soup.find('input', {'id': '__EVENTVALIDATION'})
            viewstategen = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})

            payload = {
                '__VIEWSTATE': viewstate['value'] if viewstate else '',
                '__VIEWSTATEGENERATOR': viewstategen['value'] if viewstategen else '',
                '__EVENTVALIDATION': event_validation['value'] if event_validation else '',
                'ctl00$MainContent$txtAddress': cleaned_address,
                'ctl00$MainContent$btnSearch': 'Search',
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            result = session.post(search_url, data=payload, headers=headers)
            result_soup = BeautifulSoup(result.text, 'html.parser')

            details_div = result_soup.find("div", id="MainContent_pnlResults")
            if not details_div:
                st.warning(f"No property found for '{cleaned_address}'. Please check the spelling or try another address.")
            else:
                st.subheader("Property Details")
                rows = details_div.find_all("tr")
                property_text = ""
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) == 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        st.write(f"**{label}:** {value}")
                        property_text += f"{label}: {value}\n"

                st.subheader("🧠 GPT Summary")
                summary = summarize_with_gpt(property_text)
                st.success(summary)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
