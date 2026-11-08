import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_pdf_report(user_details, prediction_data, recommendations):
    """
    Generates a beautifully styled PDF report in-memory and returns its byte content.
    
    Args:
        user_details: dict with 'username', 'email'
        prediction_data: dict with 'symptoms', 'predicted_disease', 'confidence_score', 'created_at'
        recommendations: dict with 'description', 'causes', 'precautions', 'diet', 'exercises', 'specialist'
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    # Styles Setup
    styles = getSampleStyleSheet()
    
    # Palette Colors
    PRIMARY_COLOR = colors.HexColor("#1e3a8a")   # Deep Blue
    SECONDARY_COLOR = colors.HexColor("#0d9488") # Teal
    DARK_TEXT = colors.HexColor("#1f2937")       # Charcoal
    LIGHT_BG = colors.HexColor("#f3f4f6")        # Soft grey
    ACCENT_BG = colors.HexColor("#eff6ff")       # Soft light blue
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=SECONDARY_COLOR,
        alignment=TA_CENTER
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=DARK_TEXT
    )
    
    bold_label = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=DARK_TEXT
    )
    
    results_title = ParagraphStyle(
        'ResultsTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY_COLOR
    )
    
    results_value = ParagraphStyle(
        'ResultsValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=SECONDARY_COLOR
    )

    story = []
    
    # Header Banner / Logo
    story.append(Paragraph("MediPredict AI", title_style))
    story.append(Paragraph("Disease Prediction & Health Recommendation Report", subtitle_style))
    story.append(Spacer(1, 15))
    
    # Decorative line
    line_table = Table([[""]], colWidths=[532])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 2, PRIMARY_COLOR),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0)
    ]))
    story.append(line_table)
    story.append(Spacer(1, 15))
    
    # Patient & Report Metadata Table
    dt_obj = prediction_data.get('created_at')
    if isinstance(dt_obj, str):
        # Already a string
        formatted_date = dt_obj
    elif isinstance(dt_obj, datetime):
        formatted_date = dt_obj.strftime("%d %b %Y, %I:%M %p")
    else:
        formatted_date = datetime.now().strftime("%d %b %Y, %I:%M %p")
        
    meta_data = [
        [Paragraph("Patient Name:", bold_label), Paragraph(user_details.get('username', 'N/A'), body_style),
         Paragraph("Report Date:", bold_label), Paragraph(formatted_date, body_style)],
        [Paragraph("Patient Email:", bold_label), Paragraph(user_details.get('email', 'N/A'), body_style),
         Paragraph("Report ID:", bold_label), Paragraph(f"MPR-{prediction_data.get('id', 'N/A')}", body_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[100, 166, 100, 166])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # Symptoms Entered Section
    story.append(Paragraph("Reported Symptoms", section_heading))
    symptoms_text = prediction_data.get('symptoms', 'None')
    # If symptoms is list, join them
    if isinstance(symptoms_text, list):
        symptoms_text = ", ".join(symptoms_text)
    
    story.append(Paragraph(symptoms_text, body_style))
    story.append(Spacer(1, 15))
    
    # Prediction Results Box
    story.append(Paragraph("Diagnostic Classification Output", section_heading))
    conf_score = prediction_data.get('confidence_score', 0.0)
    conf_pct = f"{conf_score * 100:.1f}%" if conf_score <= 1.0 else f"{conf_score:.1f}%"
    
    pred_data = [
        [Paragraph("Predicted Condition", results_title), Paragraph("Inference Confidence", results_title)],
        [Paragraph(prediction_data.get('predicted_disease', 'N/A').title(), results_value), Paragraph(conf_pct, results_value)]
    ]
    pred_table = Table(pred_data, colWidths=[266, 266])
    pred_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ACCENT_BG),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 12),
        ('BOX', (0,0), (-1,-1), 1.5, PRIMARY_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
    ]))
    story.append(pred_table)
    story.append(Spacer(1, 15))
    
    # Clinical Description & Causes
    story.append(Paragraph("Clinical Description", section_heading))
    story.append(Paragraph(recommendations.get('description', 'N/A'), body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Possible Causes / Risk Factors", section_heading))
    causes_list = recommendations.get('causes', [])
    if causes_list:
        causes_content = "<br/>".join([f"&bull; {cause}" for cause in causes_list])
    else:
        causes_content = "N/A"
    story.append(Paragraph(causes_content, body_style))
    story.append(Spacer(1, 15))
    
    # Health Recommendations Section
    story.append(Paragraph("Actionable Health Recommendations", section_heading))
    
    rec_table_data = []
    
    # Precautions
    precautions = recommendations.get('precautions', [])
    prec_content = "<br/>".join([f"{i+1}. {p}" for i, p in enumerate(precautions)]) if precautions else "N/A"
    rec_table_data.append([Paragraph("Recommended Precautions", bold_label), Paragraph(prec_content, body_style)])
    
    # Diet Plan
    diet = recommendations.get('diet', [])
    diet_content = ", ".join(diet) if diet else "N/A"
    rec_table_data.append([Paragraph("Suggested Diet & Foods", bold_label), Paragraph(diet_content, body_style)])
    
    # Exercises
    exercises = recommendations.get('exercises', [])
    exec_content = ", ".join(exercises) if exercises else "N/A"
    rec_table_data.append([Paragraph("Recommended Exercises", bold_label), Paragraph(exec_content, body_style)])
    
    # Specialist
    specialist = recommendations.get('specialist', 'General Physician')
    rec_table_data.append([Paragraph("Suggested Medical Specialist", bold_label), Paragraph(f"Consult a <b>{specialist}</b> for clinical confirmation and guidance.", body_style)])
    
    rec_table = Table(rec_table_data, colWidths=[160, 372])
    rec_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_BG)
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 30))
    
    # Disclaimer block at the bottom
    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("<b>Disclaimer:</b> MediPredict AI is an automated machine learning screening prototype. This report is for educational purposes only and does not constitute formal medical diagnosis, advice, or treatment plans. If you are experiencing serious or worsening symptoms, please consult a qualified healthcare professional or seek emergency medical services immediately.", disclaimer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
