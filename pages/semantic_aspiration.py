import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df
from chart_utils import create_donut_chart, get_compare_colors, get_categorical_colors

st.markdown("# :primary[:material/hub:] Semantic Layer Aspiration Gap")
st.markdown("Explore the gap between semantic layer goals and actual adoption rates")

df = get_filtered_df()

semantic_interest_df = df[df['education_topic'].str.contains('Semantic|ontolog', case=False, na=False)]
n_semantic_interest = len(semantic_interest_df)

semantic_users_df = df[df['modeling_approach'].str.contains('Canonical|semantic', case=False, na=False)]
n_semantic_users = len(semantic_users_df)

non_users_df = df[~df['modeling_approach'].str.contains('Canonical|semantic', case=False, na=False)]

pct_interest = n_semantic_interest / len(df) * 100 if len(df) > 0 else 0
pct_users = n_semantic_users / len(df) * 100 if len(df) > 0 else 0

overview_col1, overview_col2 = st.columns(2)

with overview_col1:
    with st.container(border=True):
        st.markdown("#### :primary[:material/school:] Semantic Aspirants Overview")
        
        if n_semantic_interest > 0:
            top_industry = semantic_interest_df['industry'].value_counts().idxmax()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Want Semantics Training", f"{n_semantic_interest:,}")
            col2.metric("% of Survey", f"{pct_interest:.1f}%")
            col3.metric("Top Industry", top_industry)
            
            top_role = semantic_interest_df['role'].value_counts().idxmax()
            st.metric("Top Role", top_role)
            
            interest_ff = semantic_interest_df['has_firefighting'].sum() / n_semantic_interest * 100
            users_ff = semantic_users_df['has_firefighting'].sum() / n_semantic_users * 100 if n_semantic_users > 0 else 0
            interest_growth = (semantic_interest_df['team_growth_2026'] == 'Grow').sum() / n_semantic_interest * 100
            users_growth = (semantic_users_df['team_growth_2026'] == 'Grow').sum() / n_semantic_users * 100 if n_semantic_users > 0 else 0
            interest_lead = semantic_interest_df['has_leadership_gap'].sum() / n_semantic_interest * 100
            users_lead = semantic_users_df['has_leadership_gap'].sum() / n_semantic_users * 100 if n_semantic_users > 0 else 0
            
            col4, col5, col6 = st.columns(3)
            col4.metric("Firefighting", f"{interest_ff:.0f}%", delta=f"{interest_ff - users_ff:+.1f}%", delta_color="inverse")
            col5.metric("Expect Growth", f"{interest_growth:.0f}%", delta=f"{interest_growth - users_growth:+.1f}%")
            col6.metric("Leadership Gap", f"{interest_lead:.0f}%", delta=f"{interest_lead - users_lead:+.1f}%", delta_color="inverse")

with overview_col2:
    with st.container(border=True):
        st.markdown("#### :primary[:material/check_circle:] Semantic Users Overview")
        
        if n_semantic_users > 0:
            users_top_industry = semantic_users_df['industry'].value_counts().idxmax()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Use Semantic Models", f"{n_semantic_users:,}")
            col2.metric("% of Survey", f"{pct_users:.1f}%")
            col3.metric("Top Industry", users_top_industry)
            
            users_top_role = semantic_users_df['role'].value_counts().idxmax()
            st.metric("Top Role", users_top_role)
            
            users_ff = semantic_users_df['has_firefighting'].sum() / n_semantic_users * 100
            interest_ff = semantic_interest_df['has_firefighting'].sum() / n_semantic_interest * 100 if n_semantic_interest > 0 else 0
            users_growth = (semantic_users_df['team_growth_2026'] == 'Grow').sum() / n_semantic_users * 100
            interest_growth = (semantic_interest_df['team_growth_2026'] == 'Grow').sum() / n_semantic_interest * 100 if n_semantic_interest > 0 else 0
            users_lead = semantic_users_df['has_leadership_gap'].sum() / n_semantic_users * 100
            interest_lead = semantic_interest_df['has_leadership_gap'].sum() / n_semantic_interest * 100 if n_semantic_interest > 0 else 0
            
            col4, col5, col6 = st.columns(3)
            col4.metric("Firefighting", f"{users_ff:.0f}%", delta=f"{users_ff - interest_ff:+.1f}%", delta_color="inverse")
            col5.metric("Expect Growth", f"{users_growth:.0f}%", delta=f"{users_growth - interest_growth:+.1f}%")
            col6.metric("Leadership Gap", f"{users_lead:.0f}%", delta=f"{users_lead - interest_lead:+.1f}%", delta_color="inverse")

