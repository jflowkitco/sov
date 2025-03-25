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
                'ctl00$MainContent$txtAddress': address_input,
                'ctl00$MainContent$btnSearch': 'Search',
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            result = session.post(search_url, data=payload, headers=headers)
            result_soup = BeautifulSoup(result.text, 'html.parser')

            details_div = result_soup.find("div", id="MainContent_pnlResults")
            if not details_div:
                st.warning("No property found. Try a full street address like '123 N Main St'.")
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

