import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.transforms import Affine2D

st.set_page_config(layout="wide")

def d_hondt(votes, seats):
    quotients = [(vote_count / i, party) for party, vote_count in votes.items() for i in range(1, seats + 1)]
    quotients.sort(reverse=True, key=lambda x: x[0])
    seat_allocation = {}
    for _, party in quotients[:seats]:
        seat_allocation[party] = seat_allocation.get(party, 0) + 1
    return seat_allocation

def sainte_lague(votes, seats):
    quotients = [(vote_count / (2 * i + 1), party) for party, vote_count in votes.items() for i in range(seats)]
    quotients.sort(reverse=True, key=lambda x: x[0])
    seat_allocation = {}
    for _, party in quotients[:seats]:
        seat_allocation[party] = seat_allocation.get(party, 0) + 1
    return seat_allocation

def modified_sainte_lague(votes, seats):
    quotients = [(vote_count / 1.4, party) for party, vote_count in votes.items()]
    for party, vote_count in votes.items():
        quotients.extend([(vote_count / (2 * i + 1), party) for i in range(1, seats)])
    quotients.sort(reverse=True, key=lambda x: x[0])
    seat_allocation = {}
    for _, party in quotients[:seats]:
        seat_allocation[party] = seat_allocation.get(party, 0) + 1
    return seat_allocation

