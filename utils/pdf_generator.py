from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
import tempfile

# 设置中文字体（修改为你的实际字体路径）
FONT_PATH = "C:/Windows/Fonts/simsun.ttc"
pdfmetrics.registerFont(TTFont('SimSun', FONT_PATH))


def create_styles():
    """创建自定义样式，避免与默认样式冲突"""
    styles = getSampleStyleSheet()

    # 覆盖默认Normal样式
    styles['Normal'].fontName = 'SimSun'
    styles['Normal'].fontSize = 12
    styles['Normal'].leading = 14

    # 新建中文标题样式（避免使用默认名称）
    styles.add(ParagraphStyle(
        name='CN_Heading1',
        parent=styles['Heading1'],
        fontName='SimSun',
        fontSize=16,
        alignment=1,  # 居中
        spaceAfter=14,
        textColor=colors.black
    ))

    styles.add(ParagraphStyle(
        name='CN_Heading2',
        parent=styles['Heading2'],
        fontName='SimSun',
        fontSize=14,
        spaceBefore=12,
        spaceAfter=12,
        textColor=colors.black
    ))

    # 新建表格正文样式
    styles.add(ParagraphStyle(
        name='Table_Text',
        parent=styles['Normal'],
        fontSize=10,
        leading=12
    ))

    return styles


def create_pdf(data):
    # 创建临时文件
    temp_file = tempfile.mktemp(suffix='.pdf')

    # 初始化文档
    doc = SimpleDocTemplate(
        temp_file,
        pagesize=letter,
        leftMargin=72,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = create_styles()
    elements = []

    # 标题部分
    title = Paragraph(data['metadata']['title'], styles['CN_Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 24))  # 添加标题间距

    # 元数据段落
    meta_info = [
        f"<b>日期:</b> {data['metadata']['date'][:10]}",
        f"<b>地点:</b> {data['metadata']['location']}",
        f"<b>主持人:</b> {data['metadata']['host']['name']}（{data['metadata']['host']['position']}）"
    ]

    for text in meta_info:
        p = Paragraph(text, styles['Normal'])
        p.keepWithNext = True  # 保持段落不分开
        elements.append(p)

    elements.append(Spacer(1, 12))  # 段落间距

    # 国际形势分析
    elements.append(Paragraph('国际形势分析', styles['CN_Heading2']))
    analysis = Paragraph(data['agenda']['international']['analysis'], styles['Normal'])
    analysis.spaceAfter = 18  # 设置段后间距
    elements.append(analysis)

    # 行动项表格
    table_data = [
        [Paragraph('<b>任务</b>', styles['Table_Text']),
         Paragraph('<b>负责人</b>', styles['Table_Text']),
         Paragraph('<b>截止日期</b>', styles['Table_Text'])]
    ]

    for item in data['actionItems']:
        if 'task' in item:
            table_data.append([
                Paragraph(item['task'], styles['Table_Text']),
                Paragraph(item['owner'], styles['Table_Text']),
                Paragraph(item['deadline'], styles['Table_Text'])
            ])

    table = Table(table_data, colWidths=[doc.width / 3] * 3)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'SimSun'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('WORDWRAP', (0, 0), (-1, -1), 'RMBF')  # 中文自动换行
    ]))

    elements.append(table)

    # 生成PDF
    doc.build(elements)
    return temp_file