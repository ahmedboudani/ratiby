# salary/salary_functions.py
# salary/main.py

import os
import json
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from flask import Flask, render_template, request, jsonify, send_file

# تسجيل الخطوط العربية
pdfmetrics.registerFont(TTFont('ArabicFont', 'arial.ttf'))
pdfmetrics.registerFont(TTFont('BoldArabicFont', 'arialbd.ttf'))

# تحويل النص العربي ليظهر بشكل صحيح
def reshape_text(text):
    """Reshapes Arabic text for correct display in PDF"""
    if text is None:
        return ""
    return get_display(arabic_reshaper.reshape(text))

# تحويل اسم الشهر من إنجليزي إلى عربي
def get_arabic_month():
    """Converts the current month to Arabic and returns the year"""
    months_ar = {
        "January": "جانفي", "February": "فيفري", "March": "مارس", "April": "أفريل",
        "May": "ماي", "June": "جوان", "July": "جويلية", "August": "أوت",
        "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"
    }
    now = datetime.now()
    return months_ar.get(now.strftime("%B"), ""), now.strftime("%Y")

# دالة لتنسيق العملة
def format_currency(value):
    """Formats a number as Algerian currency"""
    try:
        return f"ج د {float(value):,.2f}"
    except (ValueError, TypeError):
        return "ج د 0.00"

# بيانات الوظائف (كما تم توفيرها)
data = {
    "موظفو التعليم":['معلم مدرسة إبتدائية',
                'أستاذ تعليم إبتدائي','أ ت إبتدائي قسم أول','أ ت إبتدائي قسم ثان','أستاذ مميز في التعليم الابتدائي',
                'أستاذ تعليم أساسي',
                'أستاذ تعليم متوسط','أ ت متوسط قسم أول','أ ت متوسط قسم ثان','أستاذ مميز في التعليم المتوسط',
                'أستاذ تعليم ثانوي','أ ت ثانوي قسم أول','أ ت ثانوي قسم ثان','أستاذ مميز في التعليم الثانوي'],
    "موظفو التربية":['ناظر في التعليم الابتدائي','ناظر في التعليم المتوسط','ناظر في التعليم الثانوي','مستشار التربية',
                'مساعد تربية','مساعد رئيسي للتربية',
                'مشرف تربية','مشرف رئيسي للتربية','مشرف رئيس للتربية','مشرف عام للتربية',
                'مربي متخصص في الدعم التربوي','مربي متخصص رئيسي في الدعم التربوي','مربي متخصص رئيس في الدعم التربوي','مربي متخصص عام في الدعم التربوي'],
    "موظفو المخابر" :['عون تقني للمخابر','معاون تقني للمخابر',
                'ملحق بالمخابر','ملحق رئيسي بالمخابر','ملحق رئيس بالمخابر','ملحق مشرف بالمخابر'],
    "موظفو مصالح الاقتصادية": ['مساعد مصالح الاقتصادية','مساعد رئيسي للمصالح الاقتصادية',
                'نائب مقتصد','نائب مقتصد مسير','مقتصد','مقتصد رئيسي'],
    " موظفو التفتيش": ['مفتش مادة للتعليم الابتدائي','مفتش إدارة للتعليم الابتدائي','مفتش التغذية المدرسية للتعليم الابتدائي',
                      'مفتش مادة للتعليم المتوسط','مفتش إدارة للتعليم المتوسط','مفتش التوجيه المدرسي للتعليم م','مفتش المالي للتعليم المتوسط',
                      'مفتش مادة للتعليم الثانوي','مفتش إدارة للتعليم الثانوي','مفتش التوجيه المدرسي للتعليم ثا','مفتش المالي للتعليم الثانوي','مفتش التربية الوطنية'],
    "موظفو إدارة مؤسسات التعليم":['مدير مدرسة إبتدائية','مدير متوسطة','مدير ثانوية'],
    " موظفو التوجيه و الإرشاد المدرسي":['مستشار التوجيه و الإرشاد م و م','مستشار محلل للتوجيه م و م','مستشار رئيسي للتوجيه م و م','مستشار رئيس للتوجيه م و م'],
    "موظفو التغذية المدرسية":['مستشار التغذية المدرسية','مستشار رئيسي للتغذية المدرسية','مستشار رئيس للتغذية المدرسية']
}

