from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Colors
    DARK_BLUE = RGBColor(15, 23, 42)
    TEAL = RGBColor(14, 165, 233)
    WHITE = RGBColor(255, 255, 255)
    TEXT_DARK = RGBColor(51, 65, 85)
    BG_GRAY = RGBColor(248, 250, 252)

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, category_text="AI WORKSHOP"):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
        
        p_cat = tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = TEAL

        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_BLUE

    def add_bullets(slide, items, left=Inches(0.8), top=Inches(1.8), width=Inches(11.7), height=Inches(5.0)):
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = item[0]
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = DARK_BLUE
            
            if len(item) > 1 and item[1]:
                p_sub = tf.add_paragraph()
                p_sub.text = item[1]
                p_sub.font.size = Pt(14)
                p_sub.font.color.rgb = TEXT_DARK
                p_sub.level = 1

    def add_table(slide, headers, rows, left=Inches(0.8), top=Inches(1.8), width=Inches(11.7), height=Inches(4.5)):
        table_shape = slide.shapes.add_table(len(rows) + 1, len(headers), left, top, width, height)
        table = table_shape.table
        
        # Headers
        for idx, header in enumerate(headers):
            cell = table.cell(0, idx)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = DARK_BLUE
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.bold = True
                paragraph.font.color.rgb = WHITE
                paragraph.font.size = Pt(14)

        # Rows
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                cell = table.cell(r_idx + 1, c_idx)
                cell.text = str(val)
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 0 else BG_GRAY
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.color.rgb = TEXT_DARK
                    paragraph.font.size = Pt(13)

    # -------------------------------------------------------------------------
    # SLIDE 1: Title
    # -------------------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, DARK_BLUE)
    tb = s1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.33), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = "AI to Agentic AI"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = WHITE

    p2 = tf.add_paragraph()
    p2.text = "Concepts, Campus Agent Hands-on & Career Path"
    p2.font.size = Pt(24)
    p2.font.color.rgb = TEAL

    p3 = tf.add_paragraph()
    p3.text = "\nBuilding Practical Tool-Calling Autonomous Agents for Real-World Campus Applications\nFormat: Interactive College Workshop | Hands-on Python & OpenAI Tools\nHost: Aigosys Technical Workshop"
    p3.font.size = Pt(14)
    p3.font.color.rgb = WHITE

    # -------------------------------------------------------------------------
    # SLIDE 2: Journey Map
    # -------------------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Today's Journey Map")
    add_bullets(s2, [
        ("01. AI Foundations", "ML vs DL vs AI, Neural Networks, Modern AI Tooling Landscape"),
        ("02. Agents & Systems", "LLMs vs Autonomous Agents, Tool Calling & Workflows, RAG vs CAG vs AGI"),
        ("03. Campus Agent Build", "Architecture & Database, Writing Custom Python Tools, Live Terminal Demo & Debug"),
        ("04. Next-Gen Retrieval", "Cloudflare AI Search & Modern Agentic Retrieval Infrastructure for Large Documents"),
        ("05. Career & Action", "30-Day Developer Growth Plan, Recruiter Expectations, and Certificate Distribution")
    ])

    # -------------------------------------------------------------------------
    # SLIDE 3: Workshop Goals
    # -------------------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Workshop Goals & Outcomes")
    add_bullets(s3, [
        ("Conceptual Mastery", "ML vs DL intuition (predicting grades vs face recognition); Chatbots vs Tool-Calling Agents; RAG vs CAG architectures."),
        ("Tangible Portfolio Project", "A running Campus AI Agent in Python that interacts with SQLite across 6 distinct operational tools."),
        ("Extensible Skillset", "Step-by-step knowledge to implement and attach custom tools to an LLM agent in under 5 minutes.")
    ])

    # -------------------------------------------------------------------------
    # SLIDE 5: What is Artificial Intelligence?
    # -------------------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "What is Artificial Intelligence?")
    add_bullets(s5, [
        ("Narrow AI (Applied AI)", "Designed to excel at one specific task. Dominates 100% of real-world software applications today.\nExamples: Gmail spam filters, Chess bots, Face ID, Netflix recommendation algorithms."),
        ("General AI (AGI Vision)", "Theoretical human-level adaptability across any intellectual domain. Can learn, reason, and transfer knowledge across unrelated domains seamlessly.\nExamples: Sci-Fi systems like Jarvis or HAL 9000 (Currently aspirational).")
    ])

    # -------------------------------------------------------------------------
    # SLIDE 6: Machine Learning in One Slide
    # -------------------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Machine Learning in One Slide")
    add_bullets(s6, [
        ("Traditional Software Paradigm", "Data + Rules → Answers\nExample: Writing code like `if attendance < 75%: reject_exam_hall_ticket()`."),
        ("Machine Learning Paradigm", "Data + Answers → Rules\nExample: Feeding 5 years of historical student study habits and exam results into an algorithm to automatically infer grading rules.")
    ])

    # -------------------------------------------------------------------------
    # SLIDE 7: The Three Core Types of Machine Learning
    # -------------------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "The Three Core Types of Machine Learning")
    add_bullets(s7, [
        ("Supervised Learning", "Learns from labeled data (Input + Correct Output).\nCampus Example: Predicting final exam scores based on study hours, attendance logs, and internal assessment marks."),
        ("Unsupervised Learning", "Finds hidden patterns or clusters in unlabeled data.\nCampus Example: Grouping students into study profiles based on library gate access timestamps and book checkouts."),
        ("Reinforcement Learning", "Learns via trial, error, rewards, and penalties.\nCampus Example: Autonomous robotics navigation trained to maneuver quadcopters through college corridors.")
    ])

    # -------------------------------------------------------------------------
    # SLIDE 13: What is an AI Agent?
    # -------------------------------------------------------------------------
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "What is an AI Agent?")
    add_bullets(s13, [
        ("AI Agent Core Equation", "AI Agent = LLM Brain + Context Memory + Tool Execution + Goal Orientation"),
        ("LLM Core", "Reasons over user intent and decides which action or function to invoke."),
        ("Tools & APIs", "Functions that read databases, trigger webhooks, or query local APIs."),
        ("Memory & Autonomous Loops", "Maintains state and re-evaluates results until goal criteria are met."),
        ("Real-World Example", "An agent asked to 'book a room' checks availability, inserts a row into SQLite, and sends a confirmation email without step-by-step human intervention.")
    ])

    # -------------------------------------------------------------------------
    # SLIDE 21: Architecture Comparison Matrix (Table)
    # -------------------------------------------------------------------------
    s21 = prs.slides.add_slide(blank_layout)
    add_header(s21, "Architecture Comparison Matrix")
    headers = ["Architecture", "Core Focus", "Action Capability", "Best Campus Example"]
    rows = [
        ["Chatbot", "Text Conversation", "None (Text Only)", "Writing an email draft to HOD"],
        ["Tool-Calling Agent", "Executing Workflows", "High (Executes Code & DBs)", "Adding events, issuing certificates"],
        ["RAG", "Unstructured Doc Search", "Read-only Retrieval", "Searching 200-page College Regulation PDF"],
        ["CAG", "Cached High-Speed Context", "Read-only High Speed", "Instant lookup across semester schedule"],
        ["AGI", "General Autonomous Human", "Theoretical Universal", "Future autonomous department manager"]
    ]
    add_table(s21, headers, rows)

    # -------------------------------------------------------------------------
    # SLIDE 27 & 28: Campus Agent Code Sample
    # -------------------------------------------------------------------------
    s28 = prs.slides.add_slide(blank_layout)
    add_header(s28, "Python Tool Implementation (`tools.py`)", "HANDS-ON CODE")
    tb = s28.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = """from db import get_db

# Tool 1: Search Events
def search_events(query: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE title LIKE ? COLLATE NOCASE", (f"%{query}%",))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Tool 2: Certificate Generator
def generate_certificate(student_name: str):
    return f"Certificate generated successfully for {student_name}. Download URL: https://certificate.aigosys.com/pdf/{student_name}" """
    p.font.size = Pt(13)
    p.font.name = "Courier New"
    p.font.color.rgb = DARK_BLUE

    # -------------------------------------------------------------------------
    # SLIDE 31: Troubleshooting Table
    # -------------------------------------------------------------------------
    s31 = prs.slides.add_slide(blank_layout)
    add_header(s31, "Troubleshooting & Common Pitfalls")
    headers_31 = ["Symptom / Error", "Root Cause", "Quick Developer Fix"]
    rows_31 = [
        ["APIKeyNotFoundError", ".env file missing or not loaded", "Call load_dotenv() at top of script"],
        ["sqlite3.OperationalError", "Database tables not initialized", "Execute init_db() in db.py"],
        ["Tool Never Triggers", "Vague tool description in JSON", "Rewrite schema description to be explicit"],
        ["Certificate 403 Error", "Network/Cloudflare restriction", "Fallback to local base URL http://127.0.0.1:8001"],
        ["No Search Results Returned", "SQL Case-sensitivity mismatch", "Use LIKE ? COLLATE NOCASE in SQL query"]
    ]
    add_table(s31, headers_31, rows_31)

    # -------------------------------------------------------------------------
    # SLIDE 46: Certificate & Connect
    # -------------------------------------------------------------------------
    s46 = prs.slides.add_slide(blank_layout)
    set_slide_background(s46, DARK_BLUE)
    add_header(s46, "Connect & Download Your Certificate", "CERTIFICATE DISTRIBUTION")
    
    # Change title text colors for dark slide
    for shape in s46.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if p.text != "CERTIFICATE DISTRIBUTION":
                    p.font.color.rgb = WHITE

    add_bullets(s46, [
        ("1. Scan QR / Open WhatsApp", "Join the Aigosys Developer Community."),
        ("2. Send Command", "Type 'certificate' in the chat."),
        ("3. Receive Certificate", "The bot immediately sends your personalized PDF certificate."),
        ("4. Share Accomplishment", "Tag @Aigosys on LinkedIn to showcase your project!")
    ], top=Inches(2.0))

    prs.save("AI_to_Agentic_AI_Workshop.pptx")
    print("Presentation saved successfully as 'AI_to_Agentic_AI_Workshop.pptx'.")

if __name__ == "__main__":
    create_presentation()