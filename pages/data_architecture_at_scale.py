import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from data_utils import get_filtered_df, ORG_SIZE_ORDER
from chart_utils import get_primary_color

st.markdown("# :primary[:material/trending_up:] Data Architecture at Scale")
st.markdown("Explore how data architecture patterns evolve with organizational scale")

df = get_filtered_df()

df_arch = df.copy()
df_arch['org_size_cat'] = pd.Categorical(df_arch['org_size'], categories=ORG_SIZE_ORDER, ordered=True)
df_arch = df_arch.dropna(subset=['org_size', 'architecture_trend'])

def normalize_architecture(arch):
    if pd.isna(arch):
        return arch
    arch_lower = arch.lower()
    if arch_lower.startswith('centralized warehouse'):
        return 'Centralized warehouse'
    if 'lakehouse' in arch_lower:
        return 'Lakehouse'
    if 'data mesh' in arch_lower or 'federated' in arch_lower:
        return 'Data mesh / Federated'
    if 'data lake' in arch_lower:
        return 'Data Lake + Power BI architecture'
    return arch

df_arch['architecture_trend'] = df_arch['architecture_trend'].apply(normalize_architecture)

with st.container(border=True):
    st.markdown("#### :primary[:material/stacked_bar_chart:] Architecture by Org Size")
    
    arch_by_size = df_arch.groupby(['org_size_cat', 'architecture_trend']).size().reset_index(name='count')
    totals = df_arch.groupby('org_size_cat').size().reset_index(name='total')
    arch_by_size = arch_by_size.merge(totals, on='org_size_cat')
    arch_by_size['percentage'] = (arch_by_size['count'] / arch_by_size['total'] * 100).round(1)
    
    top_arch_by_size = arch_by_size.loc[arch_by_size.groupby('org_size_cat')['percentage'].idxmax()]
    
    chart = alt.Chart(arch_by_size).mark_bar().encode(
        x=alt.X('org_size_cat:N', title='Organization Size', sort=ORG_SIZE_ORDER),
        y=alt.Y('percentage:Q', title='Percentage', stack='normalize'),
        color=alt.Color('architecture_trend:N', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(title='Architecture', orient='bottom', columns=3)),
        tooltip=['org_size_cat:N', 'architecture_trend:N', alt.Tooltip('percentage:Q', format='.1f')]
    ).properties(height=600)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        if len(top_arch_by_size) >= 2:
            smallest_org = top_arch_by_size[top_arch_by_size['org_size_cat'] == ORG_SIZE_ORDER[0]].iloc[0] if ORG_SIZE_ORDER[0] in top_arch_by_size['org_size_cat'].values else None
            largest_org = top_arch_by_size[top_arch_by_size['org_size_cat'] == ORG_SIZE_ORDER[-1]].iloc[0] if ORG_SIZE_ORDER[-1] in top_arch_by_size['org_size_cat'].values else None
            
            if smallest_org is not None:
                st.caption(f"**:primary[Small orgs:]** {smallest_org['architecture_trend']} ({smallest_org['percentage']:.0f}%) — Smaller teams tend to prefer simpler, centralized setups that reduce coordination overhead.")
            
            if largest_org is not None:
                st.caption(f"**:primary[Large orgs:]** {largest_org['architecture_trend']} ({largest_org['percentage']:.0f}%) — Larger enterprises often adopt distributed architectures to manage complexity across multiple teams.")
            
            unique_archs = top_arch_by_size['architecture_trend'].nunique()
            if unique_archs == 1:
                st.caption(f"**:primary[Pattern:]** Consistent architecture preference across all org sizes suggests industry-wide convergence on {top_arch_by_size['architecture_trend'].iloc[0]}.")
            else:
                st.caption(f"**:primary[Pattern:]** As organizations grow, their architecture preferences shift — suggesting that team size and complexity drive different architectural needs.")

with st.container(border=True):
    st.markdown("#### :primary[:material/timeline:] The Data Mesh Journey")
    
    mesh_by_size = df_arch[df_arch['architecture_trend'].str.contains('mesh|federated', case=False, na=False)]
    mesh_pct_by_size = mesh_by_size.groupby('org_size_cat').size() / df_arch.groupby('org_size_cat').size() * 100
    mesh_pct_df = mesh_pct_by_size.reset_index()
    mesh_pct_df.columns = ['org_size', 'mesh_percentage']
    mesh_pct_df = mesh_pct_df.dropna()
    
    area = alt.Chart(mesh_pct_df).mark_area(
        opacity=0.3,
        color=get_primary_color()
    ).encode(
        x=alt.X('org_size:N', title='Organization Size', sort=ORG_SIZE_ORDER),
        y=alt.Y('mesh_percentage:Q', title='Data Mesh Adoption %')
    )
    
    line = alt.Chart(mesh_pct_df).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('org_size:N', title='Organization Size', sort=ORG_SIZE_ORDER),
        y=alt.Y('mesh_percentage:Q', title='Data Mesh Adoption %'),
        tooltip=['org_size:N', alt.Tooltip('mesh_percentage:Q', format='.1f')]
    )
    
    chart = (area + line).properties(height=400)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        if len(mesh_pct_df) >= 2:
            min_mesh = mesh_pct_df['mesh_percentage'].min()
            max_mesh = mesh_pct_df['mesh_percentage'].max()
            min_size = mesh_pct_df.loc[mesh_pct_df['mesh_percentage'].idxmin(), 'org_size']
            max_size = mesh_pct_df.loc[mesh_pct_df['mesh_percentage'].idxmax(), 'org_size']
            growth = max_mesh - min_mesh
            
            st.caption(f"**:primary[Lowest adoption:]** {min_size} ({min_mesh:.0f}%) — Smaller organizations often lack the domain complexity that makes data mesh valuable, favoring simpler centralized approaches.")
            st.caption(f"**:primary[Highest adoption:]** {max_size} ({max_mesh:.0f}%) — Larger enterprises embrace mesh patterns to scale data ownership across autonomous domain teams.")
            
            if growth > 15:
                st.caption(f":primary[:material/trending_up:] **{growth:.0f}pt spread** — Strong correlation between org size and mesh adoption suggests it's primarily an enterprise-scale solution.")
            elif growth > 5:
                st.caption(f":primary[:material/trending_up:] **{growth:.0f}pt spread** — Moderate growth indicates mesh is gaining traction beyond just the largest organizations.")
            else:
                st.caption(f":primary[:material/trending_flat:] **{growth:.0f}pt spread** — Relatively flat adoption across sizes suggests mesh principles are being applied regardless of scale.")

