import fitz  # PyMuPDF
from groq import Groq
import os
import json
import base64
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def convert_pdf_to_images(pdf_path):
    """
    Converts a PDF file into a list of base64 encoded images (PNG).
    """
    doc = fitz.open(pdf_path)
    base64_images = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        base64_img = base64.b64encode(img_data).decode('utf-8')
        base64_images.append(base64_img)
        
    return base64_images

def generate_exam_with_groq(base64_images, api_key, status_callback=None):
    """
    Sends PDF page images to Groq (Llama 4 Scout) in batches to generate a full exam.
    Processes 5 pages at a time to stay within limits and cover the whole PDF.
    """
    client = Groq(api_key=api_key)
    model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    # CONTENT RELEVANCE INSTRUCTIONS
    prompt_template = """
    You are an expert professor designed to help students prepare for exams.
    Analyze the provided images, which represent pages from a study material PDF.
    
    CRITICAL INSTRUCTION:
    1. IGNORE administrative pages like Syllabus, Attendance Policy, Course Logistics, Table of Contents, or Introduction/Welcome pages.
    2. FOCUS ONLY on technical subject matter, core concepts, definitions, formulas, and DIAGRAMS.
    3. If the images only contain administrative info, return an empty JSON structure for that batch.
    4. Pay special attention to DIAGRAMS, CHARTS, or FIGURES.

    Task: Generate questions based on the SUBJECT MATTER found in these pages.
    Return output strictly as a JSON object:
    {{
      "mcq": [{{ "question": "...", "options": ["a", "b", "c", "d"], "answer": "..." }}],
      "short_answer": [{{ "question": "...", "answer": "..." }}],
      "essay": [{{ "question": "...", "key_points_to_cover": "..." }}]
    }}
    """
    
    all_results = {
        "mcq": [],
        "short_answer": [],
        "essay": []
    }
    
    batch_size = 5
    total_pages = len(base64_images)
    
    for i in range(0, total_pages, batch_size):
        batch = base64_images[i:i + batch_size]
        current_batch_num = (i // batch_size) + 1
        total_batches = (total_pages + batch_size - 1) // batch_size
        
        if status_callback:
            status_callback(f"Processing batch {current_batch_num} of {total_batches} (Pages {i+1} to {min(i+batch_size, total_pages)})...")
        
        content = [{"type": "text", "text": prompt_template}]
        for img_b64 in batch:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })
            
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048
            )
            
            result = json.loads(completion.choices[0].message.content)
            
            # Merge results
            if "mcq" in result: all_results["mcq"].extend(result["mcq"])
            if "short_answer" in result: all_results["short_answer"].extend(result["short_answer"])
            if "essay" in result: all_results["essay"].extend(result["essay"])
            
        except Exception as e:
            if status_callback:
                status_callback(f"⚠️ Error in batch {current_batch_num}: {str(e)}")
            continue

    return all_results

def create_pdf_report(exam_json):

    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=15
    )
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    option_style = ParagraphStyle(
        'Option',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=4
    )
    
    # Title
    story.append(Paragraph("Generated Exam Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Section: MCQs
    if exam_json.get("mcq"):
        story.append(Paragraph("Part I: Multiple Choice Questions", section_style))
        for i, q in enumerate(exam_json["mcq"]):
            # Question
            question_text = f"{i+1}. {q.get('question', 'N/A')}"
            story.append(Paragraph(question_text, question_style))
            
            # Options
            for opt in q.get('options', []):
                story.append(Paragraph(f"• {opt}", option_style))
            story.append(Spacer(1, 0.1*inch))
    
    # Section: Short Answer
    if exam_json.get("short_answer"):
        story.append(Paragraph("Part II: Short Answer Questions", section_style))
        for i, q in enumerate(exam_json["short_answer"]):
            question_text = f"{i+1}. {q.get('question', 'N/A')}"
            story.append(Paragraph(question_text, question_style))
            story.append(Spacer(1, 0.1*inch))
    
    # Section: Essay
    if exam_json.get("essay"):
        story.append(Paragraph("Part III: Essay Questions", section_style))
        for i, q in enumerate(exam_json["essay"]):
            question_text = f"{i+1}. {q.get('question', 'N/A')}"
            story.append(Paragraph(question_text, question_style))
            story.append(Spacer(1, 0.1*inch))
    
    # New page for Answer Key
    story.append(PageBreak())
    story.append(Paragraph("Answer Key", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # MCQ Answers
    if exam_json.get("mcq"):
        story.append(Paragraph("Multiple Choice Answers:", section_style))
        for i, q in enumerate(exam_json["mcq"]):
            answer_text = f"{i+1}. {q.get('answer', 'N/A')}"
            story.append(Paragraph(answer_text, question_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Short Answer Reference
    if exam_json.get("short_answer"):
        story.append(Paragraph("Short Answer Reference:", section_style))
        for i, q in enumerate(exam_json["short_answer"]):
            answer_text = f"{i+1}. {q.get('answer', 'N/A')}"
            story.append(Paragraph(answer_text, question_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Essay Key Points
    if exam_json.get("essay"):
        story.append(Paragraph("Essay Key Points:", section_style))
        for i, q in enumerate(exam_json["essay"]):
            key_points = f"{i+1}. {q.get('key_points_to_cover', 'N/A')}"
            story.append(Paragraph(key_points, question_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