def largest_remainder(votes, seats, quota_func):
    total_votes = sum(votes.values())
    quota = quota_func(total_votes, seats)
    allocation = {party: int(vote_count // quota) for party, vote_count in votes.items()}
    remainders = {party: vote_count % quota for party, vote_count in votes.items()}
    remaining_seats = seats - sum(allocation.values())
    sorted_remainders = sorted(remainders.items(), key=lambda x: x[1], reverse=True)
    for party, _ in sorted_remainders[:remaining_seats]:
        allocation[party] += 1
    return allocation

def hare_quota(total_votes, seats):
    return total_votes / seats

def convert_to_float(value):
    try:
        return float(value.strip('%')) / 100.0
    except ValueError:
        return 0.0

def allocate_seats(votes, method, seats, threshold, quota_func=None):
    total_votes = sum(votes.values())
    votes = {party: vote for party, vote in votes.items() if vote / total_votes >= threshold}
    if method == largest_remainder:
        return method(votes, seats, quota_func)
    else:
        return method(votes, seats)

def allocate_seats_by_constituencies(df, methods):
    results = []
    for constituency, method_params in methods.items():
        if constituency not in df['Distrikt'].unique():
            st.warning(f"Column for {constituency} not found in the data.")
            continue
        for method_name, seats, threshold, *extra in method_params:
            method = method_name
            votes = {party: df[(df['Distrikt'] == constituency) & (df['Parti'] == party)]['Stemmer'].values[0] for party in df['Parti'].unique() if df[(df['Distrikt'] == constituency) & (df['Parti'] == party)]['Stemmer'].values[0] > 0}
            allocation = allocate_seats(votes, method, seats, threshold, hare_quota)
            for party, seat_count in allocation.items():
                results.append({'Parti': party, 'Constituency': constituency, 'Seats': seat_count})
    return pd.DataFrame(results)

def plot_half_circle_chart(data, colors, kategori_mapping):
    
    aggregated_data = data.groupby(['Parti', 'Kategori']).sum().reset_index()
    aggregated_data = aggregated_data.sort_values(by='Kategori', ascending=False)
   
    fictitious_party = pd.DataFrame({
        'Parti': ['Fiktivt Parti'],
        'Kategori': [0],
        'Seats': [sum(aggregated_data['Seats'])]
    })
    aggregated_data = pd.concat([aggregated_data, fictitious_party], ignore_index=True)
   
    total_mandates = sum(aggregated_data['Seats'])
   
    if total_mandates == 0:
        st.error("The total of seats cannot be zero.")
        return
   
    angles = aggregated_data['Seats'] / total_mandates * 360  
   
    fig, ax = plt.subplots(figsize=(10, 5), subplot_kw=dict(aspect="equal"))
    startangle = 270  
    wedges, texts = ax.pie(
        angles,
        startangle=startangle,
        colors=[colors.get(kategori, "#FFFFFF") if kategori != 0 else "#FFFFFF" for kategori in aggregated_data['Kategori']],
        wedgeprops=dict(width=0.3, edgecolor='none')
    )
   
    labels = []
    for i, wedge in enumerate(wedges):
        if aggregated_data['Parti'].iloc[i] == 'Fiktivt Parti':
            continue
        angle = (wedge.theta2 - wedge.theta1) / 2.0 + wedge.theta1
        x = np.cos(np.radians(angle))
        y = np.sin(np.radians(angle))

        label = ax.text(
            x * 0.7, y * 0.7,
            f"{aggregated_data['Parti'].iloc[i]}: {aggregated_data['Seats'].iloc[i]}",
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.6),
            rotation=90
        )
        labels.append(label)
   
    plt.gca().set_aspect('equal')
    fig.tight_layout()
    plt.gca().set_position([0, 0, 1, 1])
    fig.canvas.draw()
   
    trans_data = Affine2D().rotate_deg(90) + ax.transData
    for text in texts:
        text.set_transform(trans_data)
    for wedge in wedges:
        wedge.set_transform(trans_data)
    for label in labels:
        label.set_transform(trans_data)
   
    ax.set(aspect="equal", title="Seat distribution among political groups\nin the European Parliament")
    st.pyplot(fig)

default_values = {'Parti': ['EPP', 'S&D', 'ECR', 'RE', 'GUE/NGL', 'G/EFA', 'ID', 'NI', 'Valgdeltagelse', 'Antall personer med stemmerett'], 'Kategori': [8, 3, 9, 6, 1, 5, 10, 11, 11, 11], 'Austria': ['35 %', '24 %', '0 %', '9 %', '0 %', '14 %', '18 %', '0 %', '60 %', '7400000'], 'Belgium_Flemish': ['15 %', '10 %', '19 %', '16 %', '5 %', '12 %', '22 %', '0 %', '88 %', '4700000'], 'Belgium_French': ['10 %', '30 %', '0 %', '22 %', '16 %', '22 %', '0 %', '0 %', '88 %', '3600000'], 'Belgium_German': ['100 %', '0 %', '0 %', '0 %', '0 %', '0 %', '0 %', '0 %', '88 %', '50000'], 'Bulgaria': ['39 %', '31 %', '0 %', '29 %', '0 %', '0 %', '1 %', '0 %', '33 %', '5800000'], 'Croatia': ['47 %', '39 %', '10 %', '0 %', '0 %', '4 %', '0 %', '0 %', '30 %', '3700000'], 'Cyprus': ['26 %', '22 %', '0 %', '19 %', '25 %', '0 %', '0 %', '8 %', '45 %', '700000'], 'Czech Republic': ['24 %', '0 %', '29 %', '0 %', '0 %', '28 %', '18 %', '0 %', '29 %', '8600000'], 'Denmark': ['9 %', '30 %', '0 %', '36 %', '8 %', '18 %', '0 %', '0 %', '66 %', '4500000'], 'Estonia': ['12 %', '27 %', '0 %', '47 %', '0 %', '0 %', '15 %', '0 %', '38 %', '900000'], 'Finland': ['24 %', '17 %', '16 %', '16 %', '8 %', '19 %', '0 %', '0 %', '41 %', '4500000'], 'France': ['18 %', '10 %', '0 %', '0 %', '14 %', '21 %', '37 %', '0 %', '50 %', '48700000'], 'Germany': ['30 %', '17 %', '1 %', '8 %', '7 %', '26 %', '12 %', '0 %', '61 %', '64800000'], 'Greece': ['26 %', '6 %', '3 %', '0 %', '19 %', '0 %', '0 %', '46 %', '59 %', '9900000'], 'Hungary': ['0 %', '55 %', '0 %', '34 %', '0 %', '0 %', '0 %', '11 %', '43 %', '8200000'], 'Ireland_Dublin': ['38 %', '2 %', '0 %', '21 %', '25 %', '15 %', '0 %', '0 %', '50 %', '850000'], 'Ireland_Midland_North_West': ['38 %', '2 %', '0 %', '21 %', '25 %', '15 %', '0 %', '0 %', '50 %', '1300000'], 'Ireland_South': ['38 %', '2 %', '0 %', '21 %', '25 %', '15 %', '0 %', '0 %', '50 %', '1450000'], 'Italy_Central': ['10 %', '25 %', '7 %', '0 %', '0 %', '0 %', '38 %', '19 %', '55 %', '11700000'], 'Italy_Islands': ['10 %', '25 %', '7 %', '0 %', '0 %', '0 %', '38 %', '19 %', '55 %', '6400000'], 'Italy_North_East': ['10 %', '25 %', '7 %', '0 %', '0 %', '0 %', '38 %', '19 %', '55 %', '11500000'], 'Italy_North_West': ['10 %', '25 %', '7 %', '0 %', '0 %', '0 %', '38 %', '19 %', '55 %', '15800000'], 'Italy_Southern': ['10 %', '25 %', '7 %', '0 %', '0 %', '0 %', '38 %', '19 %', '55 %', '13500000'], 'Latvia': ['52 %', '0 %', '32 %', '10 %', '0 %', '6 %', '0 %', '0 %', '34 %', '1500000'], 'Lithuania': ['47 %', '38 %', '0 %', '16 %', '0 %', '0 %', '0 %', '0 %', '53 %', '2400000'], 'Luxembourg': ['29 %', '17 %', '0 %', '29 %', '0 %', '26 %', '0 %', '0 %', '84 %', '500000'], 'Malta': ['59 %', '41 %', '0 %', '0 %', '0 %', '0 %', '0 %', '0 %', '73 %', '400000'], 'Netherlands': ['16 %', '25 %', '9 %', '28 %', '4 %', '14 %', '5 %', '0 %', '42 %', '13300000'], 'Poland_Greater_Poland': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '3250000'], 'Poland_Kuyavian_Pomeranian': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '1800000'], 'Poland_Lesser_Poland_Swietokrzyskie': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '3600000'], 'Poland_Lodz': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '1700000'], 'Poland_Lower_Silesian_Opole': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '2750000'], 'Poland_Lublin': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '1800000'], 'Poland_Lubusz_West_Pomeranian': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '1900000'], 'Poland_Masovian': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '3200000'], 'Poland_Podlaskie_Warmian_Masurian': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '1650000'], 'Poland_Pomeranian': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '1900000'], 'Poland_Silesian': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '3000000'], 'Poland_Subcarpathian': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '1500000'], 'Poland_Warsaw': ['43 %', '8 %', '43 %', '0 %', '0 %', '0 %', '6 %', '0 %', '46 %', '2000000'], 'Portugal': ['30 %', '46 %', '0 %', '3 %', '14 %', '7 %', '0 %', '0 %', '31 %', '9800000'], 'Romania': ['42 %', '29 %', '0 %', '29 %', '0 %', '0 %', '0 %', '0 %', '51 %', '15500000'], 'Slovakia': ['25 %', '0 %', '16 %', '33 %', '0 %', '0 %', '0 %', '26 %', '25 %', '4400000'], 'Slovenia': ['100 %', '0 %', '0 %', '0 %', '0 %', '0 %', '0 %', '0 %', '29 %', '1800000'], 'Spain': ['25 %', '41 %', '8 %', '6 %', '13 %', '7 %', '0 %', '0 %', '61 %', '38100000'], 'Sweden': ['23 %', '32 %', '21 %', '0 %', '9 %', '16 %', '0 %', '0 %', '55 %', '8300000']}

