import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom smoothie!
    """
)

name_on_order = st.text_input("Name On Smoothie:")
st.write("The Name On Your Smoothie Will be:", name_on_order)

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

# Initialize variables
session = None
my_dataframe = None

# Create Snowflake session
try:
    session = Session.builder.configs(connection_parameters).create()
    st.success("Connected to Snowflake!")
except Exception as e:
    st.error(f"Failed to connect to Snowflake: {e}")

# Retrieve data from Snowflake if session is established
if session:
    try:
        my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).to_pandas()
    except Exception as e:
        st.error(f"Failed to retrieve data: {e}")

# Display multiselect for ingredients if data is available
if my_dataframe is not None and not my_dataframe.empty:
    ingredients_list = st.multiselect(
        'Choose up to 5 ingredients:',
        my_dataframe['FRUIT_NAME'].tolist(),
        max_selections=5
    )

    if ingredients_list:
        ingredients_string = ' '.join(ingredients_list)

        my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
        """

        # Show the insert statement (for debugging purposes)
        st.write(my_insert_stmt)

        time_to_insert = st.button('Submit Order')

        if time_to_insert:
            try:
                session.sql(my_insert_stmt).collect()
                st.success('Your Smoothie is ordered!', icon="✅")
            except Exception as e:
                st.error(f"Failed to submit order: {e}")
else:
    if session:
        st.success('No available ingredients right now', icon='👍')
    else:
        st.error('Cannot display ingredients as the connection to Snowflake failed.')
import requests
fruityvice_response = requests.get("https://fruityvice.com/api/fruit/watermelon")
st.text(fruityvice_response)