# المعطيات الخاصة بجميع الدوال (كما تم توفيرها)
category_mapping = {
    "عون تقني للمخابر": "5", "معاون تقني للمخابر": "7", "مساعد مصالح الاقتصادية": "7", "مساعد تربية": "7",
    "ملحق بالمخابر": "8", "مساعد رئيسي للتربية": "8", "مساعد رئيسي للمصالح الاقتصادية": "8",
    "معلم مدرسة إبتدائية": "10", "مشرف تربية": "10", "مربي متخصص في الدعم التربوي": "10",
    "ملحق رئيسي بالمخابر": "10", "نائب مقتصد": "10", "نائب مقتصد مسير": "11", "ملحق رئيس بالمخابر": "11",
    "مربي متخصص رئيسي في الدعم التربوي": "11", "مشرف رئيسي للتربية": "11", "أستاذ تعليم أساسي": "11",
    "مستشار التغذية المدرسية": "12", "ملحق مشرف بالمخابر": "12", "مستشار التوجيه و الإرشاد م و م": "12",
    "مربي متخصص رئيس في الدعم التربوي": "12", "مشرف رئيس للتربية": "12", "أستاذ تعليم متوسط": "12",
    "أستاذ تعليم إبتدائي": "12", "أ ت متوسط قسم أول": "13", "أستاذ تعليم ثانوي": "13", "مستشار التربية": "13",
    "مشرف عام للتربية": "13", "مربي متخصص عام في الدعم التربوي": "13", "أ ت إبتدائي قسم أول": "13",
    "مستشار محلل للتوجيه م و م": "13", "مستشار رئيسي للتغذية المدرسية": "13", "مقتصد": "13",
    "أ ت إبتدائي قسم ثان": "14", "أستاذ تعليم ثانوي قسم أول": "14", "ناظر في التعليم الابتدائي": "14",
    "مستشار رئيسي للتوجيه م و م": "14", "مستشار رئيس للتغذية المدرسية": "14", "مقتصد رئيسي": "14",
    "أستاذ مميز في التعليم الابتدائي": "15", "أ ت متوسط قسم ثان": "15", "ناظر في التعليم المتوسط": "15",
    "مدير مدرسة إبتدائية": "15", "أستاذ مميز في التعليم المتوسط": "16", "أستاذ تعليم ثانوي قسم ثان": "16",
    "ناظر في التعليم الثانوي": "16", "مدير متوسطة": "16", "مستشار رئيس للتوجيه م و م": "16",
    "مفتش المالي للتعليم المتوسط": "16", "أستاذ مميز في التعليم الثانوي": "17", "مدير ثانوية": "17",
    "مفتش مادة للتعليم الابتدائي": "17", "مفتش إدارة للتعليم الابتدائي": "17",
    "مفتش التغذية المدرسية للتعليم الابتدائي": "17", "مفتش مادة للتعليم المتوسط": "17",
    "مفتش إدارة للتعليم المتوسط": "17", "مفتش التوجيه المدرسي للتعليم م": "17",
    "مفتش المالي للتعليم الثانوي": "17", "مفتش مادة للتعليم الثانوي": "خ ص ق ف1",
    "مفتش إدارة للتعليم الثانوي": "خ ص ق ف1", "مفتش التوجيه المدرسي للتعليم ثا": "خ ص ق ف1",
    "مفتش التربية الوطنية": "خ ص ق ف2"
}

bas_mapping = {
    "5": 488, "7": 548, "8": 579, "10": 653, "11": 698, "12": 737, "13": 778, "14": 821,
    "15": 866, "16": 913, "17": 962, "خ ص ق ف1": 1130, "خ ص ق ف2": 1190
}