df = pd.DataFrame(default_values)
districts = [col for col in df.columns if col not in ['Parti', 'Kategori']]
email_address = "alberto@vthoresen.no"
st.title("EU Parliament Election Simulator")
st.markdown(f"Contact: [Alberto Valiente Thoresen](mailto:{email_address})")
st.markdown("""
Adjust your forecasts using the menu on the left. Voter turnout by country can also be registered at the bottom of this menu.

The starting point for the simulation is the forecast "vote share by member state" for the EU Parliament Election 2024, presented [here](https://ecfr.eu/publication/a-sharp-right-turn-a-forecast-for-the-2024-european-parliament-elections/) , with rough population estimates for 2024.
When not available, vote shares per constituency are estimated on the basis of the expected vote share for the respective member state that the constituency belongs to.

In the original forecast, the authors warn that "vote shares do not add up to 100 per cent because we do not show minor parties or votes for 'other' parties." 
However, in this simulation, vote shares are normalized, so they do add to 100 % by constituency. This starting point might overestimate the number of seats for certain parliamentary groups.
You also have to take in consideration that the poll was from Januar 2024. 
But you can update these values by adjusting the sliders with more recent forecasts.

This program calculates seat allocation by applying the correct method used in each constituency for the number of seats available, considering current political group thresholds.
These methods include [D'Hont Method](https://en.wikipedia.org/wiki/D%27Hondt_method), [Sainte-Laguë Method (including the modified version)](https://en.wikipedia.org/wiki/Sainte-Lagu%C3%AB_method) and [Largest Remainder Method](https://en.wikipedia.org/wiki/Largest_remainders_method).
An overview of the methods used by constituency is presented [here](https://en.wikipedia.org/wiki/2024_European_Parliament_election).

**Note**: For simplicity, this program uses Sainte-Laguë instead of the Single Transferable Vote (STV) method for Ireland and Malta. The Sainte-Laguë method still provides proportional representation at the political group level. For more information on the intricacies of the STV method, see [Single Transferable Vote - Disadvantages](https://aceproject.org/main/english/es/esf04b.htm). This summary provides a good overview of the challenges involved in forecasting this method based on political groups and programming such forecasts.

A diagram showing the resulting distribution of seats in the forecast will be presented below. It may take some time to visualize.
""")

