import streamlit as st
from postal.parser import parse_address
from postal.expand import expand_address
from PIL import Image
import pytesseract
import requests
import folium
from geopy.distance import geodesic
from streamlit_folium import folium_static

# Streamlit Interface for Address Parsing and Normalization
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"]{
        background-image: url("https://images.unsplash.com/photo-1605364850023-a917c39f8fe9?q=80&w=1802&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
        background-size: cover;
        background-position: center -30px;
    }
            
    
    [data-testid="stHeader"]{
        background-color: rgba(0,0,0,0);
            
    }
    .title {
        text-align: center;
        font-size: 2em;
        color: white;
    }
    .input-section {
        margin: 20px;
        padding: 20px;
        border: 2px solid #ddd;
        border-radius: 8px;
        background-color: #f9f9f9;
    }
    .button {
        display: inline-block;
        padding: 10px 20px;
        font-size: 16px;
        color: white;
        background-color: #007bff;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 10px;
    }
    .button:hover {
        background-color: #0056b3;
    }
    .warning {
        color: #ff6f61;
    }
    .error {
        color: #d9534f;
    }
    .info {
        color: #5bc0de;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Address Parsing, Normalization, and Postal Delivery Optimization</div>', unsafe_allow_html=True)

# Function to get coordinates for addresses using Position Stack API
def get_coordinates(addresses):
    api_key = "f509fdf6a43a9e54f34ed11a5dfbc152"  # Your Position Stack API key
    base_url = "http://api.positionstack.com/v1/forward"
    coordinates = []

    for address in addresses:
        if not address.strip():  # Skip if the address is empty
            continue

        params = {
            'access_key': api_key,
            'query': address,
            'limit': 1,  # We need only the first result
            'country': 'IN',  # Restrict to India for better accuracy
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()

            if response.status_code == 200 and 'data' in data and len(data['data']) > 0:
                location = data['data'][0]
                lat = location.get('latitude')
                lon = location.get('longitude')
                region = location.get('region')

                # Check if the result is in the correct state/region
                if region and "Andhra Pradesh" in region:
                    coordinates.append((address, lat, lon))
                else:
                    st.markdown(f"<p class='warning'>Coordinates not found accurately for: {address} (Got {region})</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p class='error'>No data found for {address}.</p>", unsafe_allow_html=True)
        except requests.exceptions.RequestException as e:
            st.markdown(f"<p class='error'>Error fetching data for {address}: {e}</p>", unsafe_allow_html=True)

    return coordinates

# Function to compute the Haversine distance between two coordinates
def haversine_distance(coord1, coord2):
    return geodesic(coord1, coord2).kilometers

# Function to display the map with two addresses and the distance between them
def display_map_with_distance(coordinates):
    if len(coordinates) == 2:
        loc1 = (coordinates[0][1], coordinates[0][2])  # (latitude, longitude)
        loc2 = (coordinates[1][1], coordinates[1][2])

        # Calculate the distance between the two locations
        distance = haversine_distance(loc1, loc2)

        # Create a folium map centered between the two locations
        map_center = [(loc1[0] + loc2[0]) / 2, (loc1[1] + loc2[1]) / 2]
        m = folium.Map(location=map_center, zoom_start=5)

        # Add markers for the two locations
        folium.Marker(location=loc1, popup=coordinates[0][0], tooltip=f"{coordinates[0][0]}").add_to(m)
        folium.Marker(location=loc2, popup=coordinates[1][0], tooltip=f"{coordinates[1][0]}").add_to(m)

        # Draw a line between the two locations
        folium.PolyLine(locations=[loc1, loc2], color="blue", weight=2.5, opacity=1).add_to(m)

        # Display the distance in kilometers on the map
        midpoint = [(loc1[0] + loc2[0]) / 2, (loc1[1] + loc2[1]) / 2]
        folium.Marker(location=midpoint, 
                      icon=folium.DivIcon(html=f'<div style="font-size: 12pt; color: red;">{distance:.2f} km</div>')).add_to(m)

        # Display the map
        folium_static(m)
    else:
        st.markdown("<p class='error'>Please enter exactly two addresses.</p>", unsafe_allow_html=True)

# Initialize session state for storing normalized addresses
if 'normalized_address' not in st.session_state:
    st.session_state.normalized_address = []

# Address Parsing and Normalization
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
    if st.button('Parse', key='parse_button'):
        # Parse the address
        parsed = parse_address(address)
        st.markdown("<h4 style='font-weight: bold;'>Parsed Address:</h4>", unsafe_allow_html=True)
        for component in parsed:
            st.write(f'{component[1]}: {component[0]}')

    if st.button('Normalize', key='normalize_button'):
        # Normalize the address
        normalized = expand_address(address)
        
        # Ensure that there are normalized results
        if normalized:
            st.markdown("<h4 style='font-weight: bold;'>Normalized Address Variations:</h4>", unsafe_allow_html=True)
            st.session_state.normalized_address = normalized
            for addr in normalized:
                st.write(f"- {addr}")  # Display each variation as a list item
        else:
            st.write('No normalized address found.')

# Postal Delivery Optimization
if st.session_state.normalized_address:
    # Define choices for the constant address
    constant_address = st.selectbox(
    'Select a postal address:',
    ["Sontyam, Visakhapatnam, Andhra Pradesh, India",
     "Gajuwaka, Visakhapatnam, Andhra Pradesh, India",
     "Madhurawada, Visakhapatnam, Andhra Pradesh, India"]
)


    # Use the first normalized address from the list
    second_address = st.session_state.normalized_address[0]

    # Combine both addresses for the mapping part
    addresses = [constant_address, second_address]


    # Add a button to show postal delivery optimization
    if st.button('Show Distance Visualization', key='distance_button'):
        # Fetch and display coordinates
        coordinates = get_coordinates(addresses)
        
        if len(coordinates) == 2:
            for address, lat, lon in coordinates:
                st.write(f"{address}: ({lat}, {lon})")

            # Display the map with the two addresses and the distance
            display_map_with_distance(coordinates)
        else:
            st.markdown("<p class='error'>Failed to retrieve valid coordinates for both addresses.</p>", unsafe_allow_html=True)