with st.container(border=True):
    st.markdown("#### :primary[:material/compare_arrows:] The Aspiration-to-Adoption Gap")
    
    gap_ratio = pct_interest / pct_users if pct_users > 0 else 0
    
    col1, col2 = st.columns([3, 1])
    with col1:
        gap_data = pd.DataFrame({
            'category': ['Want Semantics Training', 'Use Semantic Models'],
            'percentage': [pct_interest, pct_users],
            'count': [n_semantic_interest, n_semantic_users]
        })
        
        chart = alt.Chart(gap_data).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('category:N', sort=None, title=None, axis=alt.Axis(labelLimit=0)),
            x=alt.X('percentage:Q', title='% of Survey'),
            color=alt.Color('category:N', scale=alt.Scale(domain=['Want Semantics Training', 'Use Semantic Models'], range=get_compare_colors()), legend=None),
            tooltip=['category:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f')]
        ).properties(height=150)
        st.altair_chart(chart, use_container_width=True)
    
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        st.caption(f"A striking **{gap_ratio:.1f}x** more practitioners want to learn semantics than actually use it, revealing a significant aspiration-to-adoption gap.")
        st.caption(f"The **{pct_interest - pct_users:.1f}%** gap suggests substantial barriers to semantic model adoption despite strong interest.")

with st.container(border=True):
    st.markdown("#### :primary[:material/person:] Who Wants Semantics Training?")
    
    breakdown_dim = st.selectbox(
        "Break down by:",
        options=["role", "industry", "org_size", "modeling_approach"],
        format_func=lambda x: x.replace('_', ' ').title(),
        key="sem_breakdown"
    )
    
    if n_semantic_interest > 0:
        top_n_training = st.slider("Top N", min_value=3, max_value=10, value=8, key="training_top_n")
        interest_counts = semantic_interest_df[breakdown_dim].value_counts().head(top_n_training).reset_index()
        interest_counts.columns = [breakdown_dim, 'count']
        interest_counts['percentage'] = (interest_counts['count'] / n_semantic_interest * 100).round(1)
        
        top_item = interest_counts.iloc[0][breakdown_dim] if len(interest_counts) > 0 else "N/A"
        top_pct = interest_counts.iloc[0]['percentage'] if len(interest_counts) > 0 else 0
        
        training_colors = get_categorical_colors()[:len(interest_counts)]
        chart = alt.Chart(interest_counts).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y(f'{breakdown_dim}:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
            x=alt.X('percentage:Q', title='% of Those Interested'),
            color=alt.Color(f'{breakdown_dim}:N', scale=alt.Scale(domain=interest_counts[breakdown_dim].tolist(), range=training_colors), legend=None),
            tooltip=[f'{breakdown_dim}:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f')]
        ).properties(height=300)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.altair_chart(chart, use_container_width=True)
        with col2:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            dim_label = breakdown_dim.replace('_', ' ')
            st.caption(f":primary[{top_item[:20]}] leads semantic interest at **{top_pct:.0f}%**, making this {dim_label} a prime target for semantic training initiatives.")
            if len(interest_counts) > 1:
                second = interest_counts.iloc[1][breakdown_dim]
                second_pct = interest_counts.iloc[1]['percentage']
                st.caption(f":primary[{second[:20]}] follows at **{second_pct:.0f}%**, suggesting a secondary opportunity for curriculum development.")
    else:
        st.info("No respondents interested in semantics training in current filter")

with st.container(border=True):
    st.markdown("#### :primary[:material/lightbulb:] What's Blocking Semantic Adoption?")
    
    interest_model = semantic_interest_df['modeling_approach'].value_counts(normalize=True).head(5) * 100 if n_semantic_interest > 0 else pd.Series()
    
    interest_pains = []
    if n_semantic_interest > 0:
        for pains in semantic_interest_df['modeling_pain_points'].dropna():
            for p in str(pains).split(', '):
                if p.strip() and 'None' not in p:
                    interest_pains.append(p.strip())
    interest_pain_pct = pd.Series(interest_pains).value_counts(normalize=True).head(5) * 100 if interest_pains else pd.Series()
    
    col1, col2, col3 = st.columns([3, 3, 2])
    
    with col1:
        st.markdown("##### Current Modeling Approaches")
        if n_semantic_interest > 0:
            top_n_modeling = st.slider("Top N", min_value=3, max_value=10, value=5, key="modeling_top_n")
            modeling_counts = semantic_interest_df['modeling_approach'].value_counts().head(top_n_modeling).reset_index()
            modeling_counts.columns = ['approach', 'count']
            colors = get_categorical_colors()[:top_n_modeling]
            modeling_chart = alt.Chart(modeling_counts).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('approach:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
                x=alt.X('count:Q', title='Count'),
                color=alt.Color('approach:N', scale=alt.Scale(domain=modeling_counts['approach'].tolist(), range=colors), legend=None),
                tooltip=['approach:N', 'count:Q']
            ).properties(height=250)
            st.altair_chart(modeling_chart, use_container_width=True)
    
    with col2:
        st.markdown("##### Their Pain Points")
        if n_semantic_interest > 0 and interest_pains:
            top_n_pains = st.slider("Top N", min_value=3, max_value=5, value=5, key="pains_top_n")
            pain_counts = pd.Series(interest_pains).value_counts().head(top_n_pains).reset_index()
            pain_counts.columns = ['pain', 'count']
            pain_colors = get_categorical_colors()[:top_n_pains]
            
            chart = alt.Chart(pain_counts).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('pain:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
                x=alt.X('count:Q', title='Count'),
                color=alt.Color('pain:N', scale=alt.Scale(domain=pain_counts['pain'].tolist(), range=pain_colors), legend=None),
                tooltip=['pain:N', 'count:Q']
            ).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
    
    with col3:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        top_model = interest_model.idxmax() if len(interest_model) > 0 else "N/A"
        top_model_pct = interest_model.max() if len(interest_model) > 0 else 0
        top_pain = interest_pain_pct.idxmax() if len(interest_pain_pct) > 0 else "N/A"
        top_pain_pct = interest_pain_pct.max() if len(interest_pain_pct) > 0 else 0
        st.caption(f"Most semantic aspirants currently use :primary[{top_model[:20]}] at **{top_model_pct:.0f}%**—their jumping-off point for semantic adoption.")
        st.caption(f":primary[{top_pain[:25]}] emerges as the top pain at **{top_pain_pct:.0f}%**, suggesting where semantic models could provide the most value.")

