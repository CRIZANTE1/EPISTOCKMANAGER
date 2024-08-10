import json
import streamlit as st 
from streamlit_lottie import st_lottie


def load_lottiefile(filepath: str):
    with open(filepath, 'r') as f:
        return json.load(f)
    
lottie_fantasm = load_lottiefile(r'animations\fantasm.json')

def animation_fantasm():
    st_lottie(lottie_fantasm,
            speed=1,
            reverse=False,
            loop=True,
            quality='high',
            height=200,  # Defina a altura desejada em pixels
            width=200,   # Defina a largura desejada em pixels
            key='fantasm_animation',
            )