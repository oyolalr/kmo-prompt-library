import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any
import os

# Constants
ELEMENT_TYPES = ['role', 'goal', 'audience', 'context', 'output', 'tone']
CSV_COLUMNS = ['title', 'type', 'content']
PROMPT_HISTORY_COLUMNS = ['name', 'timestamp', 'prompt']

# Custom theme and styling
def set_theme():
    st.markdown("""
    <style>
    /* Modern dark theme inspired by shadcn */
    :root {
        --background: #09090B;
        --foreground: #FAFAFA;
        --muted: #27272A;
        --muted-foreground: #A1A1AA;
        --popover: #18181B;
        --border: #27272A;
        --input: #27272A;
        --primary: #FAFAFA;
        --secondary: #27272A;
    }

    .stApp {
        background-color: var(--background);
        color: var(--foreground);
    }

    .stTitle {
        color: var(--foreground) !important;
        font-weight: 600 !important;
    }

    /* Input fields and Selectboxes styling */
    .stTextInput > div > div, .stSelectbox > div > div, .stTextArea > div > div {
        background-color: var(--input) !important;
        border-color: var(--border) !important;
        color: var(--foreground) !important;
    }

    /* Button styling - updated for better contrast */
    .stButton > button {
        background-color: var(--secondary) !important;
        color: var(--foreground) !important;
        border: 1px solid var(--border) !important;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: var(--muted) !important;
        border-color: var(--primary) !important;
    }

    .streamlit-expanderHeader {
        background-color: var(--secondary) !important;
        border-color: var(--border) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Data management
class DataManager:
    @staticmethod
    def load_data(filename: str, columns: List[str]) -> pd.DataFrame:
        if not os.path.exists(filename):
            df = pd.DataFrame(columns=columns)
            df.to_csv(filename, index=False)
            return df
        return pd.read_csv(filename)

    @staticmethod
    def save_data(df: pd.DataFrame, filename: str) -> None:
        df.to_csv(filename, index=False)

    @staticmethod
    def save_prompt(name: str, prompt: str) -> None:
        df = DataManager.load_data('prompt_history.csv', PROMPT_HISTORY_COLUMNS)
        # CHANGE: Formatted timestamp for better readability in history
        new_row = pd.DataFrame({
            'name': [name],
            'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'prompt': [prompt]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        DataManager.save_data(df, 'prompt_history.csv')

# UI Components
class ElementCreator:
    @staticmethod
    def render():
        with st.expander("Create New Element", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                element_type = st.selectbox("Type", ELEMENT_TYPES, key="new_type")
                title = st.text_input("Title", key="new_title")
            with col2:
                content = st.text_area("Content", key="new_content", height=100)
            
            if st.button("Add Element", key="add_element"):
                if title and content:
                    df = DataManager.load_data('prompt_elements.csv', CSV_COLUMNS)
                    new_row = pd.DataFrame({'title': [title], 'type': [element_type], 'content': [content]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    DataManager.save_data(df, 'prompt_elements.csv')
                    st.success("Element added successfully!")
                    # CHANGE: Use st.rerun() to refresh the list in other tabs
                    st.rerun()
                else:
                    st.error("Please provide both a title and content.")

class ElementEditor:
    @staticmethod
    def render():
        # CHANGE: Load the dataframe once at the beginning of the render method
        df = DataManager.load_data('prompt_elements.csv', CSV_COLUMNS)
        
        if df.empty:
            st.warning("No elements found. Please create some elements first.")
            return

        col1, col2 = st.columns(2)
        with col1:
            all_types = ['All'] + sorted(df['type'].unique().tolist())
            selected_type = st.selectbox("Filter by Type", all_types, key="filter_type")
        
        # CHANGE: Filter view based on selection
        filtered_df = df if selected_type == 'All' else df[df['type'] == selected_type]
        
        if filtered_df.empty:
            st.warning(f"No elements found for type: {selected_type}")
            return
        
        for index, row in filtered_df.iterrows():
            with st.expander(f"{row['title']} ({row['type']})", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    new_title = st.text_input("Title", value=row['title'], key=f"title_{index}")
                    # CHANGE: Safety check for index alignment in selectbox
                    current_type_idx = ELEMENT_TYPES.index(row['type']) if row['type'] in ELEMENT_TYPES else 0
                    new_type = st.selectbox("Type", ELEMENT_TYPES, index=current_type_idx, key=f"type_{index}")
                with col2:
                    new_content = st.text_area("Content", value=row['content'], key=f"content_{index}", height=100)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Update", key=f"update_{index}"):
                        # CHANGE: Modifying the master df using the original index from filtered_df
                        df.at[index, 'title'] = new_title
                        df.at[index, 'type'] = new_type
                        df.at[index, 'content'] = new_content
                        DataManager.save_data(df, 'prompt_elements.csv')
                        st.success("Updated!")
                        # CHANGE: Fixed function from st._rerun() to st.rerun()
                        st.rerun()
                with c2:
                    if st.button("Delete", key=f"delete_{index}"):
                        # CHANGE: Standardized deletion using drop
                        df = df.drop(index)
                        DataManager.save_data(df, 'prompt_elements.csv')
                        st.success("Deleted!")
                        # CHANGE: Fixed function from st._rerun() to st.rerun()
                        st.rerun()

class PromptBuilder:
    @staticmethod
    def render():
        df = DataManager.load_data('prompt_elements.csv', CSV_COLUMNS)
        
        col1, col2, col3 = st.columns(3)
        selections = {}
        
        with col1:
            selections['role'] = PromptBuilder._create_section("Role", 'role', df)
            selections['goal'] = PromptBuilder._create_section("Goal", 'goal', df)
        with col2:
            selections['audience'] = PromptBuilder._create_section("Target Audience", 'audience', df, True)
            selections['context'] = PromptBuilder._create_section("Context", 'context', df, True)
        with col3:
            selections['output'] = PromptBuilder._create_section("Output", 'output', df, True)
            selections['tone'] = PromptBuilder._create_section("Tone", 'tone', df)
        
        recursive_feedback = st.checkbox("Request recursive feedback")
        prompt = PromptBuilder._generate_prompt(selections, df, recursive_feedback)
        PromptBuilder._display_prompt(prompt)

    @staticmethod
    def _create_section(title: str, element_type: str, df: pd.DataFrame, multi_select: bool = False) -> Dict[str, Any]:
        elements = df[df['type'] == element_type]
        options = ["Skip", "Write your own"] + elements['title'].tolist()
        
        if multi_select:
            selected = st.multiselect(title, options, key=f"select_{element_type}")
        else:
            selected = st.selectbox(title, options, key=f"select_{element_type}")
        
        custom_content = ""
        is_custom = ("Write your own" in selected) if multi_select else (selected == "Write your own")
        if is_custom:
            custom_content = st.text_input(f"Custom {title}", key=f"custom_{element_type}")
        
        return {'selected': selected, 'custom': custom_content, 'elements': elements}

    @staticmethod
    def _generate_prompt(selections: Dict[str, Dict], df: pd.DataFrame, recursive_feedback: bool) -> str:
        prompt_parts = []
        for section, data in selections.items():
            sel = data['selected']
            # Skip logic for both single and multi-select
            if sel == "Skip" or (isinstance(sel, list) and (not sel or "Skip" in sel)):
                continue
                
            section_title = section.title()
            if isinstance(sel, list):
                content_list = []
                if "Write your own" in sel:
                    content_list.append(data['custom'])
                # CHANGE: Optimized list comprehension for multi-select content gathering
                content_list.extend([df[df['title'] == s]['content'].values[0] for s in sel if s not in ["Skip", "Write your own"]])
                content = "\n".join(content_list)
                prompt_parts.append(f"{section_title}:\n{content}")
            else:
                content = data['custom'] if sel == "Write your own" else df[df['title'] == sel]['content'].values[0]
                prompt_parts.append(f"{section_title}: {content}")
        
        prompt = "\n\n".join(prompt_parts)
        if recursive_feedback:
            prompt += "\n\nBefore you provide the response, please ask me any questions..."
        return prompt

    @staticmethod
    def _display_prompt(prompt: str):
        st.text_area("Generated Prompt", value=prompt, height=250, key="generated_prompt")
        col1, col2 = st.columns(2)
        with col1:
            prompt_name = st.text_input("Prompt Name")
        with col2:
            if st.button("Save Prompt"):
                if prompt_name:
                    DataManager.save_prompt(prompt_name, prompt)
                    st.success("Saved!")
                else:
                    st.error("Name required.")

class PromptBrowser:
    @staticmethod
    def render():
        if not os.path.exists('prompt_history.csv'):
            st.warning("No history found.")
            return
        
        df = pd.read_csv('prompt_history.csv')
        
        # NEW FEATURE: Download History Button
        # Encodes dataframe as CSV for browser download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download History as CSV",
            data=csv,
            file_name=f"prompt_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
        
        # CHANGE: Used iloc[::-1] to display the most recent prompts at the top
        for index, row in df.iloc[::-1].iterrows(): 
            with st.expander(f"{row['name']} ({row['timestamp']})", expanded=False):
                st.text_area("Content", value=row['prompt'], height=150, key=f"hist_{index}")

def main():
    # CHANGE: Optimized page config for the layout
    st.set_page_config(layout="wide", page_title="KMo's Prompt Tool")
    set_theme()
    st.title("KMo's Prompt Creation Tool")
    
    tabs = st.tabs(["Element Creator", "Element Editor", "Prompt Builder", "Browse Prompts"])
    with tabs[0]: ElementCreator.render()
    with tabs[1]: ElementEditor.render()
    with tabs[2]: PromptBuilder.render()
    with tabs[3]: PromptBrowser.render()

if __name__ == "__main__":
    main()