deg_mapping = {
    "5": {1: 24, 2: 49, 3: 73, 4: 98, 5: 122, 6: 146, 7: 171, 8: 195, 9: 220, 10: 244, 11: 268, 12: 293},
    "7": {1: 27, 2: 55, 3: 82, 4: 110, 5: 137, 6: 164, 7: 192, 8: 219, 9: 247, 10: 274, 11: 301, 12: 329},
    "8": {1: 29, 2: 58, 3: 87, 4: 116, 5: 145, 6: 174, 7: 203, 8: 232, 9: 261, 10: 290, 11: 318, 12: 347},
    "10": {1: 33, 2: 65, 3: 98, 4: 131, 5: 163, 6: 196, 7: 229, 8: 261, 9: 294, 10: 327, 11: 359, 12: 392},
    "11": {1: 35, 2: 70, 3: 105, 4: 140, 5: 175, 6: 209, 7: 244, 8: 279, 9: 314, 10: 349, 11: 384, 12: 419},
    "12": {1: 37, 2: 74, 3: 111, 4: 147, 5: 184, 6: 221, 7: 258, 8: 295, 9: 332, 10: 369, 11: 405, 12: 442},
    "13": {1: 39, 2: 78, 3: 117, 4: 156, 5: 195, 6: 233, 7: 272, 8: 311, 9: 350, 10: 389, 11: 428, 12: 467},
    "14": {1: 41, 2: 82, 3: 123, 4: 164, 5: 205, 6: 246, 7: 287, 8: 328, 9: 369, 10: 411, 11: 452, 12: 493},
    "15": {1: 43, 2: 87, 3: 130, 4: 173, 5: 217, 6: 260, 7: 303, 8: 346, 9: 390, 10: 433, 11: 476, 12: 520},
    "16": {1: 46, 2: 91, 3: 137, 4: 183, 5: 228, 6: 274, 7: 320, 8: 365, 9: 411, 10: 457, 11: 502, 12: 548},
    "17": {1: 48, 2: 96, 3: 144, 4: 192, 5: 241, 6: 289, 7: 337, 8: 385, 9: 433, 10: 481, 11: 529, 12: 577},
    "خ ص ق ف1": {1: 57, 2: 113, 3: 170, 4: 226, 5: 283, 6: 339, 7: 396, 8: 452, 9: 509, 10: 565, 11: 622, 12: 678},
    "خ ص ق ف2": {1: 60, 2: 119, 3: 179, 4: 238, 5: 298, 6: 357, 7: 417, 8: 476, 9: 536, 10: 595, 11: 655, 12: 714}
}


