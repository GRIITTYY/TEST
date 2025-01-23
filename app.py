import streamlit as st
import sqlite3
import qrcode
from io import BytesIO
from streamlit_option_menu import option_menu
from datetime import datetime
from urllib.parse import unquote, quote
import json
import pytz

# -------------------------------------------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------------------------------------

def validate_login(email, password):
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# ----------------------------------------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------------------------------------

def main():
    if page == "ADMIN LOGIN":
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False

        if not st.session_state.logged_in:
            # Display login form
            st.subheader("Login")
            email = st.text_input("Email")
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
            # Display logout button and QR code
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
            with col8:
                if st.button("Logout"):
                    st.session_state.logged_in = False
                    st.rerun()  # Rerun the app to update the UI

            timezone = pytz.timezone('Africa/Lagos')
            now = datetime.now(timezone)
            scan_date = now.strftime("%d-%m-%Y")
            scan_time = now.strftime("%H:%M:%S")

            data = {
                "scan_date": scan_date,
                "scan_time": scan_time
            }
            json_data = json.dumps(data)
            encoded_json_data = quote(json_data)

            url = f"https://testrepo.streamlit.app/?data={encoded_json_data}"

            qr_image = generate_qr_code(url)
            st.image(qr_image, caption="Scan this QR code to mark attendance")

    elif page == "MARK MY ATTENDANCE":
        query_params = st.query_params

        if "data" in query_params:
            data_param = query_params["data"]
            try:
                decoded_data_param = unquote(data_param)
                data = json.loads(decoded_data_param)

                student_email = st.text_input("Email address", placeholder="Enter your registered email address")
                if st.button("Check-in"):
                    st.success("You have successfully checked in ✅")

                st.info("You can only check in once per day")

            except json.JSONDecodeError:
                st.error("Invalid JSON data in the URL.")
        else:
            st.image("assets/img/lens_scan.png", width=300)
            st.error("Kindly Scan New QR Code from the Admin", icon="🚫")


# -------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
