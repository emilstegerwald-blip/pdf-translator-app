import streamlit as st
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# Konfiguration der Seite
st.set_page_config(page_title="PDF Buch-Übersetzer", layout="wide")

st.title("📖 PDF Reader & Übersetzer")
st.info("Lade eine PDF hoch, sie wird übersetzt und du kannst sie wie ein Buch lesen.")

# Session State Initialisierung (um den Fortschritt zu speichern)
if 'translated_pages' not in st.session_state:
    st.session_state.translated_pages = {}
if 'page_number' not in st.session_state:
    st.session_state.page_number = 0

def translate_text(text):
    """Übersetzt Text ins Deutsche, lässt Zahlen unberührt."""
    if not text.strip():
        return ""
    try:
        # GoogleTranslator behält Zahlen normalerweise im Kontext bei
        translated = GoogleTranslator(source='auto', target='de').translate(text)
        return translated
    except Exception as e:
        return f"Fehler bei der Übersetzung: {e}"

def create_pdf(text_list):
    """Erstellt eine neue PDF aus der Liste der übersetzten Texte."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    for text in text_list:
        text_object = c.beginText(40, height - 40)
        text_object.setFont("Helvetica", 10)
        
        # Zeilenumbruch-Logik (vereinfacht)
        lines = text.split('\n')
        for line in lines:
            text_object.textLine(line)
        
        c.drawText(text_object)
        c.showPage()
    
    c.save()
    buffer.seek(0)
    return buffer

# File Uploader
uploaded_file = st.file_uploader("Wähle eine PDF-Datei", type="pdf")

if uploaded_file is not None:
    # PDF öffnen
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Vorherige Seite") and st.session_state.page_number > 0:
            st.session_state.page_number -= 1
    with col3:
        if st.button("Nächste Seite ➡️") and st.session_state.page_number < total_pages - 1:
            st.session_state.page_number += 1
    
    current_page_idx = st.session_state.page_number
    st.write(f"Seite {current_page_idx + 1} von {total_pages}")

    # Seite verarbeiten
    if current_page_idx not in st.session_state.translated_pages:
        with st.spinner(f"Übersetze Seite {current_page_idx + 1}... bitte warten."):
            page = doc.load_page(current_page_idx)
            original_text = page.get_text("text")
            
            # Übersetzung durchführen
            german_text = translate_text(original_text)
            st.session_state.translated_pages[current_page_idx] = german_text
    
    # Anzeige wie ein Buch
    display_text = st.session_state.translated_pages[current_page_idx]
    
    st.markdown("---")
    # Buch-Optik Container
    st.markdown(
        f"""
        <div style="background-color: #f9f9f9; padding: 40px; border-radius: 10px; border: 1px solid #ddd; min-height: 600px; color: black; font-family: 'Georgia', serif; line-height: 1.6;">
            {display_text.replace('\n', '<br>')}
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Download Option für das gesamte (bis jetzt übersetzte) Buch
    if st.button("Übersetzte PDF generieren & speichern"):
        all_translated = [st.session_state.translated_pages.get(i, "Seite noch nicht geladen") for i in range(total_pages)]
        pdf_output = create_pdf(all_translated)
        st.download_button(
            label="Download der deutschen PDF",
            data=pdf_output,
            file_name="uebersetztes_buch.pdf",
            mime="application/pdf"
        )