def get_salaries(category, rank, degree, family_status, children_count, senior_children_count, is_solidarity):
    """
    Calculates salary based on provided parameters using the detailed mappings.
    This function has been updated with the new logic provided.
    """
    results = {}
    try:
        degree = int(degree) if degree else 0
        children_count = int(children_count) if children_count else 0
        senior_children_count = int(senior_children_count) if senior_children_count else 0
    except (ValueError, TypeError):
        degree = 0
        children_count = 0
        senior_children_count = 0

    cat_id = category_mapping.get(rank, "")
    results['category_id'] = cat_id

    base_salary_points = bas_mapping.get(cat_id, 0)
    base_salary_value = base_salary_points * 45
    results['base_salary'] = base_salary_value

    mihania_points = deg_mapping.get(cat_id, {}).get(degree, 0)
    mihania_value = mihania_points * 45
    results['mihania'] = mihania_value

    principal_salary = base_salary_value + mihania_value
    results['principal_salary'] = principal_salary

    technical_allowance = 0
    if category == "موظفو المخابر":
        technical_allowance = principal_salary * 0.25
    results['technical_allowance'] = technical_allowance
    results['risk_allowance'] = technical_allowance

    taahil_allowance = 0
    if category != "موظفو المخابر":
        if cat_id in bas_mapping and cat_id.isdigit() and int(cat_id) < 13:
            taahil_allowance = principal_salary * 0.40
        elif cat_id in bas_mapping:
            taahil_allowance = principal_salary * 0.45
    results['taahil_allowance'] = taahil_allowance

    pedagogie_allowance = 0
    if category not in ["موظفو المخابر", "موظفو مصالح الاقتصادية"]:
        pedagogie_allowance = degree * base_salary_value * 0.04
    results['pedagogie_allowance'] = pedagogie_allowance

    finance_management_allowance = 0
    if category == "موظفو مصالح الاقتصادية":
        finance_management_allowance = degree * base_salary_value * 0.04
    results['finance_management_allowance'] = finance_management_allowance

    school_support_allowance = 0
    if category in ["موظفو التعليم", "موظفو إدارة مؤسسات التعليم"] or \
        rank in ['مفتش مادة للتعليم الابتدائي', 'مفتش إدارة للتعليم الابتدائي', 'مفتش مادة للتعليم المتوسط',
                 'مفتش إدارة للتعليم المتوسط', 'مفتش مادة للتعليم الثانوي', 'مفتش إدارة للتعليم الثانوي']:
        school_support_allowance = principal_salary * 0.45
    elif category in ["موظفو مصالح الاقتصادية", "موظفو المخابر"] or \
          rank in ["مفتش المالي للتعليم الثانوي", "مفتش المالي للتعليم المتوسط"]:
        school_support_allowance = principal_salary * 0.15
    else:
        school_support_allowance = principal_salary * 0.3
    results['school_support_allowance'] = school_support_allowance

    management_allowance = 0
    if category == "موظفو إدارة مؤسسات التعليم":
        comb2_mapping = {'مدير مدرسة إبتدائية': 3000, 'مدير متوسطة': 4000, 'مدير ثانوية': 5000}
        management_allowance = comb2_mapping.get(rank, 0)
    results['management_allowance'] = management_allowance

    tawthik_allowance = 0
    if category != "موظفو المخابر":
        tawthik_mapping = {
            "5": 2000, "7": 2000, "8": 2000, "10": 2000, "11": 2500, "12": 2500, "13": 3000,
            "14": 3000, "15": 3000, "16": 3000, "17": 3000, "خ ص ق ف1": 3000, "خ ص ق ف2": 3000
        }
        tawthik_allowance = tawthik_mapping.get(cat_id, 0)
    results['tawthik_allowance'] = tawthik_allowance

    forfait_allowance = 1500
    results['forfait_allowance'] = forfait_allowance
    
    gross_salary = (principal_salary + technical_allowance + technical_allowance + taahil_allowance +
                    tawthik_allowance + pedagogie_allowance + school_support_allowance +
                    management_allowance + finance_management_allowance + forfait_allowance)
    results['gross_salary'] = gross_salary

    cnas_deduction = gross_salary * 0.09
    results['cnas_deduction'] = cnas_deduction

    imposable_salary = gross_salary - cnas_deduction
    results['imposable_salary'] = imposable_salary

    irg_deduction = 0.0
    if imposable_salary > 30000:
        if imposable_salary <= 35000:
            calc1 = (imposable_salary - 20000) * 0.23
            reduction = min(max(calc1 * 0.4, 1000), 1500)
            irg_deduction = (calc1 - reduction) * 137 / 51 - 27925 / 8
        elif imposable_salary <= 80000:
            irg_deduction = ((imposable_salary - 40000) * 0.27 + 4600) - 1500
        elif imposable_salary <= 160000:
            irg_deduction = ((imposable_salary - 80000) * 0.30 + 4600 + 10800) - 1500
        elif imposable_salary <= 320000:
            irg_deduction = ((imposable_salary - 160000) * 0.33 + 4600 + 10800 + 24000) - 1500
        else:
            irg_deduction = ((imposable_salary - 320000) * 0.35 + 4600 + 10800 + 24000 + 52800) - 1500
    results['irg_deduction'] = max(0, int(irg_deduction))

    solidarity_deduction = 0.0
    if is_solidarity:
        solidarity_deduction = gross_salary * 0.01
    results['solidarity_deduction'] = solidarity_deduction

    total_deductions = cnas_deduction + irg_deduction + solidarity_deduction
    results['total_deductions'] = total_deductions

    single_salary = 0
    family_grants = 0
    family_super_grants = 0
    if family_status == "متزوج":
        if children_count > 0:
            single_salary = 800
            family_grants = children_count * 300
        else:
            single_salary = 5
            family_grants = 0
    results['single_salary'] = single_salary
    results['family_grants'] = family_grants
    family_super_grants = senior_children_count * 11.25
    results['family_super_grants'] = family_super_grants

    net_salary = gross_salary + single_salary + family_grants + family_super_grants - total_deductions
    results['net_salary'] = net_salary

    performance_allowance = principal_salary * 0.9828
    results['performance_allowance'] = performance_allowance

    final_results = {}
    for key, value in results.items():
        if isinstance(value, (int, float)):
            final_results[key] = f"{value:.2f}"
        else:
            final_results[key] = value

    return final_results

