import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import create_donut_chart, get_categorical_colors

st.markdown("# :primary[:material/forum:] Industry Voices Explorer")
st.markdown("Discover what data practitioners wish the industry understood better")

df = get_filtered_df()

voices_df = df[df['industry_wish'].notna() & (df['industry_wish'].str.strip() != '')]
n_voices = len(voices_df)

all_text = ' '.join(voices_df['industry_wish'].dropna()).lower()
stop_words = {'the', 'a', 'an', 'is', 'it', 'to', 'and', 'of', 'in', 'that', 'for', 
              'on', 'with', 'as', 'be', 'are', 'was', 'this', 'not', 'but', 'they',
              'have', 'has', 'had', 'we', 'you', 'i', 'or', 'can', 'more', 'about',
              'from', 'all', 'just', 'how', 'what', 'when', 'there', 'their', 'so',
              'if', 'than', 'its', "it's", "it's", 'at', 'do', 'would', 'by', 'like', 'need', 'also',
              'being', 'been', 'were', 'get', 'much', 'many', 'into', 'only', 'should'}
words = [w.strip('.,!?()[]{}":;') for w in all_text.split() 
         if len(w) > 3 and w.strip('.,!?()[]{}":;').lower() not in stop_words]
theme_counts = pd.Series(words).value_counts().head(25)
theme_options = {f"{word} ({count})": word for word, count in theme_counts.items()}

init_multiselect_state("voice_theme", "All themes")
init_multiselect_state("voice_role", "All roles")
init_multiselect_state("voice_industry", "All industries")
init_multiselect_state("voice_org", "All org sizes")

with st.container(border=True):
    st.markdown("#### :primary[:material/search:] Search & Filter Quotes")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.multiselect(
            "Filter by theme:",
            options=["All themes"] + list(theme_options.keys()),
            key="voice_theme"
        )
        selected_themes = get_multiselect_values("voice_theme", "All themes", theme_options)
    
    filtered_voices = voices_df.copy()
    if selected_themes:
        mask = filtered_voices['industry_wish'].apply(
            lambda x: any(theme in str(x).lower() for theme in selected_themes) if pd.notna(x) else False
        )
        filtered_voices = filtered_voices[mask]
    
    with col2:
        role_opts = get_options_with_counts(filtered_voices, 'role')
        if role_opts:
            st.multiselect(
                "Filter by role:",
                options=["All roles"] + list(role_opts.keys()),
                key="voice_role"
            )
            selected_roles = get_multiselect_values("voice_role", "All roles", role_opts)
        else:
            st.info("No roles available")
            selected_roles = []
    
    if selected_roles:
        filtered_voices = filtered_voices[filtered_voices['role'].isin(selected_roles)]
    
    col3, col4 = st.columns(2)
    
    with col3:
        industry_opts = get_options_with_counts(filtered_voices, 'industry')
        if industry_opts:
            st.multiselect(
                "Filter by industry:",
                options=["All industries"] + list(industry_opts.keys()),
                key="voice_industry"
            )
            selected_industries = get_multiselect_values("voice_industry", "All industries", industry_opts)
        else:
            st.info("No industries available")
            selected_industries = []
    
    if selected_industries:
        filtered_voices = filtered_voices[filtered_voices['industry'].isin(selected_industries)]
    
    with col4:
        size_order = ["< 50 employees", "50–199", "200–999", "1,000–10,000", "10,000+"]
        org_opts = get_options_with_counts(filtered_voices, 'org_size', size_order)
        if org_opts:
            st.multiselect(
                "Filter by org size:",
                options=["All org sizes"] + list(org_opts.keys()),
                key="voice_org"
            )
            selected_orgs = get_multiselect_values("voice_org", "All org sizes", org_opts)
        else:
            st.info("No org sizes available")
            selected_orgs = []

    if selected_orgs:
        filtered_voices = filtered_voices[filtered_voices['org_size'].isin(selected_orgs)]

