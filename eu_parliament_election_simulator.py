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

default_values = {'Parti': ['EPP', 'S&D', 'ECR', 'RE', 'GUE/NGL', 'G/EFA', 'ID', 'NI', 'Valgdeltagelse', 'Antall personer med stemmerett'], 'Kategori': [8, 3, 9, 6, 1, 5, 10, 11, 11, 11], 'Austria': ['38.75%', '27.92%', '0.00%', '5.42%', '0.00%', '11.25%', '16.67%', '0.00%', '60.00%', '7400000'], 'Belgium_Flemish': ['12.15%', '25.23%', '0.00%', '25.23%', '12.15%', '25.23%', '0.00%', '0.00%', '88.00%', '4700000'], 'Belgium_French': ['16.88%', '8.12%', '25.00%', '16.88%', '0.00%', '8.12%', '25.00%', '0.00%', '88.00%', '3600000'], 'Belgium_German': ['12.15%', '25.23%', '0.00%', '25.23%', '12.15%', '25.23%', '0.00%', '0.00%', '88.00%', '50000'], 'Bulgaria': ['40.97%', '29.52%', '11.89%', '17.62%', '0.00%', '0.00%', '0.00%', '0.00%', '33.00%', '5800000'], 'Croatia': ['36.30%', '27.40%', '8.90%', '8.90%', '0.00%', '0.00%', '0.00%', '18.49%', '30.00%', '3700000'], 'Cyprus': ['33.33%', '33.33%', '0.00%', '0.00%', '33.33%', '0.00%', '0.00%', '0.00%', '45.00%', '700000'], 'Czech Republic': ['23.93%', '0.00%', '18.93%', '28.57%', '4.64%', '14.29%', '9.64%', '0.00%', '29.00%', '8600000'], 'Denmark': ['7.51%', '23.12%', '0.00%', '38.73%', '7.51%', '15.61%', '7.51%', '0.00%', '66.00%', '4500000'], 'Estonia': ['0.00%', '33.75%', '0.00%', '50.00%', '0.00%', '0.00%', '16.25%', '0.00%', '38.00%', '900000'], 'Finland': ['22.99%', '15.52%', '0.00%', '22.99%', '7.47%', '15.52%', '15.52%', '0.00%', '41.00%', '4500000'], 'France': ['10.84%', '6.79%', '0.00%', '28.37%', '8.11%', '16.21%', '29.69%', '0.00%', '50.00%', '48700000'], 'Germany': ['30.23%', '16.68%', '1.02%', '7.28%', '6.26%', '26.08%', '11.43%', '1.02%', '61.00%', '64800000'], 'Greece': ['38.21%', '9.64%', '4.64%', '0.00%', '28.57%', '0.00%', '0.00%', '18.93%', '59.00%', '9900000'], 'Hungary': ['61.79%', '23.93%', '0.00%', '9.64%', '0.00%', '0.00%', '0.00%', '4.64%', '43.00%', '8200000'], 'Ireland_Dublin': ['36.30%', '0.00%', '0.00%', '8.90%', '36.30%', '18.49%', '0.00%', '0.00%', '50.00%', '850000'], 'Ireland_Midland_North_West': ['36.30%', '0.00%', '0.00%', '8.90%', '36.30%', '18.49%', '0.00%', '0.00%', '50.00%', '1300000'], 'Ireland_South': ['36.30%', '0.00%', '0.00%', '8.90%', '36.30%', '18.49%', '0.00%', '0.00%', '50.00%', '1450000'], 'Italy_Central': ['9.57%', '26.03%', '6.89%', '0.00%', '0.00%', '0.00%', '38.37%', '19.14%', '55.00%', '11700000'], 'Italy_Islands': ['9.57%', '26.03%', '6.89%', '0.00%', '0.00%', '0.00%', '38.37%', '19.14%', '55.00%', '6400000'], 'Italy_North_East': ['9.57%', '26.03%', '6.89%', '0.00%', '0.00%', '0.00%', '38.37%', '19.14%', '55.00%', '11500000'], 'Italy_North_West': ['9.57%', '26.03%', '6.89%', '0.00%', '0.00%', '0.00%', '38.37%', '19.14%', '55.00%', '15800000'], 'Italy_Southern': ['9.57%', '26.03%', '6.89%', '0.00%', '0.00%', '0.00%', '38.37%', '19.14%', '55.00%', '13500000'], 'Latvia': ['25.23%', '25.23%', '25.23%', '12.15%', '0.00%', '12.15%', '0.00%', '0.00%', '34.00%', '1500000'], 'Lithuania': ['36.05%', '18.37%', '8.84%', '18.37%', '0.00%', '18.37%', '0.00%', '0.00%', '53.00%', '2400000'], 'Luxembourg': ['33.75%', '16.25%', '0.00%', '33.75%', '0.00%', '16.25%', '0.00%', '0.00%', '84.00%', '500000'], 'Malta': ['33.75%', '66.25%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '73.00%', '400000'], 'Netherlands': ['23.12%', '23.12%', '15.32%', '23.12%', '3.76%', '11.56%', '0.00%', '0.00%', '42.00%', '13300000'], 'Poland_Greater_Poland': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '3250000'], 'Poland_Kuyavian_Pomeranian': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '1800000'], 'Poland_Lesser_Poland_Swietokrzyskie': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '3600000'], 'Poland_Lodz': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '1700000'], 'Poland_Lower_Silesian_Opole': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '2750000'], 'Poland_Lublin': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '1800000'], 'Poland_Lubusz_West_Pomeranian': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '1900000'], 'Poland_Masovian': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '3200000'], 'Poland_Podlaskie_Warmian_Masurian': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '1650000'], 'Poland_Pomeranian': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '1900000'], 'Poland_Silesian': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '3000000'], 'Poland_Subcarpathian': ['33.28%', '15.76%', '50.96%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '1500000'], 'Poland_Warsaw': ['33.00%', '16.00%', '51.00%', '0.00%', '0.00%', '0.00%', '0.00%', '0.00%', '46.00%', '2000000'], 'Portugal': ['33.33%', '43.01%', '0.00%', '0.00%', '19.00%', '4.66%', '0.00%', '0.00%', '31.00%', '9800000'], 'Romania': ['43.66%', '31.22%', '0.00%', '25.12%', '0.00%', '0.00%', '0.00%', '0.00%', '51.00%', '15500000'], 'Slovakia': ['30.46%', '22.99%', '15.52%', '15.52%', '0.00%', '0.00%', '0.00%', '15.52%', '25.00%', '4400000'], 'Slovenia': ['49.53%', '25.23%', '0.00%', '25.23%', '0.00%', '0.00%', '0.00%', '0.00%', '29.00%', '1800000'], 'Spain': ['22.22%', '36.94%', '5.56%', '14.86%', '11.11%', '3.75%', '0.00%', '5.56%', '61.00%', '38100000'], 'Sweden': ['29.96%', '25.09%', '14.98%', '14.98%', '4.87%', '10.11%', '0.00%', '0.00%', '55.00%', '8300000']}

df = pd.DataFrame(default_values)
districts = [col for col in df.columns if col not in ['Parti', 'Kategori']]
email_address = "alberto@vthoresen.no"
st.title("EU Parliament Election Simulator")
st.markdown(f"Contact: [Alberto Valiente Thoresen](mailto:{email_address})")
st.markdown("""
Adjust your forecasts using the menu on the left.
Voter turnout by country can also be registered at the bottom of this menu.

The starting point for the simulation is the distribution of seats in the EU Parliament by constituency, based on the 2019 election results, with rough population estimates for 2024.

Certain political groups start at 0% because they did not secure seats in those constituencies in 2019, although they may have received votes. You can update these values by adjusting the sliders with recent forecasts.

This program calculates seat allocation by applying the correct method that is used in each constituency for the number of seats available, and taking in consideration current political group thresholds.

**Note**: For simplicity, this program uses Sainte-Laguë instead of the Single Transferable Vote (STV) method for Ireland and Malta. The Sainte-Laguë still provides proportional representation at the political group level.

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
