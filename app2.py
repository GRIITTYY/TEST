import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from streamlit_option_menu import option_menu
from datetime import datetime
from urllib.parse import unquote, quote
import json
import pytz
import qrcode
from io import BytesIO
import time
from bcrypt import checkpw, hashpw, gensalt

# MongoDB connection
def get_database():
    uri = st.secrets["MONGODB_URI"]
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["main_db"]
        return db
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {str(e)}")
        return None

# Validate login credentials (hashed password comparison)
def validate_login(email, password):
    db = get_database()
    if db is not None:
        collection = db["admins"]
        user = collection.find_one({"email": email})
        if user and user.get('password') == password:
            return True
    return False

# Generate QR code
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

# Main function
def main():
    st.title("Welcome")

    # Sidebar menu
    with st.sidebar:
        page = option_menu(
            "Menu",
            ["MARK MY ATTENDANCE", "ADMIN LOGIN"],
            icons=["house", "bar-chart-line"],
            menu_icon="justify",
            styles={
                "container": {"background-color": "#fafafa"},
                "nav-link": {"font-size": "17px", "text-align": "justify", "margin": "0px", "--hover-color": "#eee"}
            }
        )

    if page == "ADMIN LOGIN":
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False

        if not st.session_state.logged_in:
            # Login form
            st.subheader("Login")
            
            if 'email' not in st.session_state:
                email = st.text_input("Email")
                if email:
                    st.session_state.email = email  # Store email in session state once it's input
            else:
                email = st.session_state.email  # Use email from session if already set
                
            password = st.text_input("Password", type="password")
            submit = st.button("Submit")

            if submit:
                if email and password:
                    if validate_login(email, password):
                        st.session_state.logged_in = True
                        st.success(f"Welcome {email}!")
                        st.rerun()  # Rerun the app to update the UI
                    else:
                        st.error("Invalid credentials. Please try again.", icon="❌")
                else:
                    st.warning("Please enter both email and password.", icon="❗")
        else:
            # Logout button and QR code generation
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
            with col8:
                if st.button("Logout"):
                    st.session_state.logged_in = False
                    st.rerun()  # Rerun the app to update the UI

            if st.button("Generate QR Code"):
                now = datetime.now(pytz.timezone('Africa/Lagos'))
                scan_date = now.strftime("%d-%m-%Y")
                scan_time = now.strftime("%H:%M:%S")

                # Fetch admin data
                db = get_database()
                admin_data = db["admins"].find_one({"email": email})
                admin_id = admin_data.get("admin_id", "default_admin_id")
                admin_location = admin_data.get("admin_location", "default_location")

                data = {
                    "scan_date": scan_date,
                    "scan_time": scan_time,
                    "admin_id": admin_id,
                    "admin_location": admin_location
                }

                # Encode data and generate QR code URL
                json_data = json.dumps(data)
                encoded_json_data = quote(json_data)
                url = f"https://test-attendance.streamlit.app/?data={encoded_json_data}"

                qr_image = generate_qr_code(url)
                st.image(qr_image, caption="Scan this QR code to mark attendance", width=200)

    elif page == "MARK MY ATTENDANCE":
        query_params = st.query_params

        if "data" in query_params:  # Check if 'data' exists
            data_param = query_params["data"]  # Directly get the value (assumed to be the only value)
            try:
                decoded_data_param = unquote(data_param)  # Decode URL-encoded string
                data = json.loads(decoded_data_param)  # Convert JSON string to dictionary

                # Process the data
                student_email = st.text_input("Email address", placeholder="Enter your registered email address")
                if st.button("Check-in"):
                    st.success("You have successfully checked in ✅")

                    # Insert data into MongoDB
                    db = get_database()
                    collection = db["students"]
                    now = datetime.now(pytz.timezone('Africa/Lagos'))
                    check_in_date = now.strftime("%d-%m-%Y")
                    check_in_time = now.strftime("%H:%M:%S")
                    
                    # Check for duplicate check-ins
                    if db["students"].find_one({"scan_date": data["scan_date"], "scan_time": data["scan_time"]}):
                        st.error("You have already checked in today!", icon="🚫")
                    else:
                        collection.insert_one({
                            "scan_date": data["scan_date"],
                            "scan_time": data["scan_time"],
                            "email": student_email,
                            "check_in_date": check_in_date,
                            "check_in_time": check_in_time,
                            "admin_id": data["admin_id"],
                            "location": data["admin_location"]
                        })

                st.info("You can only check in once per day")

            except json.JSONDecodeError:
                st.error("Invalid JSON data in the URL.")
        else:
            st.image("assets/img/lens_scan.png", width=300)
            st.error("Kindly Scan New QR Code from the Admin", icon="🚫")

# Run the main function
if __name__ == "__main__":
    main()