with st.container(border=True):
    st.markdown("#### :primary[:material/compare:] What Drives Architecture Choice?")
    
    col1, col2 = st.columns([3, 1])
    
    arch_counts = df_arch['architecture_trend'].value_counts()
    
    with col2:
        min_count = st.number_input(
            "Min. responses:",
            min_value=1,
            max_value=int(arch_counts.max()) if len(arch_counts) > 0 else 100,
            value=5,
            key="arch_min_count"
        )
    
    arch_options = sorted([opt for opt in arch_counts.index if arch_counts[opt] >= min_count])
    
    with col1:
        architecture_type = st.selectbox(
            "Select Architecture:",
            options=arch_options,
            key="arch_select"
        )
    
    if architecture_type:
        arch_df = df_arch[df_arch['architecture_trend'] == architecture_type]
        non_arch_df = df_arch[df_arch['architecture_trend'] != architecture_type]
        
        arch_industry = arch_df['industry'].value_counts(normalize=True).head(6) * 100
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown("##### Industry Distribution")
            industry_counts = arch_df['industry'].value_counts().head(6)
            chart = alt.Chart(industry_counts.reset_index()).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('industry:N', sort='-x', title=None),
                x=alt.X('count:Q', title='Count'),
                color=alt.Color('count:Q', scale=alt.Scale(scheme='viridis'), legend=None)
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)
        
        with col2:
            st.markdown("##### Key Metrics")
            st.metric("Total Users", f"{len(arch_df):,}")
            ai_pct = arch_df['ai_embedded'].sum() / len(arch_df) * 100 if len(arch_df) > 0 else 0
            st.metric("AI Embedded", f"{ai_pct:.1f}%")
            ff_pct = arch_df['has_firefighting'].sum() / len(arch_df) * 100 if len(arch_df) > 0 else 0
            st.metric("Firefighting Rate", f"{ff_pct:.1f}%")
            growth_pct = (arch_df['team_growth_2026'] == 'Grow').sum() / len(arch_df) * 100 if len(arch_df) > 0 else 0
            st.metric("Expect Growth", f"{growth_pct:.1f}%")
        
        with col3:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            top_ind = arch_industry.idxmax() if len(arch_industry) > 0 else "N/A"
            top_ind_pct = arch_industry.max() if len(arch_industry) > 0 else 0
            
            other_ai = non_arch_df['ai_embedded'].sum() / len(non_arch_df) * 100 if len(non_arch_df) > 0 else 0
            other_ff = non_arch_df['has_firefighting'].sum() / len(non_arch_df) * 100 if len(non_arch_df) > 0 else 0
            other_growth = (non_arch_df['team_growth_2026'] == 'Grow').sum() / len(non_arch_df) * 100 if len(non_arch_df) > 0 else 0
            
            ai_diff = ai_pct - other_ai
            ff_diff = ff_pct - other_ff
            growth_diff = growth_pct - other_growth
            total_pct = len(arch_df) / len(df_arch) * 100 if len(df_arch) > 0 else 0
            
            st.caption(f"**:primary[{architecture_type}]** represents **{len(arch_df):,} respondents** ({total_pct:.0f}% of survey), with **{top_ind}** leading adoption at {top_ind_pct:.0f}%.")
            
            if ai_diff > 0:
                st.caption(f"**:primary[AI Embedded:]** Teams using this architecture are **{abs(ai_diff):.0f}% more likely** to have AI embedded in their workflows compared to other architectures.")
            else:
                st.caption(f"**:primary[AI Embedded:]** Adoption among these teams lags **{abs(ai_diff):.0f}%** behind other architectures, suggesting room for AI integration.")
            
            if ff_diff > 0:
                st.caption(f"**:primary[Firefighting:]** They report **{abs(ff_diff):.0f}% more firefighting** than peers, indicating potential stability challenges.")
            else:
                st.caption(f"**:primary[Firefighting:]** They enjoy **{abs(ff_diff):.0f}% less firefighting** than peers, suggesting more stable workflows.")
            
            if growth_diff > 0:
                st.caption(f"**:primary[Growth Outlook:]** **{growth_pct:.0f}%** expect team growth—**{abs(growth_diff):.0f}% higher** than average, signaling strong investment in this approach.")
            else:
                st.caption(f"**:primary[Growth Outlook:]** **{growth_pct:.0f}%** expect team growth—**{abs(growth_diff):.0f}% below** average, possibly indicating a mature or consolidating segment.")
    else:
        st.info("No architecture options meet the minimum response threshold.")
