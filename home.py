import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Choropleth, FeatureGroup

# Load GeoJSON data
geojson_url = "https://wfs-kbhkort.kk.dk/k101/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=k101:afstemningsomraade&outputFormat=json&SRSNAME=EPSG:4326"
gdf = gpd.read_file(geojson_url)

# Assuming df_votes is already loaded with the required data
# Example structure of df_votes:
# df_votes = pd.DataFrame({
#     'Area': ['Area1', 'Area2', 'Area3'],
#     'Name': ['Candidate1', 'Candidate2', 'Candidate1'],
#     'Votes': [100, 150, 120]
# })

df_votes = pd.read_csv('df_votes_kbh.csv')
# Ensure names match correctly
df_votes['Area'] = df_votes['Area'].str.strip()
gdf['navn'] = gdf['navn'].str.strip()

# Create a dropdown for selecting a candidate
candidate_names = df_votes['Name'].unique()
selected_candidate = st.selectbox('Select a Candidate', candidate_names)
column = st.selectbox('Værdi', ['Votes', '% af personlige stemmer', 'Rank'])

df_votes = df_votes[df_votes['Votes']!='Personlige stemmer']
c1, c2 =st.columns(2)
df_votes['Votes'] = pd.to_numeric(df_votes['Votes'])
df_votes1 = df_votes.groupby('Area').sum('Votes').reset_index().rename(columns={'Votes': 'votes in area'})
df_votes['Rank'] = df_votes.groupby('Area')['Votes'].rank(ascending=False, method='min').astype(int)
df_votes = df_votes.merge(df_votes1, how='left', on='Area')
df_votes['% af personlige stemmer'] = df_votes['Votes']/df_votes['votes in area']*100


#c1.write(df_votes)
c2.write(df_votes1)

# Merge DataFrame with GeoDataFrame
merged_gdf = pd.merge(df_votes, gdf, left_on='Area', right_on='navn')
merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry='geometry').dropna(subset=['geometry'])

# Function to create and update the map
def update_map(candidate_name):
    # Filter for the selected candidate
    candidate_df = merged_gdf[merged_gdf['Name'] == candidate_name]

    # Create a Folium map centered on Copenhagen without adding unnecessary layers
    m = folium.Map(location=[55.6761, 12.5683], zoom_start=12, control_scale=True)
    

    # Add a Choropleth map for the selected candidate's votes
    Choropleth(
        geo_data=candidate_df,
        name='Votes',
        data=candidate_df,
        columns=['navn', 'Votes'],
        key_on='feature.properties.navn',
        fill_color='PuRd',
        fill_opacity=0.9,
        line_opacity=0,  # Set line_opacity to 0
        line_weight=0,   # Set line_weight to 0 to remove borders
        legend_name=f'Votes for {candidate_name}'
    ).add_to(m)

    # Add a Choropleth map for the selected candidate's rank
    Choropleth(
        geo_data=candidate_df,
        name='Rank',
        data=candidate_df,
        columns=['navn', 'Rank'],
        key_on='feature.properties.navn',
        fill_color='PuRd',
        fill_opacity=0.9,
        line_opacity=0,  # Set line_opacity to 0
        line_weight=0,   # Set line_weight to 0 to remove borders
        legend_name=f'Rank for {candidate_name}',
        reverse=True
    ).add_to(m)

    # Add a Choropleth map for the percentage of personal votes
    Choropleth(
        geo_data=candidate_df,
        name='% of personal votes',
        data=candidate_df,
        columns=['navn', '% af personlige stemmer'],
        key_on='feature.properties.navn',
        fill_color='PuRd',
        fill_opacity=0.9,
        line_opacity=0,  # Set line_opacity to 0
        line_weight=0,   # Set line_weight to 0 to remove borders
        legend_name=f'% of personal votes for {candidate_name}'
    ).add_to(m)

    # Add tooltips or popups with relevant data on hover
    for _, row in candidate_df.iterrows():
        tooltip_text = f"Area: {row['Area']}<br>Votes: {row['Votes']}<br>Rank: {row['Rank']}<br>% of personal votes: {row['% af personlige stemmer']:.2f}%"
        
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: {'color': 'transparent', 'weight': 0},  # Remove borders
            tooltip=folium.Tooltip(tooltip_text),
        ).add_to(m)

    # Since Choropleth layers are directly added, you don't need to explicitly add them to LayerControl
    # Just add a basic LayerControl without specifying layers
    folium.LayerControl(collapsed=False, autoZIndex=False).add_to(m)

    
    return m

# Streamlit UI
st.title('Copenhagen Election Results')




# Display the map
m = update_map(selected_candidate)
st_folium(m, width=700, height=500)
