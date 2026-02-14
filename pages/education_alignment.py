import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from data_utils import get_filtered_df, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import get_compare_colors, get_plotly_scale, get_categorical_colors

st.markdown("# :primary[:material/school:] Education-to-Gap Alignment")
st.markdown("Compare what practitioners want to learn vs actual skill gaps")

df = get_filtered_df()

education_counts = df['education_topic'].value_counts()
pain_points = []
for pains in df['modeling_pain_points'].dropna():
    for p in str(pains).split(', '):
        if p.strip() and p.strip() != 'None / modeling is going well':
            pain_points.append(p.strip())

unique_pains = list(set(pain_points))

with st.container(border=True):
    st.markdown("#### :primary[:material/grid_view:] Desire vs Reality Matrix")
    st.markdown("This heatmap reveals where education desires intersect with real-world pain points. Brighter cells indicate stronger alignment—practitioners who want specific training are also experiencing related challenges. Use this to identify high-impact training opportunities.")
    
    top_edu = education_counts.head(8).index.tolist()
    top_pains = pd.Series(pain_points).value_counts().head(8).index.tolist()
    
    alignment_matrix = pd.DataFrame(0, index=top_edu, columns=[p[:25] for p in top_pains])
    
    for _, row in df.iterrows():
        edu = row['education_topic']
        pains = row['modeling_pain_points']
        if pd.notna(edu) and edu in top_edu and pd.notna(pains):
            for p in str(pains).split(', '):
                p = p.strip()
                if p in top_pains:
                    alignment_matrix.loc[edu, p[:25]] += 1
    
    max_val = alignment_matrix.max().max()
    max_idx = alignment_matrix.stack().idxmax()
    
    def wrap_label(text, max_width=20):
        words = text.split()
        lines = []
        current_line = []
        current_len = 0
        for word in words:
            if current_len + len(word) + (1 if current_line else 0) <= max_width:
                current_line.append(word)
                current_len += len(word) + (1 if len(current_line) > 1 else 0)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_len = len(word)
        if current_line:
            lines.append(' '.join(current_line))
        return '<br>'.join(lines)
    
    wrapped_edu = [wrap_label(e) for e in top_edu]
    wrapped_pains = [wrap_label(p[:25]) for p in top_pains]
    
    alignment_matrix.index = wrapped_edu
    alignment_matrix.columns = wrapped_pains
    
    fig = px.imshow(
        alignment_matrix,
        color_continuous_scale=get_plotly_scale(),
        labels=dict(x="Pain Point", y="Education Desired", color="Count"),
        aspect='auto',
        text_auto=True
    )
    fig.update_traces(xgap=1, ygap=1)
    fig.update_layout(height=450, margin=dict(t=10))
    fig.update_xaxes(tickangle=90)
    fig.update_yaxes(tickangle=0)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Shows count of respondents wanting each education topic AND experiencing each pain point")
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        top_edu_topic = education_counts.idxmax()
        top_edu_pct = education_counts.max() / len(df) * 100
        top_pain = pd.Series(pain_points).value_counts().idxmax()
        top_pain_count = pd.Series(pain_points).value_counts().max()
        st.caption(f"The strongest alignment occurs between :primary[{max_idx[0][:20]}] and :primary[{max_idx[1][:20]}], with **{max_val}** respondents seeking this education while experiencing this pain point.")
        st.caption(f":primary[{top_edu_topic[:25]}] is the most desired topic at **{top_edu_pct:.0f}%**, while :primary[{top_pain[:25]}] affects **{top_pain_count}** practitioners—revealing where training investments would have the greatest impact.")
        alignment_density = (alignment_matrix > 0).sum().sum() / alignment_matrix.size * 100
        st.caption(f"The matrix shows **{alignment_density:.0f}%** cell coverage, indicating {'broad' if alignment_density > 50 else 'focused'} overlap between education desires and pain points—{'suggesting systemic skill gaps' if alignment_density > 50 else 'highlighting specific training opportunities'}.")

role_opts = get_options_with_counts(df, 'role')

init_multiselect_state("edu_role", "All roles")

