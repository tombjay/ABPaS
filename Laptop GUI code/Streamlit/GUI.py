import pandas as pd
import streamlit as st
import json
import time
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import urllib.request

try:
    import streamlit.ReportThread as ReportThread
    from streamlit.server.Server import Server
except Exception:
    # Streamlit >= 0.65.0
    import streamlit.report_thread as ReportThread
    from streamlit.server.server import Server

st.set_page_config(layout="wide")

# after it's been refreshed 100 times.
count = st_autorefresh(interval=5000, limit=1000, key="counter") 

def BCV_Data_Extractor(path):
    with open(path, 'r') as outfile:
        jsonfile = outfile.readlines()
    
    df = pd.read_json(jsonfile[1]).T.reset_index()
    for i, val in enumerate(jsonfile):
        if i in [0,1]: 
            continue
        else:
            df_s = pd.read_json(val).T.reset_index()
            df = df.append(df_s, ignore_index=True)
    df["IsObstacle_Detected"] = df.Ultrasonic_D_CM.map(lambda x: x<=10)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.rename(columns = {'index':'Name'}, inplace = True)
    return df
def RPi_Data_Extractor(path):
    with open(path, 'r') as outfile:
        jsonfile = outfile.readlines()
    df = pd.read_json(jsonfile[1]).T.reset_index()
    for i, val in enumerate(jsonfile):
        if i in [0,1]:
            continue
        else:
            df_s = pd.read_json(val).T.reset_index()
            df = df.append(df_s, ignore_index=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.rename(columns = {'index':'Name'}, inplace = True)
    return df
def customer_details_saver(app_domain):
    details = urllib.request.urlopen(app_domain).read()
    cus_json_file = json.loads(details)
    with open("customer_details", 'w') as outfile:
        json.dump(cus_json_file, outfile)
    return None

st.sidebar.markdown('''<div align="center"> <h1> <b> <u> Welcome to the Project "Automated Bike Parking System - ABPaS" </u> </b> </h1> </div>''', unsafe_allow_html=True)
st.sidebar.markdown('''<h3> <b> 
Below are the creator details:</b></h3>''', unsafe_allow_html=True)
st.sidebar.markdown('''
                    #### Name : John Pravin Arockiasamy \n
                    (<st180270@stud.uni-stuttgart.de>)\n
                    #### Name : Jayakumar Ramasamy Sundararaj \n
                    (<st178863@stud.uni-stuttgart.de>)\n
                    #### Name : Erisa Hoxha \n
                    (<st181212@stud.uni-stuttgart.de>)\n
                    ''')
#Main Coding
st.markdown('''<div align="center"> <h1> <b> Welcome to the Project "Automated Bike Parking System - ABPaS" </b> </h1> </div>''', unsafe_allow_html=True)

with st.expander("Facility Viz:"):
    col1, col2 = st.columns(2)
    lis_1 = ("--select--", 'RaspberryPi_Data')
    lis_2 = ('--select--', 'BCV_Data')
    with col1:
        picks = st.selectbox('Please Choose From the below data to visualize', lis_1)
        if picks == "RaspberryPi_Data":
            path = r"D:\ABPaS Project\Automated_Bike_Parking_System-ABPaS-main\Automated_Bike_Parking_System-ABPaS-main\Laptop Sub Code\RaspberryPi_Json_Data"
            df = RPi_Data_Extractor(path)
            st.dataframe(df)
            length = df.shape[0]
            st.plotly_chart(px.line(df, x="Timestamp", y= ["DHT_temp", "DHT_humidity"], title='Raspberry Pi Sensor Data', hover_name="Name", height=500, width=650))
            st.plotly_chart(px.line(df, x="Timestamp", y= ["PIR1_motion", "PIR2_motion"], title='Raspberry Pi Sensor Data', hover_name="Name", height=500, width=650))
            
            if df["DHT_temp"][length-1] > 27:
                st.balloons()
                st.warning("Temperature is High")
            
    with col2:
        picks = st.selectbox('Please Choose From the below data to visualize', lis_2)
        if picks == "BCV_Data":
            path = r"D:\ABPaS Project\Automated_Bike_Parking_System-ABPaS-main\Automated_Bike_Parking_System-ABPaS-main\Laptop Sub Code\BCV1_Json_Data"
            df = BCV_Data_Extractor(path)
            st.dataframe(df)  
            length = df.shape[0]
            st.plotly_chart(px.line(df, x="Timestamp", y= ["Ultrasonic_D_CM"], title='BCV1 Sensor Data', hover_name="Name", height=500, width=650))
            st.plotly_chart(px.line(df, x="Timestamp", y= ["IR2_status", "IR3_status"], title='BCV1 Sensor Data', hover_name="Name", height=500, width=650))
                
            if df["IsObstacle_Detected"][length-1]== True:
                st.balloons()
                st.warning("Obstacle Detected")
                
with st.expander("Customer Details:"):
    #app_domain = "https://abpas.herokuapp.com/parking/all"
    #customer_details_saver(app_domain)
    with open("customer_details", 'r') as outfile:
        cus_file = outfile.readlines()
        print(cus_file)
    user_df = pd.DataFrame()
    parking_df = pd.DataFrame()
    remaining_df = pd.read_json(cus_file[0])
    remaining_df.drop(['id','state', 'parkingSpot', 'user'], axis=1, inplace=True)
    for idx, file in enumerate(json.loads(cus_file[0])):
        p_df = pd.DataFrame(json.loads(cus_file[0])[idx]['parkingSpot'], index=[0])
        parking_df = parking_df.append(p_df, ignore_index=True)
        us_df = pd.DataFrame(json.loads(cus_file[0])[idx]['user'], index=[0])
        us_df.drop(['password'], axis=1, inplace=True)
        user_df = user_df.append(us_df, ignore_index=True)

    final_user_df = user_df.join(parking_df, lsuffix='_user', rsuffix='_parking')
    final_user_df= final_user_df.join(remaining_df)
    st.dataframe(final_user_df)