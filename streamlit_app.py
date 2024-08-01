import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Write directly to the app
st.title(":cup_with_straw: Customize your smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom smoothie!
    """
)

name_on_order = st.text_input('Name on smoothie:')
st.write('The name on your smoothie will be: ', name_on_order)

# Retrieve connection parameters from Streamlit secrets
connection_parameters = {
    "account": st.secrets["snowflake"]["account"],
    "user": st.secrets["snowflake"]["user"],
    "password": st.secrets["snowflake"]["password"],
    "role": st.secrets["snowflake"]["role"],
    "warehouse": st.secrets["snowflake"]["warehouse"],
    "database": st.secrets["snowflake"]["database"],
    "schema": st.secrets["snowflake"]["schema"],
    "client_session_keep_alive": True
}

# Initialize Snowflake session with error handling
try:
    session = Session.builder.configs(connection_parameters).create()
    st.success("Connected to Snowflake!")
except Exception as e:
    st.error(f"Failed to connect to Snowflake: {e}")
    session = None  # Ensure session is not used if connection fails

# Retrieve data from Snowflake if session is established
if session:
    try:
        my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
        pd_df = my_dataframe.to_pandas()
    except Exception as e:
        st.error(f"Failed to retrieve data: {e}")
        pd_df = None  # Ensure pd_df is not used if data retrieval fails

    # Display multiselect for ingredients if data is available
    if pd_df is not None and not pd_df.empty:
        ingredients_list = st.multiselect(
            'Choose up to 5 ingredients:',
            pd_df['FRUIT_NAME'].tolist(),
            max_selections=5
        )

        if ingredients_list:
            ingredients_string = ''
            for fruit_chosen in ingredients_list:
                ingredients_string += fruit_chosen + ' '
                try:
                    search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
                    st.subheader(f"{fruit_chosen} Nutrition information")
                    fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
                    fruityvice_response.raise_for_status()
                    fv_df = pd.json_normalize(fruityvice_response.json())
                    st.dataframe(fv_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to retrieve nutrition information for {fruit_chosen}: {e}")

            my_insert_stmt = f"""INSERT INTO smoothies.public.orders (ingredients, name_on_order) 
                                 VALUES ('{ingredients_string}', '{name_on_order}')"""

            time_to_insert = st.button('Submit order')

            if time_to_insert:
                if ingredients_string and name_on_order:
                    try:
                        session.sql(my_insert_stmt).collect()
                        st.success(f'Your smoothie is ordered, {name_on_order}!', icon="✅")
                    except Exception as e:
                        st.error(f"Failed to submit order: {e}")
    else:
        st.error('No data available for ingredients.')
else:
    st.error('Unable to connect to Snowflake or no data available.')