with st.container(border=True):
    st.markdown("#### :primary[:material/person:] Education Priorities by Role")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    st.multiselect(
        "Select Role:",
        options=["All roles"] + list(role_opts.keys()),
        key="edu_role"
    )
    selected_roles = get_multiselect_values("edu_role", "All roles", role_opts)
    
    if selected_roles:
        role_df = df[df['role'].isin(selected_roles)]
        role_label = ", ".join([r[:15] for r in selected_roles[:2]]) + ("..." if len(selected_roles) > 2 else "")
    else:
        role_df = df
        role_label = "All Roles"
    
    role_edu_pct = role_df['education_topic'].value_counts(normalize=True).head(6) * 100
    
    role_pains_list = []
    for pains in role_df['modeling_pain_points'].dropna():
        for p in str(pains).split(', '):
            if p.strip() and 'None' not in p:
                role_pains_list.append(p.strip())
    role_pain_pct = pd.Series(role_pains_list).value_counts(normalize=True).head(6) * 100 if role_pains_list else pd.Series()
    
    col1, col2, col3 = st.columns([3, 3, 2])
    
    with col1:
        st.markdown(f"##### What {role_label} Want to Learn")
        if len(role_df) > 0:
            role_edu = role_df['education_topic'].value_counts().head(6).reset_index()
            role_edu.columns = ['topic', 'count']
            role_edu['percentage'] = (role_edu['count'] / len(role_df) * 100).round(1)
            
            edu_colors = get_categorical_colors()[:len(role_edu)]
            chart = alt.Chart(role_edu).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('topic:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
                x=alt.X('percentage:Q', title='%'),
                color=alt.Color('topic:N', scale=alt.Scale(domain=role_edu['topic'].tolist(), range=edu_colors), legend=None),
                tooltip=['topic:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f')]
            ).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
    
    with col2:
        st.markdown(f"##### What {role_label} Struggle With")
        if len(role_df) > 0 and role_pains_list:
            pain_counts = pd.Series(role_pains_list).value_counts().head(6).reset_index()
            pain_counts.columns = ['pain', 'count']
            pain_counts['percentage'] = (pain_counts['count'] / len(role_df) * 100).round(1)
            
            pain_colors = get_categorical_colors()[:len(pain_counts)]
            chart = alt.Chart(pain_counts).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('pain:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
                x=alt.X('percentage:Q', title='%'),
                color=alt.Color('pain:N', scale=alt.Scale(domain=pain_counts['pain'].tolist(), range=pain_colors), legend=None),
                tooltip=['pain:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f')]
            ).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No pain points reported")
    
    with col3:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        top_edu_role = role_edu_pct.idxmax() if len(role_edu_pct) > 0 else "N/A"
        top_edu_role_pct = role_edu_pct.max() if len(role_edu_pct) > 0 else 0
        top_pain_role = role_pain_pct.idxmax() if len(role_pain_pct) > 0 else "N/A"
        top_pain_role_pct = role_pain_pct.max() if len(role_pain_pct) > 0 else 0
        st.caption(f"For {role_label}, :primary[{top_edu_role[:20]}] tops the education wishlist at **{top_edu_role_pct:.0f}%**, suggesting this is where training resources should focus.")
        st.caption(f"Meanwhile, :primary[{top_pain_role[:20]}] emerges as the dominant struggle at **{top_pain_role_pct:.0f}%**—a clear opportunity for targeted curriculum development.")