percentage_dict = {}
participation_dict = {}
st.sidebar.header("You can adjust percentages here")
for distrikt in districts:
    if distrikt not in ['Valgdeltagelse', 'Antall personer med stemmerett']:
        st.sidebar.subheader(distrikt)
        for index, row in df.iterrows():
            if row['Parti'] not in ['Valgdeltagelse', 'Antall personer med stemmerett']:
                default_percentage = float(row[distrikt].strip('%'))
                modified_percentage = st.sidebar.slider(f"{row['Parti']} ({distrikt})", 0.0, 100.0, default_percentage)
                percentage_dict[(row['Parti'], distrikt)] = f"{modified_percentage}%"
st.sidebar.header("You can adjust election turnout by country here")
for distrikt in districts:
    if distrikt not in ['Antall personer med stemmerett']:
        participation_row = df[df['Parti'] == 'Valgdeltagelse']
        default_participation = float(participation_row[distrikt].values[0].strip('%'))
        modified_participation = st.sidebar.slider(f"Turnout ({distrikt})", 0.0, 100.0, default_participation)
        participation_dict[distrikt] = f"{modified_participation}%"

def calculate_stemmer(row, percentage_dict, participation_dict):
    stemmer_data = []
    for distrikt in districts:
        percentage = percentage_dict.get((row['Parti'], distrikt), row[distrikt])
        valgdeltakelse = participation_dict.get(distrikt, df[df['Parti'] == 'Valgdeltagelse'][distrikt].values[0])
        personer_med_stemmerett = df[df['Parti'] == 'Antall personer med stemmerett'][distrikt].values[0]
       
        if pd.notna(percentage) and pd.notna(valgdeltakelse) and pd.notna(personer_med_stemmerett):
            percentage_value = float(percentage.strip('%')) / 100
            valgdeltakelse_value = float(valgdeltakelse.strip('%')) / 100
            personer_value = float(personer_med_stemmerett.replace(',', ''))
            stemmer = percentage_value * valgdeltakelse_value * personer_value
            stemmer_data.append(stemmer)
        else:
            stemmer_data.append(np.nan)
    return stemmer_data

results = {'Parti': [], 'Distrikt': [], 'Stemmer': [], 'Kategori': []}
for index, row in df.iterrows():
    if row['Parti'] not in ['Valgdeltagelse', 'Antall personer med stemmerett']:
        stemmer_data = calculate_stemmer(row, percentage_dict, participation_dict)
        for distrikt, stemmer in zip(districts, stemmer_data):
            results['Parti'].append(row['Parti'])
            results['Distrikt'].append(distrikt)
            results['Stemmer'].append(stemmer)
            results['Kategori'].append(row['Kategori'])

results_df = pd.DataFrame(results)

results_df_english = results_df.copy()
results_df_english.columns = ['Political Group' if col == 'Parti' else 
                              'Constituency' if col == 'Distrikt' else 
                              'Votes' if col == 'Stemmer' else 
                              col for col in results_df_english.columns]
if 'Kategori' in results_df_english.columns:
    results_df_english.drop('Kategori', axis=1, inplace=True)

st.write("### Total votes by party and country")
st.dataframe(results_df_english)

