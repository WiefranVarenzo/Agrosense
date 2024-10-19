import streamlit as st
import paho.mqtt.client as mqtt
import time
from PIL import Image
import io
import numpy as np
import tensorflow as tf
from streamlit_option_menu import option_menu
import os

# Initialize the 'page' key in st.session_state if it doesn't exist
if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'

# Function to include the CSS file
def include_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found: {file_name}")

# Example usage with the correct path
include_css("styles.css")  # Adjust this path as needed

# Additional CSS for responsiveness
st.markdown("""
    <style>
    @media screen and (max-width: 768px) {
        .sensor-box {
            margin-bottom: 20px;
            text-align: center;
        }
        .sensor-title {
            font-size: 1.2em;
        }
        .sensor-value {
            font-size: 1.5em;
        }
    }
    </style>
""", unsafe_allow_html=True)


# Define landing page
def landing_page():
    st.markdown(
        """
        <div style="text-align: center;">
            <h2 style="margin-bottom: 20px;">🌿 Welcome to AgroSense 🌿</h2>
        </div>
        <div style="text-align: justify; font-size: 1.1em; line-height: 1.5;">
            <p>
                AgroSense is a smart solution to help you maintain the health of your plants using only leaf images. We use the latest deep learning technology to accurately identify plant diseases.
            </p>
            <p>
                This application provides :
            </p>
            <ul style="list-style-position: inside;">
                <li>Detect Diseases: Upload a picture of your plant leaves to find out if your plant is healthy or suffering from diseases like scab, rust, or multiple diseases.</li>
                <li>Get Detailed Information: Get descriptions, causes, and solutions for each type of disease detected.</li>
                <li>Easier Plant Care: With the right information, you could take the necessary actions to keep your plants healthy.</li>
            </ul>
            <h3 style="text-align: center;">How it Works</h3>
            <ol style="list-style-position: inside;">
                <li>Upload Image: Select a plant leaf image from your device.</li>
                <li>Image Process: The application will process the image and provide predictions based on the deep learning model.</li>
                <li>View Results: Get information about plant health status and necessary care steps.</li>
            </ol>
            <h3 style="text-align: center;">Why Choose Us?</h3>
            <p>
                - High Accuracy: We use advanced deep learning models that combine Xception and DenseNet architectures for more accurate results.
                <br>
                - Easy to Use: The simple and intuitive interface makes it easy for anyone to operate.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("Next", key="next_button"):
        st.session_state['page'] = 'main_menu'

# Define function for cleaning and resizing image
def clean_image(image):
    image = np.array(image)
    image = np.array(Image.fromarray(image).resize((512, 512), Image.LANCZOS))
    image = image[np.newaxis, :, :, :3]
    return image

# Define function for getting prediction from the model
def get_prediction(model, image):
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)
    test = datagen.flow(image)
    predictions = model.predict(test)
    predictions_arr = np.array(np.argmax(predictions))
    return predictions, predictions_arr

# Define function for making result output
def make_results(predictions, predictions_arr):
    result = {}
    if int(predictions_arr) == 0:
        result = {"status": " is Healthy ", "prediction": f"{int(predictions[0][0].round(2)*100)}%"}
    if int(predictions_arr) == 1:
        result = {"status": ' has Multiple Diseases ', "prediction": f"{int(predictions[0][1].round(2)*100)}%"}
    if int(predictions_arr) == 2:
        result = {"status": ' has Rust ', "prediction": f"{int(predictions[0][2].round(2)*100)}%"}
    if int(predictions_arr) == 3:
        result = {"status": ' has Scab ', "prediction": f"{int(predictions[0][3].round(2)*100)}%"}
    return result

# Dictionary for storing disease information
info_dict = {
    "is Healthy": {
        "description": "The plant is healthy with no signs of disease.",
        "cause": "N/A",
        "solution": "Continue providing optimal care, including proper watering, fertilization, and sunlight."
    },
    "has Scab": {
        "description": "Scab is a fungal disease that affects the leaves and fruit of plants.",
        "cause": "Caused by the Venturia inaequalis fungus, which thrives in wet conditions.",
        "solution": "Remove and destroy infected leaves, apply fungicides, and ensure proper spacing for air circulation."
    },
    "has Rust": {
        "description": "Rust is a fungal disease that appears as rust-colored spots on leaves.",
        "cause": "Caused by various species of fungi, which spread through wind and water.",
        "solution": "Remove infected leaves, apply appropriate fungicides, and avoid overhead watering."
    },
    "has Multiple Diseases": {
        "description": "The plant shows signs of multiple diseases.",
        "cause": "Combination of factors, including poor plant health, environmental stress, and presence of multiple pathogens.",
        "solution": "Implement integrated disease management practices, improve plant care, and consult with a plant health expert if necessary."
    }
}

# Disease Analysis Page with Camera Integration
def disease_analysis_page():
    st.title('🌿 Plant Disease Detection 🌿')
    st.write("Capture or upload a leaf image to detect if the plant is healthy or has scab, rust, or multiple diseases.")

    # Camera input for real-time image capture
    camera_image = st.camera_input("Capture image from your camera")

    # File uploader for image upload
    uploaded_file = st.file_uploader("Or choose an image file", type=["png", "jpg", "jpeg"], key="file_uploader")

    if camera_image is not None:
        # If an image is captured from the camera
        image = Image.open(io.BytesIO(camera_image.getvalue()))
        st.image(image.resize((700, 400)), use_column_width=True)
        process_image(image)

    elif uploaded_file is not None:
        # If an image is uploaded from the file uploader
        image = Image.open(io.BytesIO(uploaded_file.read()))
        st.image(image.resize((700, 400)), use_column_width=True)
        process_image(image)

    else:
        st.write("Please upload an image file or use your camera to capture a leaf image.")

# Loading the Model
@st.cache_resource
def load_model(path):
    try:
        # Xception Model
        xception_model = tf.keras.models.Sequential([
            tf.keras.applications.xception.Xception(include_top=False, weights='imagenet', input_shape=(512, 512, 3)),
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(4, activation='softmax')
        ])

        # DenseNet Model
        densenet_model = tf.keras.models.Sequential([
            tf.keras.applications.densenet.DenseNet121(include_top=False, weights='imagenet', input_shape=(512, 512, 3)),
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(4, activation='softmax')
        ])

        inputs = tf.keras.Input(shape=(512, 512, 3))
        xception_output = xception_model(inputs)
        densenet_output = densenet_model(inputs)

        combined_output = tf.keras.layers.Average()([xception_output, densenet_output])

        model = tf.keras.Model(inputs=inputs, outputs=combined_output)
        model.load_weights(path)

        return model
    except FileNotFoundError:
        st.error("Model file not found. Please check the path and try again.")
        return None

model = load_model('model_akhir.h5')

def process_image(image):
    try:
        # Show progress and text
        progress = st.text("Crunching Image...")
        my_bar = st.progress(0)

        # Clean the image
        image = clean_image(image)
        my_bar.progress(30)

        # Make predictions
        predictions, predictions_arr = get_prediction(model, image)
        my_bar.progress(60)

        # Generate results
        result = make_results(predictions, predictions_arr)
        my_bar.progress(100)

        # Remove progress bar and text after prediction is complete
        progress.empty()
        my_bar.empty()

        # Display results
        st.success(f"The plant {result['status']} with {result['prediction']} prediction.")

        # Display additional information
        status = result['status'].strip()
        st.write("### Details")
        st.write(f"Description: {info_dict[status]['description']}")
        st.write(f"Cause: {info_dict[status]['cause']}")
        st.write(f"Solution: {info_dict[status]['solution']}")
        
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Function to include the CSS file
def include_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found: {file_name}")

# Example usage with the correct path
# Ensure the path here matches the actual location of your styles.css file
include_css("styles.css")  # Adjust this path as needed

# Sidebar (About) code
def show_sidebar():
    st.sidebar.title("About")
    st.sidebar.info("""
        This app uses a deep learning model to detect plant diseases from leaf images.
        The model is a combination of Xception and DenseNet architectures.
    """)
    if st.sidebar.button("Exit", key="exit_button"):
        st.session_state['page'] = 'landing'

# MQTT settings
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPICS = [
    ("csm3313_umt/group09/airquality", 0),
    ("csm3313_umt/group09/temperature", 0),
    ("csm3313_umt/group09/humidity", 0),
    ("csm3313_umt/group09/tds", 0),
    ("csm3313_umt/group09/ph", 0),
    ("csm3313_umt/group09/light", 0)
]

# Global variables to store sensor data
sensor_data = {
    "airquality": "",
    "temperature": "",
    "humidity": "",
    "tds": "",
    "ph": "",
    "light": ""
}

# Callback function when connecting to MQTT broker
def on_connect(client, userdata, flags, rc):
    st.write("Connected to MQTT broker with result code " + str(rc))
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic)
        st.write(f"Subscribed to {topic}")

# Callback function when receiving a message from MQTT broker
def on_message(client, userdata, msg):
    topic = msg.topic.split('/')[-1]
    payload = msg.payload.decode("utf-8")
    sensor_data[topic] = payload
    st.write(f"Received message from {msg.topic}: {payload}")

# Initialize MQTT client and set callback functions
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Function to include the CSS file
def include_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found: {file_name}")

# Include CSS file
include_css("styles.css")  # Adjust this path as needed

# Real-Time Sensor Page with MQTT Integration
def real_time_sensor_page():
    st.title("📊 Real-Time Sensor Data 📊")
    st.write("Here you can view the real-time sensor data.")

    # Main section for displaying sensor data
    st.subheader("Sensor Data")

    # Placeholder for sensor data
    data_placeholder = st.empty()

    # Continuously run MQTT client loop in a separate thread
    client.loop_start()

    while True:
        with data_placeholder.container():
            # Define columns layout
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="sensor-box">
                    <div class="sensor-title">Temperature</div>
                    <div class="sensor-value">{sensor_data.get('temperature', 'N/A')}°C</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="sensor-box">
                    <div class="sensor-title">Humidity</div>
                    <div class="sensor-value">{sensor_data.get('humidity', 'N/A')} %</div>
                </div>
                """, unsafe_allow_html=True)

            col3, col4 = st.columns(2)
            with col3:
                st.markdown(f"""
                <div class="sensor-box">
                    <div class="sensor-title">Air Quality</div>
                    <div class="sensor-value">{sensor_data.get('airquality', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="sensor-box">
                    <div class="sensor-title">Water Quality</div>
                    <div class="sensor-value">{sensor_data.get('tds', 'N/A')}PPM</div>
                </div>
                """, unsafe_allow_html=True)

            # Adjust the number of columns and their layout
            col5, col6 = st.columns([1, 1])  # Specify two equal-width columns
            with col5:
                st.markdown(f"""
                <div class="sensor-box">
                    <div class="sensor-title">pH</div>
                    <div class="sensor-value">{sensor_data.get('ph', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)
            with col6:
                st.markdown(f"""
                <div class="sensor-box">
                    <div class="sensor-title">Light</div>
                    <div class="sensor-value">{sensor_data.get('light', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

        time.sleep(1)


# Main menu implementation
def main_menu():
    # Top menu layout
    selected = option_menu(
        menu_title=None,
        options=["Real-Time Sensor", "Disease Analysis"],
        icons=["bar-chart-fill","camera-fill"],
        orientation="horizontal",
    )

    if selected == "Disease Analysis":
        disease_analysis_page()
    elif selected == "Real-Time Sensor":
        real_time_sensor_page()
# Page Navigation
if st.session_state['page'] == 'landing':
    landing_page()
else:
    if st.session_state['page'] == 'main_menu':
        show_sidebar()  # Show sidebar with the exit button
        main_menu()
    elif st.session_state['page'] == 'disease_analysis':
        show_sidebar()  # Show sidebar with the exit button
        disease_analysis_page()
    elif st.session_state['page'] == 'real_time_sensor':
        show_sidebar()  # Show sidebar with the exit button
        real_time_sensor_page()

# Remove the main menu
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