with st.container(border=True):
    st.markdown("#### :primary[:material/scatter_plot:] Education Interest vs Pain Point Frequency")
    st.markdown("This visualization maps the relationship between what practitioners *want* to learn and where they *struggle* most. Topics in the upper-right quadrant represent critical gaps—high demand meets high pain—signaling where training investment yields the greatest ROI.")
    
    edu_summary = []
    for topic in df['education_topic'].dropna().unique():
        topic_df = df[df['education_topic'] == topic]
        if len(topic_df) >= 10:
            edu_pct = len(topic_df) / len(df) * 100
            pain_rate = topic_df['modeling_pain_points'].apply(
                lambda x: 'None' not in str(x) if pd.notna(x) else False
            ).mean() * 100
            
            edu_summary.append({
                'topic': topic[:25] + "..." if len(topic) > 25 else topic,
                'full_topic': topic,
                'education_interest': edu_pct,
                'pain_rate': pain_rate,
                'count': len(topic_df)
            })
    
    if edu_summary:
        scatter_df = pd.DataFrame(edu_summary)
        scatter_df = scatter_df.sort_values('education_interest', ascending=False).reset_index(drop=True)
        
        top_right = scatter_df.loc[(scatter_df['education_interest'] + scatter_df['pain_rate']).idxmax()]
        
        scatter_colors = get_categorical_colors()[:len(scatter_df)]
        chart = alt.Chart(scatter_df).mark_circle(size=100, stroke='black', strokeWidth=1).encode(
            x=alt.X('pain_rate:Q', title='% With Pain Points'),
            y=alt.Y('education_interest:Q', title='% Seeking This Education'),
            size=alt.Size('count:Q', scale=alt.Scale(range=[50, 500]), legend=None),
            color=alt.Color('topic:N', scale=alt.Scale(domain=scatter_df['topic'].tolist(), range=scatter_colors), legend=alt.Legend(orient='bottom', title=None, columns=3)),
            tooltip=['topic:N', alt.Tooltip('education_interest:Q', format='.1f'),
                     alt.Tooltip('pain_rate:Q', format='.1f'), 'count:Q']
        ).properties(height=400)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.altair_chart(chart, use_container_width=True)
            st.caption("Size = number of respondents. Higher/right = more interest and more pain.")
        with col2:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            avg_pain = scatter_df['pain_rate'].mean()
            avg_interest = scatter_df['education_interest'].mean()
            low_pain_high_interest = scatter_df[(scatter_df['pain_rate'] < avg_pain) & (scatter_df['education_interest'] > avg_interest)]
            st.caption(f":primary[{top_right['topic']}] sits in the high-demand, high-pain quadrant with **{top_right['education_interest']:.0f}%** interest and **{top_right['pain_rate']:.0f}%** pain rate—making it the prime candidate for immediate training investment.")
            st.caption(f"The average pain rate across all topics is **{avg_pain:.0f}%**, providing a benchmark for prioritizing education initiatives.")
            if len(low_pain_high_interest) > 0:
                opportunity = low_pain_high_interest.iloc[0]
                st.caption(f"Topics like :primary[{opportunity['topic']}] show high interest (**{opportunity['education_interest']:.0f}%**) but lower pain (**{opportunity['pain_rate']:.0f}%**)—these represent proactive learning opportunities before problems emerge.")

with st.container(border=True):
    st.markdown("#### :primary[:material/lightbulb:] Alignment Analysis")
    st.markdown("A deeper look at how education interests align with actual challenges. Well-aligned topics indicate where training investments will directly address practitioner needs, while underserved gaps reveal areas where current education offerings fall short.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("##### :primary[:material/check_circle:] Well-Aligned Topics")
            st.caption("These education topics show the strongest correlation between learning interest and real-world challenges. Practitioners seeking these skills are actively experiencing related pain points—indicating that training in these areas will deliver immediate, practical value.")
            
            edu_pain_corr = []
            for edu_topic in top_edu:
                edu_df = df[df['education_topic'] == edu_topic]
                if len(edu_df) > 10:
                    has_any_pain = edu_df['modeling_pain_points'].apply(
                        lambda x: 'None' not in str(x) if pd.notna(x) else False
                    ).mean() * 100
                    edu_pain_corr.append({'topic': edu_topic, 'pain_rate': has_any_pain})
            
            if edu_pain_corr:
                aligned = sorted(edu_pain_corr, key=lambda x: x['pain_rate'], reverse=True)[:4]
                for item in aligned:
                    st.markdown(f"- **{item['topic'][:30]}**: {item['pain_rate']:.0f}% have pain points")
    
    with col2:
        with st.container(border=True):
            st.markdown("##### :primary[:material/warning:] Underserved Gaps")
            st.caption("These pain points affect significant numbers of practitioners but aren't matched by corresponding education interest. This disconnect suggests either a lack of awareness about available training or a perception that these challenges cannot be solved through education alone.")
            
            pain_edu_map = {}
            for pain in top_pains:
                pain_df = df[df['modeling_pain_points'].str.contains(pain, na=False)]
                if len(pain_df) > 10:
                    edu_interest = pain_df['education_topic'].value_counts()
                    pain_edu_map[pain] = len(pain_df)
            
            if pain_edu_map:
                underserved = sorted(pain_edu_map.items(), key=lambda x: x[1], reverse=True)[:4]
                for pain, count in underserved:
                    st.markdown(f"- **{pain[:30]}**: {count} affected")