country_methods = {
    'Austria': [(d_hondt, 20, 0.04)],
    'Belgium_Flemish': [(d_hondt, 13, 0.05)],
    'Belgium_French': [(d_hondt, 8, 0.05)],
    'Belgium_German': [(d_hondt, 1, 0.05)],
    'Bulgaria': [(largest_remainder, 17, 0.059, hare_quota)],
    'Croatia': [(d_hondt, 12, 0.05)],
    'Cyprus': [(largest_remainder, 6, 0.018, hare_quota)],
    'Czech Republic': [(d_hondt, 21, 0.05)],
    'Denmark': [(d_hondt, 15, 0)],
    'Estonia': [(d_hondt, 7, 0)],
    'Finland': [(d_hondt, 15, 0)],
    'France': [(d_hondt, 81, 0.05)],
    'Germany': [(sainte_lague, 96, 0)],
    'Greece': [(largest_remainder, 21, 0.03, hare_quota)],
    'Hungary': [(d_hondt, 21, 0.05)],
    'Ireland_Dublin': [(sainte_lague, 4, 0)], ## Using Sainte-Laguë instead of Single Transferable Vote for simplicity
    'Ireland_Midland_North_West': [(sainte_lague, 4, 0)],## Using Sainte-Laguë instead of Single Transferable Vote for simplicity
    'Ireland_South': [(sainte_lague, 6, 0)], ## Using Sainte-Laguë instead of Single Transferable Vote for simplicity
    'Italy_North_West': [(largest_remainder, 21, 0.04, hare_quota)],
    'Italy_North_East': [(largest_remainder, 15, 0.04, hare_quota)],
    'Italy_Central': [(largest_remainder, 14, 0.04, hare_quota)],
    'Italy_Southern': [(largest_remainder, 18, 0.04, hare_quota)],
    'Italy_Islands': [(largest_remainder, 8, 0.04, hare_quota)],
    'Latvia': [(sainte_lague, 9, 0.05)],
    'Lithuania': [(largest_remainder, 11, 0.05, hare_quota)],
    'Luxembourg': [(d_hondt, 6, 0)],
    'Malta': [(sainte_lague, 6, 0)],## Using Sainte-Laguë instead of Single Transferable Vote for simplicity
    'Netherlands': [(d_hondt, 31, 0.032)],
    'Poland_Greater_Poland': [(d_hondt, 4, 0.05)],
    'Poland_Kuyavian_Pomeranian': [(d_hondt, 2, 0.05)],
    'Poland_Lesser_Poland_Swietokrzyskie': [(d_hondt, 4, 0.05)],
    'Poland_Lodz': [(d_hondt, 3, 0.05)],
    'Poland_Lower_Silesian_Opole': [(d_hondt, 4, 0.05)],
    'Poland_Lublin': [(d_hondt, 4, 0.05)],
    'Poland_Lubusz_West_Pomeranian': [(d_hondt, 4, 0.05)],
    'Poland_Masovian': [(d_hondt, 4, 0.05)],
    'Poland_Podlaskie_Warmian_Masurian': [(d_hondt, 3, 0.05)],
    'Poland_Pomeranian': [(d_hondt, 3, 0.05)],
    'Poland_Silesian': [(d_hondt, 8, 0.05)],
    'Poland_Subcarpathian': [(d_hondt, 3, 0.05)],
    'Poland_Warsaw': [(d_hondt, 7, 0.05)],
    'Portugal': [(d_hondt, 21, 0)],
    'Romania': [(d_hondt, 33, 0.05)],
    'Slovakia': [(largest_remainder, 15, 0.05, hare_quota)],
    'Slovenia': [(d_hondt, 9, 0)],
    'Spain': [(d_hondt, 61, 0)],
    'Sweden': [(modified_sainte_lague, 21, 0.04)],
}

kategori_mapping = dict(zip(df['Parti'], df['Kategori']))
results_allocation = allocate_seats_by_constituencies(results_df, country_methods)

if 'Parti' in results_allocation.columns and 'Seats' in results_allocation.columns:
    grouped_results = results_allocation.groupby(['Parti', 'Constituency']).agg({'Seats': 'sum'}).reset_index()
    grouped_results = pd.merge(grouped_results, df[['Parti', 'Kategori']].drop_duplicates(), on='Parti', how='left')
else:
    st.warning("Seat allocation results do not contain the expected columns. Please check the allocation logic.")

grouped_results_english = grouped_results.copy()

grouped_results_english.columns = ['Political Group' if col == 'Parti' else 
                                   'Constituency' if col == 'Distrikt' else 
                                   'Seats' if col == 'Seats' else 
                                   col for col in grouped_results_english.columns]

if 'Kategori' in grouped_results_english.columns:
    grouped_results_english.drop('Kategori', axis=1, inplace=True)

st.write("### Seat distribution by political group and country")
st.dataframe(grouped_results_english)


color_mapping = {
    1: '#8B0000',  
    2: '#FF0000',   
    3: '#FF6347',   
    4: '#FF7F7F',   
    5: '#006400',   
    6: '#ADD8E6',   
    7: '#0000FF',   
    8: '#00008B',   
    9: '#140080',   
    10: '#14145A',  
    11: '#FFFF00'   
}


plot_half_circle_chart(grouped_results, color_mapping, kategori_mapping)
