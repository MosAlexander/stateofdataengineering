import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from data_utils import get_filtered_df, get_value_counts_pct, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import create_bar_chart, create_donut_chart, get_compare_colors

st.markdown("# :primary[:material/person:] Solo vs Team Practitioner Experience")
st.markdown("Compare challenges and tools across team structures and sizes")

df = get_filtered_df()

solo_df = df[df['org_size'] == '< 50 employees']
team_df = df[df['org_size'] != '< 50 employees']

n_solo = len(solo_df)
pct_solo = n_solo / len(df) * 100 if len(df) > 0 else 0

with st.container(border=True):
    st.markdown("#### :primary[:material/analytics:] Solo Practitioner Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Solo Practitioners", f"{n_solo:,}")
    col2.metric("% of Survey", f"{pct_solo:.1f}%")
    
    if n_solo > 0:
        top_challenge = solo_df['biggest_bottleneck'].value_counts().idxmax()
        top_challenge_short = top_challenge[:18] + "..." if len(top_challenge) > 18 else top_challenge
        col3.metric("Top Challenge", top_challenge_short)
        
        solo_growth = (solo_df['team_growth_2026'] == 'Grow').sum() / n_solo * 100
        col4.metric("Expect Growth", f"{solo_growth:.0f}%")

compare_opts = {
    "biggest_bottleneck": "Biggest Bottleneck",
    "modeling_pain_points": "Modeling Pain Points",
    "orchestration": "Orchestration",
    "ai_adoption": "AI Adoption",
    "storage_environment": "Storage Environment"
}

init_multiselect_state("solo_compare", "All dimensions")

with st.container(border=True):
    st.markdown("#### :primary[:material/compare:] Solo vs Team Comparison")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    compare_dimension = st.selectbox(
        "Compare on:",
        options=list(compare_opts.keys()),
        format_func=lambda x: compare_opts[x],
        key="solo_compare_dim"
    )
    
    dim_value_opts = get_options_with_counts(df, compare_dimension)
    all_label = f"All {compare_opts[compare_dimension].lower()}"
    
    init_multiselect_state(f"solo_filter_{compare_dimension}", all_label)
    
    st.multiselect(
        f"Filter {compare_opts[compare_dimension]}:",
        options=[all_label] + list(dim_value_opts.keys()),
        key=f"solo_filter_{compare_dimension}"
    )
    selected_values = get_multiselect_values(f"solo_filter_{compare_dimension}", all_label, dim_value_opts)
    
    if selected_values:
        filtered_solo = solo_df[solo_df[compare_dimension].isin(selected_values)]
        filtered_team = team_df[team_df[compare_dimension].isin(selected_values)]
    else:
        filtered_solo = solo_df
        filtered_team = team_df
    
    solo_counts = get_value_counts_pct(filtered_solo, compare_dimension, top_n=8)
    solo_counts['group'] = 'Solo (<50)'
    team_counts = get_value_counts_pct(filtered_team, compare_dimension, top_n=8)
    team_counts['group'] = 'Larger Teams'
    
    combined = pd.concat([solo_counts, team_counts])
    combined.columns = ['category', 'count', 'percentage', 'group']
    
    solo_data = combined[combined['group'] == 'Solo (<50)']
    team_data = combined[combined['group'] == 'Larger Teams']
    solo_top = solo_data.iloc[0]['category'] if len(solo_data) > 0 else "N/A"
    solo_top_pct = solo_data.iloc[0]['percentage'] if len(solo_data) > 0 else 0
    team_top = team_data.iloc[0]['category'] if len(team_data) > 0 else "N/A"
    team_top_pct = team_data.iloc[0]['percentage'] if len(team_data) > 0 else 0
    
    merged = solo_data[['category', 'percentage']].merge(
        team_data[['category', 'percentage']], 
        on='category', 
        suffixes=('_solo', '_team'),
        how='outer'
    ).fillna(0)
    merged['diff'] = merged['percentage_solo'] - merged['percentage_team']
    
    biggest_gap_row = merged.loc[merged['diff'].abs().idxmax()] if len(merged) > 0 else None
    most_similar_row = merged.loc[merged['diff'].abs().idxmin()] if len(merged) > 0 else None
    
    compare_colors = get_compare_colors()
    chart = alt.Chart(combined).mark_bar().encode(
        y=alt.Y('category:N', title=None, sort=alt.EncodingSortField(field='percentage', order='descending')),
        x=alt.X('percentage:Q', title='Percentage'),
        color=alt.Color('group:N', scale=alt.Scale(domain=['Solo (<50)', 'Larger Teams'], range=compare_colors), legend=alt.Legend(orient='bottom', title=None)),
        xOffset='group:N',
        tooltip=['category:N', 'group:N', alt.Tooltip('percentage:Q', format='.1f')]
    ).properties(height=400)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        st.caption(f"**:primary[Solo]** top: **{solo_top}** ({solo_top_pct:.0f}%)")
        st.caption(f"**:primary[Teams]** top: **{team_top}** ({team_top_pct:.0f}%)")
        
        if biggest_gap_row is not None:
            gap_cat = biggest_gap_row['category']
            gap_val = biggest_gap_row['diff']
            if gap_val > 0:
                st.caption(f":primary[:material/trending_up:] **Biggest difference:** Solo is {abs(gap_val):.0f}% higher on *{gap_cat}*")
            else:
                st.caption(f":primary[:material/trending_up:] **Biggest difference:** Teams are {abs(gap_val):.0f}% higher on *{gap_cat}*")
        
        if most_similar_row is not None:
            sim_cat = most_similar_row['category']
            sim_diff = abs(most_similar_row['diff'])
            st.caption(f":primary[:material/handshake:] **Most similar:** *{sim_cat}* (only {sim_diff:.0f}% apart)")

