# Gemini-Powered PDF Chatbot

Een interactieve chatbot die vragen over jouw PDF-documenten kan beantwoorden met behulp van Google's Gemini AI.

## Beschrijving

Deze applicatie stelt gebruikers in staat om PDF-documenten te uploaden en er vervolgens vragen over te stellen in natuurlijke taal. De chatbot analyseert de documenten, begrijpt de inhoud en geeft gedetailleerde antwoorden op basis van de informatie in de PDFs.

## Functionaliteiten

- 📄 **PDF-verwerking**: Upload meerdere PDF-documenten tegelijk
- 💬 **Interactieve chat**: Stel vragen over de inhoud van je documenten
- 🧠 **Context-bewust**: De chatbot onthoudt het gesprek en geeft samenhangende antwoorden
- 🔄 **Reset optie**: Wis de gespreksgeschiedenis wanneer nodig

## Technische details

De applicatie maakt gebruik van:

- **Streamlit**: Voor de gebruikersinterface
- **LangChain**: Voor het koppelen van verschillende AI-componenten
- **Google Gemini AI**: Als taalmodel voor het genereren van antwoorden
- **FAISS**: Voor het efficiënt opslaan en doorzoeken van document embeddings
- **PyPDF2**: Voor het extraheren van tekst uit PDF-bestanden

## Installatie

### Vereisten

- Python 3.8 of hoger
- Een Google API-sleutel voor Gemini

### Stappen

1. Clone deze repository naar je lokale machine:

```bash
git clone https://github.com/TikkaMasala1/CCC_Bellamy.git
cd https://github.com/TikkaMasala1/CCC_Bellamy.git
```

1. Installeer de benodigde packages:

```bash
pip install streamlit langchain langchain-google-genai faiss-cpu pypdf2 python-dotenv
pip install google-generativeai
```

1. Verkrijg een Google API-sleutel voor Gemini:
   - Ga naar [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Log in met je Google-account
   - Klik op "Create API Key" en volg de instructies
   - Kopieer de gegenereerde API-sleutel

1. Maak een `.env` bestand aan in de hoofdmap van het project en voeg je Google API-sleutel toe:

```bash
GOOGLE_API_KEY=AIzaSyCRA4gI4_0fJs0gWlyqHtqPlZy4JramDzE
```

Note: deze key is expired :-)

1. Start de applicatie:

```bash
streamlit run app.py
```

## Gebruiksaanwijzing

1. **Upload PDF-documenten**:
   - Klik op "Upload je PDF-bestanden" in de sidebar
   - Selecteer één of meerdere PDF-bestanden
   - Klik op "Verwerken"

2. **Stel vragen**:
   - Typ je vraag in het tekstveld onderaan
   - Klik op "Verstuur vraag"
   - Bekijk het antwoord en stel vervolgvragen

3. **Reset de chat**:
   - Klik op "Wis Gespreksgeschiedenis" in de sidebar om opnieuw te beginnen

## Hoe het werkt

1. **Documenten verwerken**:
   - Tekst wordt geëxtraheerd uit de PDF-bestanden
   - De tekst wordt opgesplitst in kleinere stukken
   - Deze stukken worden omgezet in vectorrepresentaties (embeddings)
   - De embeddings worden opgeslagen in een FAISS index

2. **Vragen beantwoorden**:
   - De vraag van de gebruiker wordt omgezet naar een vector
   - Het systeem zoekt de meest relevante tekstfragmenten
   - Deze fragmenten worden samen met de vraag naar het Gemini-model gestuurd
   - Het model genereert een antwoord op basis van de vraag en de context

## Beperkingen

- De applicatie kan moeite hebben met zeer grote PDF-bestanden
- PDFs met voornamelijk afbeeldingen of grafieken worden niet optimaal verwerkt
- De kwaliteit van antwoorden is afhankelijk van de duidelijkheid van de vragen en de kwaliteit van de PDFs

## Probleemoplossing

### API-sleutel problemen

Als je een foutmelding krijgt zoals "API key not valid", controleer dan het volgende:

1. **Controleer of de API-sleutel correct is**:
   - Ga naar [Google AI Studio](https://makersuite.google.com/app/apikey) en verifieer dat je API-sleutel nog geldig is
   - Kopieer de sleutel opnieuw naar je `.env` bestand
   - Zorg dat er geen spaties of extra tekens voor of na de sleutel staan

2. **Controleer of de Gemini API is ingeschakeld**:
   - Ga naar [Google Cloud Console](https://console.cloud.google.com/)
   - Navigeer naar "APIs & Services" > "Enabled APIs & Services"
   - Zoek naar "Gemini API" en zorg ervoor dat deze is ingeschakeld
   - Als de API niet is ingeschakeld, zoek hem dan op en klik op "Enable"

3. **Controleer of er kosten zijn verbonden**:
   - Google kan vereisen dat je een betaalmethode koppelt aan je account om de API te gebruiken
   - Controleer of je een quotum hebt bereikt als je een gratis versie gebruikt

4. **Stel de API-sleutel in via de terminal**:
   - Als het probleem aanhoudt, probeer de API-sleutel direct in de terminal in te stellen:

   Voor Windows:

   ```powershell
   set GOOGLE_API_KEY=AIzaSyCRA4gI4_0fJs0gWlyqHtqPlZy4JramDzE
   ```

   Voor macOS/Linux:

   ```bash
   export GOOGLE_API_KEY=AIzaSyCRA4gI4_0fJs0gWlyqHtqPlZy4JramDzE
   ```

   - Start vervolgens de applicatie vanuit dezelfde terminal-sessie

5. **Herstart de applicatie**:
   - Nadat je wijzigingen hebt aangebracht in het `.env` bestand of de omgevingsvariabele hebt ingesteld, start de applicatie opnieuw
