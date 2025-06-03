import streamlit as st
from postal.parser import parse_address
from postal.expand import expand_address
from PIL import Image
import pytesseract

# Streamlit Interface
st.title('Address Parsing and Normalization')

# Use radio button or dropdown for controlled input selection
option = st.radio('Choose input method:', ('Enter address manually', 'Upload image of address'))

address = None  # Initialize the address variable

if option == 'Enter address manually':
    # Show text input for manual address entry
    address = st.text_input('Enter an address')

elif option == 'Upload image of address':
    # Show file uploader for image
    uploaded_file = st.file_uploader("Upload an image", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        # Open the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded image', use_column_width=True)

        # Extract text from image using pytesseract
        address = pytesseract.image_to_string(image)
        st.write('Extracted Address:')
        st.write(address)

# Only proceed if there's an address (either from text input or image extraction)
if address:
    if st.button('Parse'):
        # Parse the address
        parsed = parse_address(address)
        st.markdown("<h4 style='font-weight: bold;'>Parsed Address:</h4>", unsafe_allow_html=True)
        for component in parsed:
            st.write(f'{component[1]}: {component[0]}')

    if st.button('Normalize'):
        # Normalize the address
        normalized = expand_address(address)
        
        # Ensure that there are normalized results
        if normalized:
            st.markdown("<h4 style='font-weight: bold;'>Normalized Address Variations:</h4>", unsafe_allow_html=True)
            for addr in normalized:
                st.write(f"- {addr}")  # Display each variation as a list item
        else:
            st.write('No normalized address found.')