if n_solo > 0:
    with st.container(border=True):
        st.markdown("#### :primary[:material/lightbulb:] Solo vs Team Profile Comparison")
        
        def shorten_label(label, max_words_per_line=2):
            label = str(label).replace('Using AI for ', '').replace('AI ', '').replace('tactical', 'Tactical')
            words = label.split()
            if len(words) <= max_words_per_line:
                return label
            lines = []
            for i in range(0, len(words), max_words_per_line):
                lines.append(' '.join(words[i:i + max_words_per_line]))
            return '<br>'.join(lines)
        
        def create_radar_chart(solo_data, team_data, column, title):
            solo_pct = solo_data[column].value_counts(normalize=True).head(6) * 100
            team_pct = team_data[column].value_counts(normalize=True).head(6) * 100
            
            categories = [shorten_label(c) for c in solo_pct.index.tolist()]
            solo_values = solo_pct.values.tolist()
            team_values = [team_pct.get(cat, 0) for cat in solo_pct.index]
            
            radar_colors = get_compare_colors()
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=solo_values + [solo_values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name='Solo',
                opacity=0.6,
                line=dict(color=radar_colors[0])
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=team_values + [team_values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name='Larger Teams',
                opacity=0.6,
                line=dict(color=radar_colors[1])
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, max(max(solo_values), max(team_values)) * 1.1], gridcolor='#333333', tickfont=dict(color='#888888')),
                    angularaxis=dict(gridcolor='#333333', tickfont=dict(color='#cccccc', size=10)),
                    bgcolor='#0d1117'
                ),
                height=400,
                margin=dict(t=40, b=100, l=80, r=80),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="top", y=-0.35, xanchor="center", x=0.5, font=dict(color='#cccccc')),
                title=dict(text=title, font=dict(color='#cccccc', size=14))
            )
            return fig, solo_pct, team_pct
        
        ai_fig, ai_solo_pct, ai_team_pct = create_radar_chart(solo_df, team_df, 'ai_adoption', '')
        arch_fig, arch_solo_pct, arch_team_pct = create_radar_chart(solo_df, team_df, 'architecture_trend', '')
        
        ai_solo_top = ai_solo_pct.idxmax()
        ai_team_top = ai_team_pct.idxmax()
        ai_solo_top_clean = ai_solo_top.replace('Using AI for ', '').replace('AI ', '')
        ai_team_top_clean = ai_team_top.replace('Using AI for ', '').replace('AI ', '')
        biggest_gap_ai = (ai_solo_pct - ai_team_pct.reindex(ai_solo_pct.index, fill_value=0)).abs().idxmax()
        gap_val = ai_solo_pct.get(biggest_gap_ai, 0) - ai_team_pct.get(biggest_gap_ai, 0)
        biggest_gap_ai_clean = biggest_gap_ai.replace('Using AI for ', '').replace('AI ', '')
        
        arch_solo_top = arch_solo_pct.idxmax()
        arch_team_top = arch_team_pct.idxmax()
        biggest_gap_arch = (arch_solo_pct - arch_team_pct.reindex(arch_solo_pct.index, fill_value=0)).abs().idxmax()
        gap_val_arch = arch_solo_pct.get(biggest_gap_arch, 0) - arch_team_pct.get(biggest_gap_arch, 0)
        
        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            st.markdown("##### :primary[:material/smart_toy:] AI Adoption")
            st.plotly_chart(ai_fig, use_container_width=True)
        
        with col2:
            st.markdown("##### :primary[:material/architecture:] Architecture Trend")
            st.plotly_chart(arch_fig, use_container_width=True)
        
        with col3:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            st.markdown("**AI Adoption**")
            if ai_solo_top == ai_team_top:
                st.caption(f"Both Solo and Teams primarily use AI for **{ai_solo_top_clean}** ({ai_solo_pct.max():.0f}% vs {ai_team_pct.get(ai_solo_top, 0):.0f}%)")
            else:
                st.caption(f"Solo practitioners focus on **{ai_solo_top_clean}** ({ai_solo_pct.max():.0f}%), while larger teams prefer **{ai_team_top_clean}** ({ai_team_pct.max():.0f}%)")
            if gap_val > 0:
                st.caption(f"Biggest gap: Solo is **{abs(gap_val):.0f}% higher** on *{biggest_gap_ai_clean}*")
            else:
                st.caption(f"Biggest gap: Teams are **{abs(gap_val):.0f}% higher** on *{biggest_gap_ai_clean}*")
            
            st.markdown("**Architecture Trend**")
            if arch_solo_top == arch_team_top:
                st.caption(f"Both groups prefer **{arch_solo_top}** ({arch_solo_pct.max():.0f}% vs {arch_team_pct.get(arch_solo_top, 0):.0f}%)")
            else:
                st.caption(f"Solo practitioners lean toward **{arch_solo_top}** ({arch_solo_pct.max():.0f}%), while larger teams prefer **{arch_team_top}** ({arch_team_pct.max():.0f}%)")
            if gap_val_arch > 0:
                st.caption(f"Biggest gap: Solo is **{abs(gap_val_arch):.0f}% higher** on *{biggest_gap_arch}*")
            else:
                st.caption(f"Biggest gap: Teams are **{abs(gap_val_arch):.0f}% higher** on *{biggest_gap_arch}*")
    
    with st.container(border=True):
        col_header, col_widget = st.columns([3, 1])
        with col_header:
            st.markdown("#### :primary[:material/school:] What They Want to Learn")
        with col_widget:
            top_n_edu = st.number_input("Show top", min_value=3, max_value=15, value=8, key="top_n_edu")
        
        chart_height = max(250, top_n_edu * 35)
        
        solo_edu_pct = solo_df['education_topic'].value_counts(normalize=True).head(top_n_edu) * 100
        team_edu_pct = team_df['education_topic'].value_counts(normalize=True).head(top_n_edu) * 100
        
        solo_top = solo_edu_pct.idxmax() if len(solo_edu_pct) > 0 else "N/A"
        team_top = team_edu_pct.idxmax() if len(team_edu_pct) > 0 else "N/A"
        
        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            st.markdown("##### Solo Practitioners")
            solo_chart = create_bar_chart(solo_df, 'education_topic', height=chart_height, top_n=top_n_edu, varied_colors=True)
            st.altair_chart(solo_chart, use_container_width=True)
        with col2:
            st.markdown("##### Larger Teams")
            team_chart = create_bar_chart(team_df, 'education_topic', height=chart_height, top_n=top_n_edu, varied_colors=True)
            st.altair_chart(team_chart, use_container_width=True)
        with col3:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            st.caption(f"**:primary[Solo]** top interest: **{solo_top}** ({solo_edu_pct.max():.0f}%)")
            st.caption(f"**:primary[Teams]** top interest: **{team_top}** ({team_edu_pct.max():.0f}%)")
            st.caption(":primary[:material/compare_arrows:] (1) Data modeling, (2) Architecture patterns, (3) Streaming, (4) Career growth, and (5) Reliability engineering ranked roughly the same for both groups.")
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/format_quote:] Voices from Practitioners")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Solo Practitioners")
            solo_wishes = solo_df[solo_df['industry_wish'].notna() & (solo_df['industry_wish'] != '')]
            if len(solo_wishes) > 0:
                all_solo_text = ' '.join(solo_wishes['industry_wish'].str.lower())
                solo_themes = []
                if 'time' in all_solo_text or 'resource' in all_solo_text: solo_themes.append("Resource constraints")
                if 'tool' in all_solo_text or 'simple' in all_solo_text: solo_themes.append("Simpler tooling")
                if 'learn' in all_solo_text or 'skill' in all_solo_text: solo_themes.append("Skill development")
                if 'automat' in all_solo_text or 'ai' in all_solo_text: solo_themes.append("Automation/AI")
                if solo_themes:
                    st.caption(f":primary[:material/summarize:] Common themes: {', '.join(solo_themes)}")
                
                solo_sample = solo_wishes.sample(min(3, len(solo_wishes)))
                for _, row in solo_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining_solo = solo_wishes[~solo_wishes.index.isin(solo_sample.index)]
                if len(remaining_solo) > 0:
                    with st.expander(f"Show more ({len(remaining_solo)} more quotes)"):
                        for _, row in remaining_solo.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
        
        with col2:
            st.markdown("##### Larger Teams")
            team_wishes = team_df[team_df['industry_wish'].notna() & (team_df['industry_wish'] != '')]
            if len(team_wishes) > 0:
                all_team_text = ' '.join(team_wishes['industry_wish'].str.lower())
                team_themes = []
                if 'time' in all_team_text or 'resource' in all_team_text: team_themes.append("Resource constraints")
                if 'tool' in all_team_text or 'simple' in all_team_text: team_themes.append("Simpler tooling")
                if 'learn' in all_team_text or 'skill' in all_team_text: team_themes.append("Skill development")
                if 'automat' in all_team_text or 'ai' in all_team_text: team_themes.append("Automation/AI")
                if team_themes:
                    st.caption(f":primary[:material/summarize:] Common themes: {', '.join(team_themes)}")
                
                team_sample = team_wishes.sample(min(3, len(team_wishes)))
                for _, row in team_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining_team = team_wishes[~team_wishes.index.isin(team_sample.index)]
                if len(remaining_team) > 0:
                    with st.expander(f"Show more ({len(remaining_team)} more quotes)"):
                        for _, row in remaining_team.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
