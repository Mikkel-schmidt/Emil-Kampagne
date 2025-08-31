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

# Fjern total-rækken, hvis den findes som tekst i Votes
if df_votes['Votes'].dtype == object:
    df_votes = df_votes[df_votes['Votes'] != 'Personlige stemmer']
    
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

# --------- NYT: helpers til partifilter og Radikale-kort ---------
def filter_party_rows(df: pd.DataFrame, party_aliases=('Radikale Venstre', 'Radikale', 'B')) -> pd.DataFrame:
    """
    Finder rækker for Radikale baseret på almindelige kolonnenavne for parti/liste.
    Fald tilbage til Name indeholdende 'Radikale', hvis der ikke findes parti-kolonner.
    """
    possible_cols = ['Party', 'Parti', 'Liste', 'List', 'PartyName', 'Party_name', 'party', 'parti', 'liste']
    aliases_pattern = '|'.join([str(a) for a in party_aliases])

    for col in possible_cols:
        if col in df.columns:
            mask = df[col].astype(str).str.contains(aliases_pattern, case=False, na=False)
            if mask.any():
                return df[mask].copy()

    # fallback: søg i kandidatnavn
    mask_name = df['Name'].astype(str).str.contains('Radikale', case=False, na=False)
    return df[mask_name].copy()

import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Choropleth, FeatureGroup

# Load GeoJSON data
geojson_url = "https://wfs-kbhkort.kk.dk/k101/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=k101:afstemningsomraade&outputFormat=json&SRSNAME=EPSG:4326"
gdf = gpd.read_file(geojson_url)

df_votes = pd.read_csv('df_votes_kbh.csv')

# Ensure names match correctly
if 'Area' in df_votes.columns:
    df_votes['Area'] = df_votes['Area'].astype(str).str.strip()
gdf['navn'] = gdf['navn'].astype(str).str.strip()

# Create a dropdown for selecting a candidate
candidate_names = df_votes['Name'].unique()
selected_candidate = st.selectbox('Select a Candidate', candidate_names)
column = st.selectbox('Værdi', ['Votes', '% af personlige stemmer', 'Rank'])

# Fjern total-rækken, hvis den findes som tekst i Votes
if df_votes['Votes'].dtype == object:
    df_votes = df_votes[df_votes['Votes'] != 'Personlige stemmer']

c1, c2 = st.columns(2)

# Sikr numerisk Votes
df_votes['Votes'] = pd.to_numeric(df_votes['Votes'], errors='coerce').fillna(0).astype(int)

# Summer pr. område (alle kandidater)
df_votes1 = df_votes.groupby('Area', as_index=False)['Votes'].sum().rename(columns={'Votes': 'votes in area'})

# Rank pr. område
df_votes['Rank'] = df_votes.groupby('Area')['Votes'].rank(ascending=False, method='min').astype(int)

# Merge total pr. område ind
df_votes = df_votes.merge(df_votes1, how='left', on='Area')
df_votes['% af personlige stemmer'] = (df_votes['Votes'] / df_votes['votes in area'] * 100).fillna(0)

# c1.write(df_votes)
c2.write(df_votes1)

# Merge DataFrame with GeoDataFrame for kandidat-kortet
merged_gdf = pd.merge(df_votes, gdf, left_on='Area', right_on='navn')
merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry='geometry').dropna(subset=['geometry'])

# --------- NYT: helpers til partifilter og Radikale-kort ---------
def filter_party_rows(df: pd.DataFrame, party_aliases=('Radikale Venstre', 'Radikale', 'B')) -> pd.DataFrame:
    """
    Finder rækker for Radikale baseret på almindelige kolonnenavne for parti/liste.
    Fald tilbage til Name indeholdende 'Radikale', hvis der ikke findes parti-kolonner.
    """
    possible_cols = ['Party', 'Parti', 'Liste', 'List', 'PartyName', 'Party_name', 'party', 'parti', 'liste']
    aliases_pattern = '|'.join([str(a) for a in party_aliases])

    for col in possible_cols:
        if col in df.columns:
            mask = df[col].astype(str).str.contains(aliases_pattern, case=False, na=False)
            if mask.any():
                return df[mask].copy()

    # fallback: søg i kandidatnavn
    mask_name = df['Name'].astype(str).str.contains('Radikale', case=False, na=False)
    return df[mask_name].copy()

def build_radikale_map(df_votes: pd.DataFrame, gdf: gpd.GeoDataFrame):
    """
    Bygger et folium-kort med total antal stemmer til Radikale pr. område.
    """
    rv = filter_party_rows(df_votes)
    if rv.empty:
        st.warning("Kunne ikke finde nogen rækker for Radikale (tjek at din CSV har en parti-/liste-kolonne eller at kandidatnavne indeholder 'Radikale').")
        return None

    rv_area = rv.groupby('Area', as_index=False)['Votes'].sum().rename(columns={'Votes': 'RV_votes'})

    merged_rv = rv_area.merge(gdf[['navn', 'geometry']], left_on='Area', right_on='navn', how='inner').dropna(subset=['geometry'])
    merged_rv = gpd.GeoDataFrame(merged_rv, geometry='geometry')

    m2 = folium.Map(location=[55.6761, 12.5683], zoom_start=12, control_scale=True)

    Choropleth(
        geo_data=merged_rv,
        name='Radikale stemmer',
        data=merged_rv,
        columns=['navn', 'RV_votes'],
        key_on='feature.properties.navn',
        fill_color='PuBu',
        fill_opacity=0.9,
        line_opacity=0,
        line_weight=0,
        legend_name='Stemmer til Radikale pr. område'
    ).add_to(m2)

    for _, row in merged_rv.iterrows():
        tooltip_text = f"Område: {row['Area']}<br>Radikale-stemmer: {int(row['RV_votes'])}"
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: {'color': 'transparent', 'weight': 0},
            tooltip=folium.Tooltip(tooltip_text),
        ).add_to(m2)

    folium.LayerControl(collapsed=False, autoZIndex=False).add_to(m2)
    return m2
# ---------------------------------------------------------------


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

# NEDENUNDER: ekstra kort for Radikale
st.markdown("## Hvor har Radikale fået flest stemmer?")
m_rad = build_radikale_map(df_votes, gdf)
if m_rad is not None:
    st_folium(m_rad, width=700, height=500)