def export_to_pdf_arabic(data):
    """
    Generates a PDF file with the salary slip.
    This function has been updated with the new content and formatting.
    """
    file_path = "salary_slip.pdf"
    
    val_academe = data.get('academy', '')
    val_etablesment = data.get('establishment', '')
    val_employee = data.get('employee_name', '')
    val_comb2 = data.get('rank', '')
    val_deg = data.get('degree', '')
    val_comb_stuation = data.get('family_status', '')
    val_cheld = data.get('children_count', '')
    val_cheld_super = data.get('senior_children_count', '')

    calculations = get_salaries(
        data.get('category', ''),
        data.get('rank', ''),
        data.get('degree', ''),
        data.get('family_status', ''),
        data.get('children_count', ''),
        data.get('senior_children_count', ''),
        data.get('is_solidarity', False)
    )

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        y_pos = height - 40
        line_height = 18

        # العناوين
        c.setFont("BoldArabicFont", 12)
        month_ar, year = get_arabic_month()
        c.drawRightString(400, y_pos, reshape_text("الجمهورية الجزائرية الديمقراطية الشعبية"))
        y_pos -= line_height
        c.drawRightString(550, y_pos, reshape_text("وزارة التربية الوطنية"))
        c.drawRightString(200, y_pos, reshape_text(f"مديرية التربية لولاية : {val_academe}"))
        y_pos -= line_height * 2
        c.setFont("BoldArabicFont", 16)
        c.drawRightString(550, y_pos, reshape_text(f"_________________ كشف الراتب لشهر {month_ar} {year} _________________"))
        c.setFont("BoldArabicFont", 12)
        y_pos -= line_height * 2
        c.drawRightString(550, y_pos, reshape_text(f"المؤسسة: {val_etablesment}"))
        c.drawRightString(200, y_pos, reshape_text(f"إسم الموظف: {val_employee}"))
        y_pos -= line_height
        c.drawRightString(550, y_pos, reshape_text(f"المهنة: {val_comb2}"))
        c.drawRightString(350, y_pos, reshape_text(f"الصنف: {calculations.get('category_id', '')}"))
        c.drawRightString(200, y_pos, reshape_text(f"الدرجة: {val_deg}"))
        y_pos -= line_height
        c.drawRightString(550, y_pos, reshape_text(f"الحالة العائلية: {val_comb_stuation}"))
        c.drawRightString(350, y_pos, reshape_text(f"عدد الأولاد: {val_cheld}"))
        c.drawRightString(200, y_pos, reshape_text(f"فوق 10س: {val_cheld_super}"))
        y_pos -= line_height * 2

        # جدول الاستحقاقات
        y_rights = y_pos 
        c.setFont("BoldArabicFont", 14)
        c.drawRightString(width -45 , y_rights, reshape_text("الاستحقاقات"))
        y_rights -= line_height
        c.setFont("ArabicFont", 12)
        c.drawRightString(width - 100, y_rights, reshape_text("الأجر القاعدي"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('base_salary', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("م الخبرة المهنية"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('mihania', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("الأجر الرئيسي"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('principal_salary', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("م الخدمات التقنية"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('technical_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("م تعويض الضرر"))
        c.drawString(width - 450, y_rights, format_currency(calculations.get('risk_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("منحة التأهيل"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('taahil_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("منحة التوثيق"))
        c.drawString(width - 450, y_rights, format_currency(calculations.get('tawthik_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("المنحة البيداغوجية"))
        c.drawString(width - 450, y_rights, format_currency(calculations.get('pedagogie_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("م الدعم المدرسي"))
        c.drawString(width - 450, y_rights, format_currency(calculations.get('school_support_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("م إدارة م التعليمية"))
        c.drawString(width - 450, y_rights, format_currency(calculations.get('management_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("م التسيير المالي"))
        c.drawString(width - 450, y_rights, format_currency(calculations.get('finance_management_allowance', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("منحة جزافية"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('forfait_allowance', '0.00')))
        
        # إضافة المنح الجديدة
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("الأجر الوحيد"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('single_salary', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text("منح عائلية"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('family_grants', '0.00')))
        y_rights -= line_height
        c.drawRightString(width - 100, y_rights, reshape_text(" م عائلية إضافية"))
        c.drawString(width -450, y_rights, format_currency(calculations.get('family_super_grants', '0.00')))

        # جدول الاقتطاعات
        y_deductions = height - 500
        c.setFont("BoldArabicFont", 14)
        c.drawRightString(width - 45, y_deductions, reshape_text("الاقتطاعات"))
        y_deductions -= line_height
        c.setFont("ArabicFont", 12)
        c.drawRightString(width - 100, y_deductions, reshape_text("إقتطاع ض إ (CNAS)"))
        c.drawString(width - 450, y_deductions, format_currency(calculations.get('cnas_deduction', '0.00')))
        y_deductions -= line_height
        c.drawRightString(width - 100, y_deductions, reshape_text("الضريبة على الدخل (IRG)"))
        c.drawString(width - 450, y_deductions, format_currency(calculations.get('irg_deduction', '0.00')))
        y_deductions -= line_height
        c.drawRightString(width - 100, y_deductions, reshape_text("إقتطاع التعاضدية"))
        c.drawString(width - 450, y_deductions, format_currency(calculations.get('solidarity_deduction', '0.00')))
        y_deductions -= line_height
        c.drawRightString(width - 100, y_deductions, reshape_text("مجموع الاقتطاعات"))
        c.drawString(width - 450, y_deductions, format_currency(calculations.get('total_deductions', '0.00')))

        # الأجر الصافي والمردودية (الجزء السفلي)
        y_summary =230 
        c.setFont("BoldArabicFont", 14)
        c.drawRightString(width - 100, y_summary, reshape_text("الأجر الصافي"))
        c.drawString(width - 450, y_summary, format_currency(calculations.get('net_salary', '0.00')))
        y_summary -= line_height
        c.drawRightString(width - 100, y_summary, reshape_text("م المردودية /3 أشهر"))
        c.drawString(width - 450, y_summary, format_currency(calculations.get('performance_allowance', '0.00')))

        # إضافة التاريخ ورمز QR
        today = datetime.now().strftime("%Y-%m-%d")
        c.setFont("ArabicFont", 12)
        c.drawString(50, 30, reshape_text(f"التاريخ : {today}"))

        qr_data = reshape_text(f"كشف الراتب لشهر  {month_ar} {year} - {val_employee} - {val_etablesment} - {val_academe}")
        
        reshaped_text = arabic_reshaper.reshape(qr_data)
        bidi_text = get_display(reshaped_text)

        qr_code = qr.QrCodeWidget(bidi_text)
        d = Drawing(40, 40)
        d.add(qr_code)
        d.drawOn(c, width - 100, 20)

        c.save()
        return file_path
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None
