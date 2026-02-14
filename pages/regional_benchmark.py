import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from data_utils import get_filtered_df, get_crosstab_pct, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import get_plotly_scale

st.markdown("# :primary[:material/public:] Regional Benchmark Tool")
st.markdown("Compare metrics and trends across different global regions and markets")

df = get_filtered_df()
regions = sorted(df['region'].dropna().unique())

region_opts = {f"{r} ({len(df[df['region']==r]):,})": r for r in regions}

init_multiselect_state("rb_regions", "All regions")

with st.container(border=True):
    st.markdown("#### :primary[:material/settings:] Region Selection")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    st.multiselect(
        "Select Regions to Compare:",
        options=["All regions"] + list(region_opts.keys()),
        key="rb_regions"
    )
    selected_regions = get_multiselect_values("rb_regions", "All regions", region_opts)
    
    if not selected_regions:
        selected_regions = regions

all_regions = selected_regions

REGION_TO_LOCATIONS = {
    'United States / Canada': ['USA', 'CAN'],
    'Europe (EU / UK)': ['GBR', 'DEU', 'FRA', 'ITA', 'ESP', 'NLD', 'BEL', 'POL', 'SWE', 'AUT', 'PRT', 'IRL', 'DNK', 'FIN', 'NOR', 'CHE', 'CZE', 'GRC', 'HUN', 'ROU'],
    'Asia–Pacific': ['CHN', 'JPN', 'KOR', 'IND', 'SGP', 'THA', 'VNM', 'MYS', 'IDN', 'PHL', 'TWN', 'HKG'],
    'Latin America': ['BRA', 'MEX', 'ARG', 'COL', 'CHL', 'PER', 'VEN', 'ECU'],
    'Australia / New Zealand': ['AUS', 'NZL'],
    'Middle East / Africa': ['ZAF', 'EGY', 'NGA', 'KEN', 'SAU', 'ARE', 'ISR', 'TUR'],
}

with st.container(border=True):
    st.markdown("#### :primary[:material/map:] Global Distribution")
    
    col_map1, col_map2 = st.columns(2)
    with col_map1:
        map_metric = st.selectbox(
            "Display metric:",
            options=["Respondents", "Daily AI Users %", "AI Embedded %", "Firefighting %", "Growth Expected %"],
            key="map_metric"
        )
    with col_map2:
        color_scales = ["Viridis", "Plasma", "Inferno", "Magma", "Cividis", "Turbo", "Electric", "Teal", "Sunsetdark", "Blues", "Greens", "Reds", "Oranges", "Purples"]
        map_color = st.selectbox(
            "Color scheme:",
            options=color_scales,
            key="map_color"
        )
    
    map_data = []
    for region in all_regions:
        if region == 'Prefer not to say':
            continue
        region_df = df[df['region'] == region]
        if len(region_df) == 0:
            continue
            
        if map_metric == "Respondents":
            value = len(region_df)
        elif map_metric == "Daily AI Users %":
            value = (region_df['daily_ai_user'].sum() / len(region_df) * 100)
        elif map_metric == "AI Embedded %":
            value = (region_df['ai_embedded'].sum() / len(region_df) * 100)
        elif map_metric == "Firefighting %":
            value = (region_df['has_firefighting'].sum() / len(region_df) * 100)
        else:
            value = ((region_df['team_growth_2026'] == 'Grow').sum() / len(region_df) * 100)
        
        for iso_code in REGION_TO_LOCATIONS.get(region, []):
            map_data.append({
                'iso_alpha': iso_code,
                'region': region,
                'value': value
            })
    
    if map_data:
        map_df = pd.DataFrame(map_data)
        fig_map = px.choropleth(
            map_df,
            locations='iso_alpha',
            color='value',
            hover_name='region',
            color_continuous_scale=map_color,
            labels={'value': map_metric},
            projection='natural earth'
        )
        fig_map.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor='#555555',
                bgcolor='rgba(0,0,0,0)',
                landcolor='#1a1a1a',
                showland=True,
                showocean=True,
                oceancolor='#0d1117',
                lakecolor='#0d1117',
                countrycolor='#333333'
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No data available for map visualization")