with st.container(border=True):
    st.markdown(f"#### :primary[:material/format_quote:] Matching Quotes ({len(filtered_voices):,})")
    
    if len(filtered_voices) > 0:
        n_display = st.slider("Quotes to display:", 5, min(30, len(filtered_voices)), 10, key="n_quotes")
        
        sort_by = st.radio(
            "Sort by:",
            options=["Random", "Longest first", "Shortest first"],
            horizontal=True,
            key="voice_sort"
        )
        
        if sort_by == "Random":
            display_voices = filtered_voices.sample(min(n_display, len(filtered_voices)))
        elif sort_by == "Longest first":
            filtered_voices['wish_len'] = filtered_voices['industry_wish'].str.len()
            display_voices = filtered_voices.nlargest(n_display, 'wish_len')
        else:
            filtered_voices['wish_len'] = filtered_voices['industry_wish'].str.len()
            display_voices = filtered_voices.nsmallest(n_display, 'wish_len')
        
        for _, row in display_voices.iterrows():
            with st.container(border=True):
                st.markdown(f"*\"{row['industry_wish']}\"*")
                st.caption(f"— {row['role']}, {row['industry']}, {row['org_size']}, {row['region']}")
    else:
        st.info("No quotes match your search criteria. Try broadening your filters.")

with st.container(border=True):
    st.markdown("#### :primary[:material/analytics:] Voice Demographics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### By Role")
        role_chart = create_donut_chart(filtered_voices, 'role', height=250) if len(filtered_voices) > 0 else None
        if role_chart:
            st.altair_chart(role_chart, use_container_width=True)
    
    with col2:
        st.markdown("##### By Industry")
        industry_chart = create_donut_chart(filtered_voices, 'industry', height=250) if len(filtered_voices) > 0 else None
        if industry_chart:
            st.altair_chart(industry_chart, use_container_width=True)

with st.container(border=True):
    st.markdown("#### :primary[:material/tag:] Common Words & Themes")
    
    if len(filtered_voices) > 0:
        all_words = ' '.join(filtered_voices['industry_wish'].dropna()).lower()
        
        stop_words = {'the', 'a', 'an', 'is', 'it', 'to', 'and', 'of', 'in', 'that', 'for', 
                      'on', 'with', 'as', 'be', 'are', 'was', 'this', 'not', 'but', 'they',
                      'have', 'has', 'had', 'we', 'you', 'i', 'or', 'can', 'more', 'about',
                      'from', 'all', 'just', 'how', 'what', 'when', 'there', 'their', 'so',
                      'if', 'than', 'its', 'at', 'do', 'would', 'by', 'like', 'need', 'also'}
        
        words = [w.strip('.,!?()[]{}":;') for w in all_words.split() 
                 if len(w) > 3 and w.strip('.,!?()[]{}":;').lower() not in stop_words]
        
        word_counts = pd.Series(words).value_counts().head(20).reset_index()
        word_counts.columns = ['word', 'count']
        
        chart = alt.Chart(word_counts).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('word:N', sort='-x', title=None),
            x=alt.X('count:Q', title='Frequency'),
            color=alt.Color('word:N', scale=alt.Scale(range=get_categorical_colors()), legend=None),
            tooltip=['word:N', 'count:Q']
        ).properties(height=400)
        
        st.altair_chart(chart, use_container_width=True)

with st.container(border=True):
    st.markdown("#### :primary[:material/download:] Export Quotes")
    
    if len(filtered_voices) > 0:
        export_df = filtered_voices[['industry_wish', 'role', 'industry', 'org_size', 'region']].copy()
        export_df.columns = ['Quote', 'Role', 'Industry', 'Org Size', 'Region']
        
        csv = export_df.to_csv(index=False)
        
        st.download_button(
            label=":primary[:material/download:] Download as CSV",
            data=csv,
            file_name="industry_voices.csv",
            mime="text/csv"
        )
        
        st.caption(f"Export {len(filtered_voices)} matching quotes")