with st.container(border=True):
    st.markdown("#### :primary[:material/compare:] Semantic Aspirants vs Semantic Users")
    
    if n_semantic_interest > 0 and n_semantic_users > 0:
        aspirant_btn = semantic_interest_df['biggest_bottleneck'].value_counts(normalize=True).head(5) * 100
        user_btn = semantic_users_df['biggest_bottleneck'].value_counts(normalize=True).head(5) * 100
        
        aspirant_btn_df = aspirant_btn.reset_index()
        aspirant_btn_df.columns = ['bottleneck', 'percentage']
        aspirant_btn_df['group'] = 'Semantic Aspirants'
        
        user_btn_df = user_btn.reset_index()
        user_btn_df.columns = ['bottleneck', 'percentage']
        user_btn_df['group'] = 'Semantic Users'
        
        combined = pd.concat([aspirant_btn_df, user_btn_df])
        
        chart = alt.Chart(combined).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('bottleneck:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
            x=alt.X('percentage:Q', title='Percentage'),
            color=alt.Color('group:N', scale=alt.Scale(domain=['Semantic Aspirants', 'Semantic Users'], range=get_compare_colors()), legend=alt.Legend(orient='bottom', title=None)),
            xOffset='group:N',
            tooltip=['bottleneck:N', 'group:N', alt.Tooltip('percentage:Q', format='.1f')]
        ).properties(height=300)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.altair_chart(chart, use_container_width=True)
        with col2:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            aspirant_top = aspirant_btn.idxmax() if len(aspirant_btn) > 0 else "N/A"
            aspirant_top_pct = aspirant_btn.max() if len(aspirant_btn) > 0 else 0
            user_top = user_btn.idxmax() if len(user_btn) > 0 else "N/A"
            user_top_pct = user_btn.max() if len(user_btn) > 0 else 0
            st.caption(f"Semantic Aspirants cite :primary[{aspirant_top}] as their top bottleneck at **{aspirant_top_pct:.0f}%**.")
            st.caption(f"Semantic Users face :primary[{user_top}] most at **{user_top_pct:.0f}%**—revealing how pain points shift post-adoption.")

with st.container(border=True):
    st.markdown("#### :primary[:material/format_quote:] Voices from the Field")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Semantic Aspirants")
        aspirant_wishes = semantic_interest_df[
            semantic_interest_df['industry_wish'].notna() & 
            (semantic_interest_df['industry_wish'] != '')
        ]
        if len(aspirant_wishes) > 0:
            asp_sample = aspirant_wishes.sample(min(3, len(aspirant_wishes)))
            for _, row in asp_sample.iterrows():
                with st.container(border=True):
                    st.markdown(f"*\"{row['industry_wish']}\"*")
                    st.caption(f"— {row['role']}, {row['industry']}")
            
            remaining = aspirant_wishes[~aspirant_wishes.index.isin(asp_sample.index)]
            if len(remaining) > 0:
                with st.expander(f"Show more ({len(remaining)} more quotes)"):
                    for _, row in remaining.iterrows():
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                        st.divider()
        else:
            st.info("No quotes available")
    
    with col2:
        st.markdown("##### Semantic Users")
        user_wishes = semantic_users_df[
            semantic_users_df['industry_wish'].notna() & 
            (semantic_users_df['industry_wish'] != '')
        ]
        if len(user_wishes) > 0:
            user_sample = user_wishes.sample(min(3, len(user_wishes)))
            for _, row in user_sample.iterrows():
                with st.container(border=True):
                    st.markdown(f"*\"{row['industry_wish']}\"*")
                    st.caption(f"— {row['role']}, {row['industry']}")
            
            remaining = user_wishes[~user_wishes.index.isin(user_sample.index)]
            if len(remaining) > 0:
                with st.expander(f"Show more ({len(remaining)} more quotes)"):
                    for _, row in remaining.iterrows():
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                        st.divider()
        else:
            st.info("No quotes available")
