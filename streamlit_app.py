import streamlit as st
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

cnx = st.connection("snowflake")
session = cnx.session()

# Retrieve data from Snowflake and convert to pandas DataFrame
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),  # Convert column to list
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Ensure the correct column names are used here
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

        st.subheader(f"{fruit_chosen} Nutrition information")

        try:
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
            fruityvice_response.raise_for_status()  # Raise an error for bad status codes
            fv_df = pd.json_normalize(fruityvice_response.json())  # Normalize JSON for DataFrame
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
