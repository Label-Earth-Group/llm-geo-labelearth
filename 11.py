import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image


def load_haz_waste_shp(
        haz_waste_shp_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/HW_Sites_EPSG4326.zip'):
    try:
        haz_waste_gdf = gpd.read_file(haz_waste_shp_url)
        haz_waste_gdf = haz_waste_gdf.dropna(how='all')
        return haz_waste_gdf
    except:
        raise Exception('Error loading hazardous waste shapefile. Please check the URL or network connection.')


def load_tract_shp(
        tract_shp_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/tract_37_EPSG4326.zip'):
    try:
        tract_gdf = gpd.read_file(tract_shp_url)
        return tract_gdf
    except:
        raise Exception('Error loading tract boundary shapefile. Please check the URL or network connection.')


def load_pop_csv(
        pop_csv_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/NC_tract_population.csv'):
    try:
        pop_df = pd.read_csv(pop_csv_url)
        pop_df['GEOID'] = pop_df['GEOID'].astype(str).str.zfill(11)
        pop_df.dropna(subset=['GEOID', 'TotalPopulation'], inplace=True)
    except:
        raise Exception('Error loading CSV file. Please check the URL or network connection.')
    return pop_df


def join_pop_to_tract(tract_gdf, pop_df):
    tract_gdf['GEOID'] = tract_gdf['GEOID'].astype(str)
    pop_df['GEOID'] = pop_df['GEOID'].astype(str)
    tract_pop_gdf = tract_gdf.merge(pop_df, on='GEOID', how='left')
    tract_pop_gdf.dropna(subset=['TotalPopulation'], inplace=True)
    return tract_pop_gdf


def intersect_tract_hazwaste(haz_waste_gdf, tract_pop_gdf):
    haz_waste_gdf = haz_waste_gdf.to_crs(tract_pop_gdf.crs)
    hazard_tract_pop_gdf = gpd.sjoin(tract_pop_gdf, haz_waste_gdf, how='inner', op='intersects')
    hazard_tract_pop_gdf = hazard_tract_pop_gdf.drop_duplicates(subset='GEOID')
    return hazard_tract_pop_gdf


def compute_pop(hazard_tract_pop_gdf):
    pop_in_hazard_tracts = hazard_tract_pop_gdf['TotalPopulation'].sum()
    print(f"The total population in the identified hazardous waste tracts is: {pop_in_hazard_tracts}")
    return pop_in_hazard_tracts


def pop_tract_map(tract_pop_gdf, hazard_tract_pop_gdf, savepath='map.png'):
    fig, ax = plt.subplots(1, figsize=(15, 10))
    tract_pop_gdf.plot(column='TotalPopulation', cmap='YlOrRd', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True,
                       legend_kwds={'label': "Population"})
    hazard_tract_pop_gdf.boundary.plot(color='k', linewidth=1.5, ax=ax, zorder=2)
    ax.axis('off')
    ax.set_title('Population Distribution and Hazardous Waste Sites in NC',
                 fontdict={'fontsize': '25', 'fontweight': '3'})
    plt.savefig(savepath, dpi=300)
    plt.close(fig)
    print(f'Map is saved to {savepath}.')
    return Image(savepath)


def assembely_solution():
    haz_waste_gdf = load_haz_waste_shp()
    tract_gdf = load_tract_shp()
    pop_df = load_pop_csv()
    tract_pop_gdf = join_pop_to_tract(tract_gdf, pop_df)
    hazard_tract_pop_gdf = intersect_tract_hazwaste(haz_waste_gdf, tract_pop_gdf)
    pop_in_hazard_tracts = compute_pop(hazard_tract_pop_gdf)
    map_img = pop_tract_map(tract_pop_gdf, hazard_tract_pop_gdf)

    print(pop_in_hazard_tracts)
    return map_img


assembely_solution()