with st.container(border=True):
    st.markdown("#### :primary[:material/bar_chart:] Regional Comparison")
    
    init_multiselect_state("rc_regions", "All regions")
    
    st.multiselect(
        "Select Regions:",
        options=["All regions"] + list(region_opts.keys()),
        key="rc_regions"
    )
    rc_selected = get_multiselect_values("rc_regions", "All regions", region_opts)
    if not rc_selected:
        rc_selected = regions
    
    rc_selected_sorted = [r for r in rc_selected if r != 'Prefer not to say']
    if 'Prefer not to say' in rc_selected:
        rc_selected_sorted.append('Prefer not to say')
    
    col_rc1, col_rc2 = st.columns(2)
    with col_rc1:
        comparison_metric = st.selectbox(
            "Compare on:",
            options=["storage_environment", "orchestration", "ai_adoption", 
                     "modeling_approach", "biggest_bottleneck", "team_growth_2026"],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="rb_metric"
        )
    
    df_regions = df[df['region'].isin(rc_selected_sorted)]
    metric_unique = df_regions[comparison_metric].nunique()
    
    with col_rc2:
        top_n_values = st.slider(
            "Top values to show:",
            min_value=1,
            max_value=metric_unique,
            value=min(6, metric_unique),
            key="rc_top_n"
        )
    
    top_values = df_regions[comparison_metric].value_counts().head(top_n_values).index.tolist()
    df_regions_filtered = df_regions[df_regions[comparison_metric].isin(top_values)]
    
    grouped_data = df_regions_filtered.groupby(['region', comparison_metric]).size().reset_index(name='count')
    totals = df_regions_filtered.groupby('region').size().reset_index(name='total')
    grouped_data = grouped_data.merge(totals, on='region')
    grouped_data['percentage'] = (grouped_data['count'] / grouped_data['total'] * 100).round(1)
    
    chart = alt.Chart(grouped_data).mark_bar().encode(
        x=alt.X('region:N', title=None, sort=rc_selected_sorted),
        y=alt.Y('percentage:Q', title='Percentage'),
        color=alt.Color(f'{comparison_metric}:N', scale=alt.Scale(scheme='tableau10'), sort=top_values, legend=alt.Legend(title=None, orient='bottom', direction='horizontal')),
        xOffset=alt.XOffset(f'{comparison_metric}:N', sort=top_values),
        tooltip=['region:N', f'{comparison_metric}:N', alt.Tooltip('percentage:Q', format='.1f')]
    ).properties(height=350)
    
    col_chart, col_insights = st.columns([2, 1])
    
    with col_chart:
        st.altair_chart(chart, use_container_width=True)
    
    with col_insights:
        st.markdown("##### :primary[:material/insights:] Key Insights")
        
        if len(grouped_data) > 0 and len(top_values) > 0:
            top_cat = top_values[0]
            top_cat_data = grouped_data[grouped_data[comparison_metric] == top_cat]
            if len(top_cat_data) > 0:
                leader_row = top_cat_data.loc[top_cat_data['percentage'].idxmax()]
                leader_region = leader_row['region']
                leader_pct = leader_row['percentage']
                top_cat_clean = top_cat.split('(')[0].strip() if '(' in top_cat else top_cat
                
                runner_up = top_cat_data.loc[top_cat_data['percentage'] != top_cat_data['percentage'].max()]
                runner_region = runner_up.loc[runner_up['percentage'].idxmax(), 'region'] if len(runner_up) > 0 else "N/A"
                runner_pct = runner_up['percentage'].max() if len(runner_up) > 0 else 0
                
                second_cat = top_values[1] if len(top_values) > 1 else None
                second_leader = ""
                if second_cat:
                    second_cat_data = grouped_data[grouped_data[comparison_metric] == second_cat]
                    if len(second_cat_data) > 0:
                        second_row = second_cat_data.loc[second_cat_data['percentage'].idxmax()]
                        second_cat_clean = second_cat.split('(')[0].strip() if '(' in second_cat else second_cat
                        second_leader = f" **{second_cat_clean}** finds its strongest adoption in {second_row['region']} at {second_row['percentage']:.0f}%."
                
                spread = leader_pct - runner_pct if runner_pct > 0 else 0
                spread_note = f" The gap of {spread:.0f}pp to {runner_region} highlights significant regional variation." if spread > 5 else " Regional adoption remains relatively balanced across markets."
                
                st.caption(f"**{top_cat_clean}** leads in {leader_region} at {leader_pct:.0f}%.{spread_note}{second_leader} These patterns reflect how regional infrastructure maturity and market dynamics shape technology choices.")

regions = df['region'].unique().tolist()

metrics_for_radar = {
    'Daily AI Users': lambda d: (d['daily_ai_user'].sum() / len(d) * 100) if len(d) > 0 else 0,
    'AI Embedded': lambda d: (d['ai_embedded'].sum() / len(d) * 100) if len(d) > 0 else 0,
    'Firefighting': lambda d: (d['has_firefighting'].sum() / len(d) * 100) if len(d) > 0 else 0,
    'Leadership Gap': lambda d: (d['has_leadership_gap'].sum() / len(d) * 100) if len(d) > 0 else 0,
    'Growth Expected': lambda d: ((d['team_growth_2026'] == 'Grow').sum() / len(d) * 100) if len(d) > 0 else 0,
}

with st.container(border=True):
    st.markdown("#### :primary[:material/table_chart:] Regional Summary")
    
    summary_data = []
    for region in regions:
        region_df = df[df['region'] == region]
        summary_data.append({
            'Region': region,
            'Daily AI': metrics_for_radar['Daily AI Users'](region_df),
            'AI Embedded': metrics_for_radar['AI Embedded'](region_df),
            'Firefighting': metrics_for_radar['Firefighting'](region_df),
            'Leadership Gap': metrics_for_radar['Leadership Gap'](region_df),
            'Growth Expected': metrics_for_radar['Growth Expected'](region_df),
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    prefer_not = summary_df[summary_df['Region'] == 'Prefer not to say']
    others = summary_df[summary_df['Region'] != 'Prefer not to say']
    summary_df = pd.concat([others, prefer_not], ignore_index=True)
    
    col_heatmap, col_tldr = st.columns([1.5, 1])
    
    with col_heatmap:
        heatmap_df = summary_df.set_index('Region')
        
        fig_heatmap = px.imshow(
            heatmap_df.values,
            x=heatmap_df.columns.tolist(),
            y=heatmap_df.index.tolist(),
            color_continuous_scale=get_plotly_scale(),
            aspect='auto'
        )
        fig_heatmap.update_traces(xgap=2, ygap=2)
        
        values = heatmap_df.values
        max_val = values.max()
        
        annotations = []
        for i, row_name in enumerate(heatmap_df.index):
            for j, col_name in enumerate(heatmap_df.columns):
                val = values[i][j]
                text_color = 'white' if val > max_val * 0.5 else '#333333'
                annotations.append(dict(
                    x=col_name, y=row_name,
                    text=f'{val:.1f}',
                    showarrow=False,
                    font=dict(color=text_color, size=11)
                ))
        
        fig_heatmap.update_layout(
            height=450,
            margin=dict(l=0, r=0, t=60, b=0),
            coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(tickfont=dict(color='#cccccc'), tickangle=90, side='top'),
            yaxis=dict(tickfont=dict(color='#cccccc')),
            annotations=annotations
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col_tldr:
        st.markdown("##### :primary[:material/insights:] Key Insights")
        
        if len(summary_df) > 0:
            top_ai_embed = summary_df.loc[summary_df['AI Embedded'].idxmax(), 'Region']
            top_ai_embed_val = summary_df['AI Embedded'].max()
            
            lowest_fire = summary_df.loc[summary_df['Firefighting'].idxmin(), 'Region']
            lowest_fire_val = summary_df['Firefighting'].min()
            
            top_growth = summary_df.loc[summary_df['Growth Expected'].idxmax(), 'Region']
            top_growth_val = summary_df['Growth Expected'].max()
            
            highest_lead_gap = summary_df.loc[summary_df['Leadership Gap'].idxmax(), 'Region']
            highest_lead_gap_val = summary_df['Leadership Gap'].max()
            
            avg_ai_embed = summary_df['AI Embedded'].mean()
            avg_fire = summary_df['Firefighting'].mean()
            avg_growth = summary_df['Growth Expected'].mean()
            
            st.caption(f"**Most AI mature:** {top_ai_embed} ({top_ai_embed_val:.0f}% embedded) — Leading the pack with AI integration {top_ai_embed_val - avg_ai_embed:.0f}% above the regional average, indicating stronger organizational commitment to AI-driven workflows.")
            
            st.caption(f"**Most stable ops:** {lowest_fire} ({lowest_fire_val:.0f}% firefighting) — With firefighting {avg_fire - lowest_fire_val:.0f}% below average, this region demonstrates more mature processes and less reactive work patterns.")
            
            st.caption(f"**Most bullish:** {top_growth} ({top_growth_val:.0f}% expect growth) — Growth expectations exceed the regional average by {top_growth_val - avg_growth:.0f}%, signaling strong confidence in data team expansion.")
            
            st.caption(f"**Needs direction:** {highest_lead_gap} ({highest_lead_gap_val:.0f}% leadership gap) — Higher leadership gap scores suggest teams in this region may benefit from clearer strategic alignment and executive sponsorship.")
